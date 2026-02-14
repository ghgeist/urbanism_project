"""Framework-agnostic profile summary service for API-first migration."""
from __future__ import annotations

from typing import Any

import pandas as pd

from services.metrics import compute_full_profile
from services.walkability import get_location, query_walkability_by_coords, validate_buffer_size

SCHEMA_VERSION = "2026-02-14"


def _validate_coordinates(lat: float, lon: float) -> tuple[float, float]:
    """Validate and normalize coordinate inputs."""
    try:
        lat_value = float(lat)
        lon_value = float(lon)
    except (TypeError, ValueError) as exc:
        raise ValueError("Latitude and longitude must be numeric.") from exc

    if not -90.0 <= lat_value <= 90.0:
        raise ValueError("Latitude must be between -90 and 90.")
    if not -180.0 <= lon_value <= 180.0:
        raise ValueError("Longitude must be between -180 and 180.")

    return lat_value, lon_value


def _validate_radii(selected_radius_miles: float, search_radius_miles: float) -> tuple[float, float]:
    """Validate radius inputs and enforce selected <= search."""
    selected_ok, selected_error = validate_buffer_size(selected_radius_miles)
    if not selected_ok:
        raise ValueError(f"Invalid selected_radius_miles: {selected_error}")

    search_ok, search_error = validate_buffer_size(search_radius_miles)
    if not search_ok:
        raise ValueError(f"Invalid search_radius_miles: {search_error}")

    selected = float(selected_radius_miles)
    search = float(search_radius_miles)
    if search < selected:
        raise ValueError("search_radius_miles must be greater than or equal to selected_radius_miles.")

    return selected, search


def _safe_numeric(series: pd.Series | None) -> pd.Series:
    if series is None:
        return pd.Series(dtype=float)
    return pd.to_numeric(series, errors="coerce").dropna()


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(value):
        return None
    return value


def _mean_column(gdf, column: str) -> float | None:
    if gdf is None or column not in gdf.columns:
        return None
    series = _safe_numeric(gdf[column])
    if series.empty:
        return None
    return _safe_float(series.mean())


def _build_nwi_stats(selected_gdf) -> dict[str, float | None]:
    """Return selected-radius NWI aggregate stats."""
    if selected_gdf is None or "natwalkind" not in selected_gdf.columns:
        return {"mean": None, "min": None, "max": None, "spread": None}

    nwi = _safe_numeric(selected_gdf["natwalkind"])
    if nwi.empty:
        return {"mean": None, "min": None, "max": None, "spread": None}

    nwi_min = _safe_float(nwi.min())
    nwi_max = _safe_float(nwi.max())
    spread = None
    if nwi_min is not None and nwi_max is not None:
        spread = nwi_max - nwi_min

    return {
        "mean": _safe_float(nwi.mean()),
        "min": nwi_min,
        "max": nwi_max,
        "spread": _safe_float(spread),
    }


def _split_selected_context(full_gdf, selected_radius_miles: float):
    """Split full search results into selected-radius and full-context frames."""
    if full_gdf is None:
        return full_gdf, full_gdf
    if "dist_miles" not in full_gdf.columns:
        return full_gdf.copy(), full_gdf.copy()

    dist = pd.to_numeric(full_gdf["dist_miles"], errors="coerce")
    selected_gdf = full_gdf[dist <= float(selected_radius_miles)].copy()
    return selected_gdf, full_gdf.copy()


def _build_response(
    profile: dict[str, Any],
    selected_gdf,
    context_gdf,
    selected_radius_miles: float,
    search_radius_miles: float,
    min_delta: float,
    origin_label: str | None,
) -> dict[str, Any]:
    """Build canonical summary response payload."""
    return {
        "schema_version": SCHEMA_VERSION,
        "origin": {
            "lat": profile["origin"]["lat"],
            "lon": profile["origin"]["lon"],
            "label": origin_label,
        },
        "selected_radius_miles": float(selected_radius_miles),
        "search_radius_miles": float(search_radius_miles),
        "min_delta": float(min_delta),
        "counts": {
            "selected_block_groups": int(len(selected_gdf)) if selected_gdf is not None else 0,
            "context_block_groups": int(len(context_gdf)) if context_gdf is not None else 0,
        },
        "nwi": _build_nwi_stats(selected_gdf),
        "components": {
            "employment_housing_mix_rank_mean": _mean_column(selected_gdf, "d2a_ranked"),
            "employment_type_diversity_rank_mean": _mean_column(selected_gdf, "d2b_ranked"),
            "intersection_density_rank_mean": _mean_column(selected_gdf, "d3b_ranked"),
            "transit_proximity_rank_mean_proxy": _mean_column(selected_gdf, "d4a_ranked"),
        },
        "metrics": {
            "everyday_convenience": profile.get("everyday_convenience"),
            "variation": profile.get("variation"),
            "transit_viability": profile.get("transit_viability"),
        },
        "upgrade_potential": profile.get("upgrade_potential"),
        "walkable_island": profile.get("walkable_island"),
    }


def build_summary_from_coords(
    *,
    lat: float,
    lon: float,
    selected_radius_miles: float,
    search_radius_miles: float | None = None,
    min_delta: float = 2.0,
    top_n: int = 3,
    conn=None,
) -> dict[str, Any]:
    """
    Build canonical summary response from coordinates.

    Runs one search-radius query and splits selected/context in Python.
    """
    lat_value, lon_value = _validate_coordinates(lat, lon)
    search_radius = selected_radius_miles if search_radius_miles is None else search_radius_miles
    selected_radius, search_radius = _validate_radii(selected_radius_miles, search_radius)

    full_gdf = query_walkability_by_coords(lon_value, lat_value, search_radius, conn=conn)
    selected_gdf, context_gdf = _split_selected_context(full_gdf, selected_radius)

    profile = compute_full_profile(
        selected_gdf=selected_gdf,
        context_gdf=context_gdf,
        origin_lon=lon_value,
        origin_lat=lat_value,
        search_radius_miles=search_radius,
        min_delta=min_delta,
        top_n=top_n,
    )

    return _build_response(
        profile=profile,
        selected_gdf=selected_gdf,
        context_gdf=context_gdf,
        selected_radius_miles=selected_radius,
        search_radius_miles=search_radius,
        min_delta=min_delta,
        origin_label=None,
    )


def build_summary_from_location_query(
    *,
    query: str,
    selected_radius_miles: float,
    search_radius_miles: float | None = None,
    min_delta: float = 2.0,
    top_n: int = 3,
    conn=None,
) -> dict[str, Any] | None:
    """Build canonical summary response from a location query string."""
    location = get_location(query)
    if not location:
        return None

    lon, lat = location
    summary = build_summary_from_coords(
        lat=lat,
        lon=lon,
        selected_radius_miles=selected_radius_miles,
        search_radius_miles=search_radius_miles,
        min_delta=min_delta,
        top_n=top_n,
        conn=conn,
    )
    summary["origin"]["label"] = query
    return summary
