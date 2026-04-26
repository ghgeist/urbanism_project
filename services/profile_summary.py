"""Framework-agnostic profile summary service for API-first migration."""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import shapely.geometry as sg

from services.metrics import (
    amenity_richness_label,
    check_hollow_neighborhood,
    compute_amenity_richness,
    compute_full_profile,
)
from services.walkability import get_location, query_walkability_by_coords, validate_buffer_size

_log = logging.getLogger(__name__)

# Bumped when block_groups was added to the response payload.
# Bumped again when component scores (d2a, d2b, d3b, d4a) were added to block_groups.
# Bumped again when WAS 2019 fields (was, amenity_richness, hollow_neighborhood,
# and per-block-group was_2019) were added.
# Bumped again when Upgrade Potential added WAS-aware mode and candidate deltas.
# The API is always forward-compatible (new fields have defaults), so this
# string is documentary only — the frontend does not gate on it.
SCHEMA_VERSION = "2026-04-26-was-aware-upgrade-potential"


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
    if not pd.api.types.is_numeric_dtype(series):
        series = pd.to_numeric(series, errors="coerce")
    return series.dropna()


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


def _geom_to_geojson(geom) -> dict | None:
    """Convert a Shapely geometry to a GeoJSON geometry dict, or None on failure."""
    if geom is None:
        return None
    try:
        if hasattr(geom, "is_empty") and geom.is_empty:
            return None
        return sg.mapping(geom)
    except Exception as exc:
        _log.warning("_geom_to_geojson: failed to convert geometry (%s): %s", type(geom).__name__, exc)
        return None


def _mean_column(gdf, column: str) -> float | None:
    if gdf is None or column not in gdf.columns:
        return None
    series = _safe_numeric(gdf[column])
    if series.empty:
        return None
    return _safe_float(series.mean())


_EMPTY_STATS: dict[str, float | None] = {
    "mean": None,
    "min": None,
    "max": None,
    "spread": None,
}


def _build_column_stats(selected_gdf, column: str) -> dict[str, float | None]:
    """Return ``{mean, min, max, spread}`` for a numeric column, or all-None.

    Shared helper for per-column aggregate blocks (NWI ``natwalkind``, WAS
    ``was_2019``, etc.). Returns a dict with every value set to ``None`` when
    the column is missing or contains no numeric values so callers never need
    to branch on "column exists".
    """
    if selected_gdf is None or column not in selected_gdf.columns:
        return dict(_EMPTY_STATS)

    series = _safe_numeric(selected_gdf[column])
    if series.empty:
        return dict(_EMPTY_STATS)

    col_min = _safe_float(series.min())
    col_max = _safe_float(series.max())
    spread = col_max - col_min if col_min is not None and col_max is not None else None

    return {
        "mean": _safe_float(series.mean()),
        "min": col_min,
        "max": col_max,
        "spread": _safe_float(spread),
    }


def _build_nwi_stats(selected_gdf) -> dict[str, float | None]:
    """Return selected-radius NWI aggregate stats."""
    return _build_column_stats(selected_gdf, "natwalkind")


def _build_was_stats(selected_gdf) -> dict[str, float | None]:
    """Return selected-radius WAS 2019 aggregate stats. All None if column absent."""
    return _build_column_stats(selected_gdf, "was_2019")


def _split_selected_context(full_gdf, selected_radius_miles: float):
    """Split full search results into selected-radius and full-context frames."""
    if full_gdf is None:
        return full_gdf, full_gdf
    if "dist_miles" not in full_gdf.columns:
        return full_gdf.copy(), full_gdf.copy()

    dist = full_gdf["dist_miles"]
    if not pd.api.types.is_numeric_dtype(dist):
        dist = pd.to_numeric(dist, errors="coerce")
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
    # Serialize selected block group geometries for choropleth map rendering.
    # Iterate via zip over pre-extracted column lists to avoid per-row Series
    # allocation from iterrows().
    block_groups = []
    if selected_gdf is not None and "geometry" in selected_gdf.columns:
        geoid_vals = selected_gdf["geoid20"].tolist() if "geoid20" in selected_gdf.columns else [None] * len(selected_gdf)
        nwi_vals = selected_gdf["natwalkind"].tolist() if "natwalkind" in selected_gdf.columns else [None] * len(selected_gdf)
        d2a_vals = selected_gdf["d2a_ranked"].tolist() if "d2a_ranked" in selected_gdf.columns else [None] * len(selected_gdf)
        d2b_vals = selected_gdf["d2b_ranked"].tolist() if "d2b_ranked" in selected_gdf.columns else [None] * len(selected_gdf)
        d3b_vals = selected_gdf["d3b_ranked"].tolist() if "d3b_ranked" in selected_gdf.columns else [None] * len(selected_gdf)
        d4a_vals = selected_gdf["d4a_ranked"].tolist() if "d4a_ranked" in selected_gdf.columns else [None] * len(selected_gdf)
        was_vals = selected_gdf["was_2019"].tolist() if "was_2019" in selected_gdf.columns else [None] * len(selected_gdf)
        for geoid20, natwalkind, d2a, d2b, d3b, d4a, was_2019, geom in zip(
            geoid_vals, nwi_vals, d2a_vals, d2b_vals, d3b_vals, d4a_vals, was_vals, selected_gdf["geometry"], strict=True
        ):
            geom_json = _geom_to_geojson(geom)
            if geom_json is None:
                continue
            block_groups.append({
                "geoid20": str(geoid20) if pd.notna(geoid20) else None,
                "natwalkind": _safe_float(natwalkind),
                "d2a_ranked": _safe_float(d2a),
                "d2b_ranked": _safe_float(d2b),
                "d3b_ranked": _safe_float(d3b),
                "d4a_ranked": _safe_float(d4a),
                "was_2019": _safe_float(was_2019),
                "geometry": geom_json,
            })

    was_stats = _build_was_stats(selected_gdf)
    amenity_value = compute_amenity_richness(selected_gdf)
    amenity_block = {
        "value": amenity_value,
        "label": amenity_richness_label(amenity_value),
    }
    nwi_stats = _build_nwi_stats(selected_gdf)
    hollow_block = check_hollow_neighborhood(
        nwi_mean=nwi_stats["mean"],
        was_mean=was_stats["mean"],
    )

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
            # Use len(block_groups) so the count matches the array length exactly,
            # even if a row was dropped because its geometry failed to serialize.
            "selected_block_groups": len(block_groups),
            "context_block_groups": int(len(context_gdf)) if context_gdf is not None else 0,
        },
        "nwi": nwi_stats,
        "was": was_stats,
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
        "amenity_richness": amenity_block,
        "upgrade_potential": profile.get("upgrade_potential"),
        "walkable_island": profile.get("walkable_island"),
        "hollow_neighborhood": hollow_block,
        "block_groups": block_groups,
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
