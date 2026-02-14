import streamlit as st
from streamlit_folium import folium_static
from services.walkability import (
    get_location,
    get_walkability_data,
    query_walkability_by_coords,
    create_map,
    get_db_connection,
    _is_connection_closed,
)
from services.metrics import compute_full_profile
from tenacity import RetryError
import logging
import os
import json
import sys
import time
import psycopg2
import pandas as pd

DEBUG_LOG_ENV = "WALKABILITY_DEBUG_LOG"
_DEBUG_LOGGER = logging.getLogger("walkability.debug")

def log_debug(location, message, data=None, hypothesis_id=None):
    """Emit a structured debug log when WALKABILITY_DEBUG_LOG=1 is set."""
    if os.environ.get(DEBUG_LOG_ENV) != "1":
        return
    if not _DEBUG_LOGGER.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            stream=sys.stdout,
        )
    payload = {
        "location": location,
        "message": message,
        "data": data,
        "timestamp_ms": int(time.time() * 1000),
        "hypothesis_id": hypothesis_id,
    }
    try:
        _DEBUG_LOGGER.info(json.dumps(payload, default=str))
    except (TypeError, ValueError) as exc:
        fallback = {
            "location": location,
            "message": "debug log serialization failed",
            "error": str(exc),
        }
        _DEBUG_LOGGER.info(json.dumps(fallback, default=str))

@st.cache_resource
def get_cached_db_connection():
    """
    Get a cached database connection that persists across reruns.
    Uses @st.cache_resource to ensure the connection is reused efficiently.
    """
    log_debug("map_display.py:14", "get_cached_db_connection entry", {}, "A")
    conn = get_db_connection()
    log_debug("map_display.py:17", "get_cached_db_connection created connection", {
        "conn_id": id(conn),
        "conn_closed": conn.closed if hasattr(conn, 'closed') else None,
        "conn_type": type(conn).__name__
    }, "A")
    return conn

@st.cache_data
def cached_get_location(city_name):
    return get_location(city_name)

def _run_with_connection_retry(query_fn, log_context):
    """Run a query function with one retry after clearing a stale cached DB connection."""
    conn = get_cached_db_connection()
    if _is_connection_closed(conn):
        log_debug(f"{log_context}:connection", "cached connection closed, refreshing", {
            "conn_id": id(conn),
        }, "A")
        get_cached_db_connection.clear()
        conn = get_cached_db_connection()

    try:
        return query_fn(conn)
    except (psycopg2.InterfaceError, psycopg2.OperationalError, psycopg2.DatabaseError) as e:
        log_debug(f"{log_context}:retry", "connection error, retrying with refreshed connection", {
            "error_type": type(e).__name__,
            "error_message": str(e),
        }, "A")
        try:
            get_cached_db_connection.clear()
            conn = get_cached_db_connection()
            return query_fn(conn)
        except Exception as retry_error:
            log_debug(f"{log_context}:retry-failed", "retry failed", {
                "error_type": type(retry_error).__name__,
                "error_message": str(retry_error),
            }, "A")
            raise e

@st.cache_data
def cached_get_walkability_data(city_name, buffer_radius_miles):
    """
    Get walkability data using a cached database connection.
    Query results are cached separately from the connection.
    """
    log_debug("map_display.py:32", "cached_get_walkability_data entry", {
        "city_name": city_name,
        "buffer_radius_miles": buffer_radius_miles
    }, "A")
    result = _run_with_connection_retry(
        query_fn=lambda conn: get_walkability_data(city_name, buffer_radius_miles, conn),
        log_context="cached_get_walkability_data",
    )
    log_debug("map_display.py:walkability-exit", "cached_get_walkability_data exit", {
        "result_shape": result.shape if hasattr(result, 'shape') else None,
    }, "A")
    return result

@st.cache_data
def cached_get_profile(location_string, buffer_radius_miles, search_radius_miles, min_delta):
    """
    Build full profile data from one search-radius query and selected-radius split.
    """
    if search_radius_miles <= buffer_radius_miles:
        raise ValueError("Search radius must be greater than buffer radius.")

    location = cached_get_location(location_string)
    if not location:
        return None

    lon, lat = location

    def _query_once(active_conn):
        full_gdf = query_walkability_by_coords(lon, lat, search_radius_miles, active_conn)
        if "dist_miles" in full_gdf.columns:
            selected_gdf = full_gdf[full_gdf["dist_miles"] <= buffer_radius_miles].copy()
        else:
            selected_gdf = full_gdf.copy()

        profile = compute_full_profile(
            selected_gdf=selected_gdf,
            context_gdf=full_gdf,
            origin_lon=lon,
            origin_lat=lat,
            search_radius_miles=search_radius_miles,
            min_delta=min_delta,
        )
        profile["location"] = location
        profile["selected_gdf"] = selected_gdf
        return profile

    return _run_with_connection_retry(
        query_fn=_query_once,
        log_context="cached_get_profile",
    )


def _format_metric(value):
    if value is None:
        return "N/A"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}"


