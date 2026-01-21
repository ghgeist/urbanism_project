import streamlit as st
from streamlit_folium import folium_static
from services.walkability import get_location, get_walkability_data, create_map, get_db_connection
from tenacity import RetryError
import os
import json
import psycopg2

# #region agent log
LOG_PATH = "/home/runner/workspace/.cursor/debug.log"
def log_debug(location, message, data, hypothesis_id):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({
                "location": location,
                "message": message,
                "data": data,
                "timestamp": __import__("time").time() * 1000,
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": hypothesis_id
            }) + "\n")
    except:
        pass
# #endregion

def _is_connection_closed(conn):
    """
    Check if a database connection is closed.
    Works with both psycopg2 connections and Streamlit SQL connections.
    """
    if conn is None:
        return True
    # Check psycopg2 connection - most reliable method
    if hasattr(conn, 'closed'):
        return conn.closed
    # For Streamlit SQL connections, we can't easily check without a query
    # Return False (assume open) and let the actual query fail gracefully
    # The exception handler will catch connection errors
    return False

@st.cache_resource
def get_cached_db_connection():
    """
    Get a cached database connection that persists across reruns.
    Uses @st.cache_resource to ensure the connection is reused efficiently.
    """
    # #region agent log
    log_debug("map_display.py:14", "get_cached_db_connection entry", {"has_pghost": bool(os.environ.get('PGHOST'))}, "A")
    # #endregion
    if os.environ.get('PGHOST'):
        conn = get_db_connection()
        # #region agent log
        log_debug("map_display.py:17", "get_cached_db_connection created direct connection", {
            "conn_id": id(conn),
            "conn_closed": conn.closed if hasattr(conn, 'closed') else None,
            "conn_type": type(conn).__name__
        }, "A")
        # #endregion
        return conn
    else:
        try:
            conn = st.connection("postgresql", type="sql")
            # #region agent log
            log_debug("map_display.py:21", "get_cached_db_connection created streamlit connection", {
                "conn_id": id(conn),
                "conn_type": type(conn).__name__
            }, "A")
            # #endregion
            return conn
        except Exception as e:
            # #region agent log
            log_debug("map_display.py:24", "get_cached_db_connection streamlit connection failed, using direct", {
                "error": str(e)
            }, "A")
            # #endregion
            # If Streamlit connection fails, try direct connection
            conn = get_db_connection()
            # #region agent log
            log_debug("map_display.py:27", "get_cached_db_connection fallback direct connection", {
                "conn_id": id(conn),
                "conn_closed": conn.closed if hasattr(conn, 'closed') else None,
                "conn_type": type(conn).__name__
            }, "A")
            # #endregion
            return conn

@st.cache_data
def cached_get_location(city_name):
    return get_location(city_name)

@st.cache_data
def cached_get_walkability_data(city_name, buffer_radius_miles):
    """
    Get walkability data using a cached database connection.
    Query results are cached separately from the connection.
    """
    # #region agent log
    log_debug("map_display.py:32", "cached_get_walkability_data entry", {
        "city_name": city_name,
        "buffer_radius_miles": buffer_radius_miles
    }, "A")
    # #endregion
    conn = get_cached_db_connection()
    # #region agent log
    log_debug("map_display.py:35", "cached_get_walkability_data got connection", {
        "conn_id": id(conn),
        "conn_closed": conn.closed if hasattr(conn, 'closed') else None,
        "conn_type": type(conn).__name__,
        "is_psycopg2": isinstance(conn, psycopg2.extensions.connection) if hasattr(psycopg2, 'extensions') else False
    }, "A")
    # #endregion
    
    # Check if connection is closed and clear cache if so
    if _is_connection_closed(conn):
        # #region agent log
        log_debug("map_display.py:38", "cached_get_walkability_data connection is CLOSED, clearing cache", {
            "conn_id": id(conn)
        }, "A")
        # #endregion
        get_cached_db_connection.clear()
        conn = get_cached_db_connection()
        # #region agent log
        log_debug("map_display.py:42", "cached_get_walkability_data got new connection after cache clear", {
            "conn_id": id(conn),
            "conn_closed": conn.closed if hasattr(conn, 'closed') else None
        }, "A")
        # #endregion
    
    try:
        result = get_walkability_data(city_name, buffer_radius_miles, conn)
        # #region agent log
        log_debug("map_display.py:48", "cached_get_walkability_data exit", {
            "result_shape": result.shape if hasattr(result, 'shape') else None,
            "conn_closed_after": conn.closed if hasattr(conn, 'closed') else None
        }, "A")
        # #endregion
        return result
    except (psycopg2.InterfaceError, psycopg2.OperationalError, psycopg2.DatabaseError) as e:
        # #region agent log
        log_debug("map_display.py:54", "cached_get_walkability_data connection error, clearing cache and retrying", {
            "error_type": type(e).__name__,
            "error_message": str(e)
        }, "A")
        # #endregion
        # Connection error - clear cache and retry once
        # This handles cases where connection was closed by server (timeout, idle cleanup, etc.)
        try:
            get_cached_db_connection.clear()
            conn = get_cached_db_connection()
            result = get_walkability_data(city_name, buffer_radius_miles, conn)
            # #region agent log
            log_debug("map_display.py:60", "cached_get_walkability_data retry successful", {
                "result_shape": result.shape if hasattr(result, 'shape') else None
            }, "A")
            # #endregion
            return result
        except Exception as retry_error:
            # #region agent log
            log_debug("map_display.py:66", "cached_get_walkability_data retry also failed", {
                "error_type": type(retry_error).__name__,
                "error_message": str(retry_error)
            }, "A")
            # #endregion
            # If retry also fails, re-raise the original error
            raise e

def render_main_content(city_name, buffer_radius_miles):
    if city_name:
        try:
            location = cached_get_location(city_name)
        except RetryError:
            st.error("Geocoding service is currently unavailable. Please try again later.")
            return

        if not location:
            st.error("Could not geocode that location. Try a more specific query (e.g., 'Cambridge, MA').")
            return

        try:
            gdf = cached_get_walkability_data(city_name, buffer_radius_miles)
        except (ValueError, psycopg2.InterfaceError, psycopg2.OperationalError) as e:
            st.error(f"Database error: {str(e)}")
            return
        
        m = create_map(location, gdf, buffer_size=buffer_radius_miles)
        if m:
            folium_static(m)
        else:
            st.error("Unable to create map. Please check your data.")
            
        df = gdf[['geoid20', 'd2a_ranked', 'd2b_ranked', 'd3b_ranked', 'd4a_ranked', 'natwalkind']].copy()
        rename_dict = {
            'geoid20': '2020 Census Block Group ID',
            'd2a_ranked': 'Employment and Housing Mix Rank',
            'd2b_ranked': 'Employment Type Rank',
            'd3b_ranked': 'Intersection Density Rank',
            'd4a_ranked': 'Commute Mode Rank',
            'natwalkind': 'National Walkability Index'
        }
        df.rename(columns=rename_dict, inplace=True)
        st.write("### National Walkability Index Components")
        st.write(
            """To score block groups, the block groups were placed into 20 quantiles by variable value (quantiles are groupings with equal numbers of records), 
            each containing 5 percent of the total block groups. Then a ranked score was assigned from 1 to 20, with 1 representing the lowest influence on walking,
            and 20 representing the highest."""
        )
        st.dataframe(df) 