def render_summary_cards(profile):
    everyday = profile.get("everyday_convenience")
    transit = profile.get("transit_viability")
    variation = profile.get("variation")
    upgrade = profile.get("upgrade_potential", {})

    if upgrade.get("found") and upgrade.get("candidates"):
        candidates = upgrade["candidates"]
        best = candidates[0]
        delta = best.get("delta_nwi")
        dist = best.get("dist_miles")
        if delta is not None and dist is not None:
            delta_str = f"+{delta:.1f}" if delta > 0 else f"{delta:.1f}"
            dist_str = f"{dist:.1f}"
            if len(candidates) > 1:
                upgrade_val = delta_str
                upgrade_caption = f"Best nearby ({dist_str} mi)"
            else:
                upgrade_val = delta_str
                upgrade_caption = f"{dist_str} mi away"
        else:
            upgrade_val = "Found"
            upgrade_caption = None
    else:
        message = upgrade.get("message")
        upgrade_val = "None found" if message else "N/A"
        upgrade_caption = None

    # Use 5 equal columns to give the button enough space (20% vs ~11%)
    col1, col2, col3, col4, col_btn = st.columns(5)
    
    with col1:
        st.metric(
            "Everyday Convenience",
            _format_metric(everyday),
            help="Average NWI score within the selected radius (higher = more walkable).",
        )
    with col2:
        st.metric(
            "Transit Viability",
            _format_metric(transit),
            help="Average transit proximity rank (1–20 scale). Higher = closer to transit. EPA proxy d4a_ranked.",
        )
        st.caption("Transit proximity rank (avg, 1–20)")
    with col3:
        st.metric(
            "Variation",
            _format_metric(variation),
            help="Standard deviation of NWI within selected radius. Measures dispersion only.",
        )
        st.caption("Dispersion (std dev)")
    with col4:
        st.metric(
            "Upgrade Potential",
            upgrade_val,
            help="Best nearby candidate meeting min NWI improvement delta within search radius.",
        )
        if upgrade_caption:
            st.caption(upgrade_caption)
    with col_btn:
        st.write("")  # vertical align with metric row
        st.write("")
        if st.button("Compare another location →", type="secondary"):
            pass  # Placeholder: signals product direction

    st.divider()


def render_nearby_better_list(profile):
    st.write("### Nearby-better candidates")
    upgrade = profile.get("upgrade_potential", {})
    if not upgrade.get("found"):
        st.info(upgrade.get("message", "No improvement found."))
        return

    candidates = upgrade.get("candidates", [])
    if not candidates:
        st.info(upgrade.get("message", "No improvement found."))
        return

    df = pd.DataFrame(candidates)
    rename_dict = {
        "geoid20": "Block Group ID",
        "natwalkind": "NWI Score",
        "delta_nwi": "NWI Improvement",
        "dist_miles": "Distance (miles)",
    }
    df.rename(columns=rename_dict, inplace=True)
    st.dataframe(df)


def render_main_content(city_name, buffer_radius_miles, search_radius_miles, min_delta):
    if city_name:
        try:
            profile = cached_get_profile(city_name, buffer_radius_miles, search_radius_miles, min_delta)
        except RetryError:
            st.error("Geocoding service is currently unavailable. Please try again later.")
            return
        except ValueError as e:
            st.error(str(e))
            return
        except (psycopg2.InterfaceError, psycopg2.OperationalError, psycopg2.DatabaseError) as e:
            st.error(f"Database error: {str(e)}")
            return

        if not profile:
            st.error(
                "Could not find that location. Try a city or ZIP (e.g. 'Cambridge, MA'). "
                "If you used UK spelling (e.g. 'harbour'), try US spelling ('harbor')."
            )
            return

        render_summary_cards(profile)

        island = profile.get("walkable_island", {})
        if island.get("is_island"):
            st.info("Walkable Island: high local NWI with lower surrounding context.")

        location = profile.get("location")
        gdf = profile.get("selected_gdf")
        m = create_map(location, gdf, buffer_size=buffer_radius_miles)
        if m:
            folium_static(m)
        else:
            st.warning("No map data available for the selected radius.")

        render_nearby_better_list(profile)

        if gdf is None or gdf.empty:
            return

        df_cols = ['geoid20', 'd2a_ranked', 'd2b_ranked', 'd3b_ranked', 'd4a_ranked', 'natwalkind', 'dist_miles']
        available_cols = [col for col in df_cols if col in gdf.columns]
        df = gdf[available_cols].copy()
        rename_dict = {
            'geoid20': '2020 Census Block Group ID',
            'd2a_ranked': 'Employment + Housing Mix Rank (higher = more mixed)',
            'd2b_ranked': 'Employment Type Diversity Rank (higher = more diverse)',
            'd3b_ranked': 'Intersection Density Rank (higher = denser network)',
            'd4a_ranked': 'Transit Proximity Rank (proxy; higher = closer to transit)',
            'natwalkind': 'NWI Score (higher = more walkable)',
            'dist_miles': 'Distance to Origin (miles)'
        }
        df.rename(columns=rename_dict, inplace=True)
        with st.expander("Raw block group data", expanded=False):
            st.write("### National Walkability Index Components")
            st.write(
                """To score block groups, EPA places each variable into 20 quantiles and assigns ranks from 1 to 20.
                Rank fields are ordinal summaries and should be interpreted as proxies, not physical quantities."""
            )
            st.dataframe(df)
