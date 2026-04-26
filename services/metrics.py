"""Pure metric computation helpers for walkability profile summaries.

WAS-derived metrics (``compute_amenity_richness``, ``check_hollow_neighborhood``)
are built on top of the Walkable Accessibility Score dataset published by:

    Credit, K., Farah, I., Talen, E., Anselin, L., & Ghomrawi, H. (2025).
    The Walkable Accessibility Score (WAS): A spatially-granular open-source
    measure of walkability for the continental US from 1997-2019.
    Environment and Planning B. https://doi.org/10.1177/23998083251377116

Source code and data: https://github.com/kcredit/Walkable-Accessibility-Score
"""
from __future__ import annotations

from typing import Any

import pandas as pd

DEFAULT_ISLAND_HIGH_THRESHOLD = 15.26
DEFAULT_ISLAND_LOW_THRESHOLD = 10.51

# Amenity Richness labels derived from the WAS 0-30 scale. After the 2019
# production load, 10 sits just above the median (8.45) and 20 sits near the
# upper quartile (21.19), giving rounded, interpretable breakpoints.
AMENITY_FULL_THRESHOLD = 20.0
AMENITY_MODERATE_THRESHOLD = 10.0

# Single source of truth for Amenity Richness label strings. Pydantic
# schemas narrow to these exact values via Literal[...]; the frontend
# type union mirrors the same set. Any change here must also be reflected
# in ``api/schemas.py`` and ``frontend/src/types/api.ts``.
AMENITY_RICHNESS_LABELS: dict[str, str] = {
    "full": "Full Amenity Access",
    "moderate": "Moderate Amenity Access",
    "sparse": "Destination Sparse",
    "unavailable": "Unavailable",
}

HOLLOW_NEIGHBORHOOD_LABEL = "Hollow Neighborhood"

# "Hollow Neighborhood" = high NWI connectivity + low WAS destination density.
# Thresholds loosely align with the Walkable Island high cutoff on the NWI side
# and the Amenity Richness "Destination Sparse" boundary on the WAS side.
DEFAULT_HOLLOW_NWI_THRESHOLD = 13.0
DEFAULT_HOLLOW_WAS_THRESHOLD = 10.0


def _numeric_series(gdf, column_name: str) -> pd.Series:
    """Return a numeric, NaN-dropped series for a GeoDataFrame column.

    Skips pd.to_numeric when the column is already a numeric dtype (the
    common case after _rows_to_gdf coerces once at the boundary).
    """
    if gdf is None or column_name not in gdf.columns:
        return pd.Series(dtype=float)
    col = gdf[column_name]
    if not pd.api.types.is_numeric_dtype(col):
        col = pd.to_numeric(col, errors="coerce")
    return col.dropna()


def _safe_float(value: Any) -> float | None:
    """Convert numeric output to plain float, preserving None for NaN/invalid."""
    if value is None:
        return None
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(value_float):
        return None
    return value_float


def compute_everyday_convenience(gdf) -> float | None:
    """Mean NWI (`natwalkind`) for selected block groups."""
    nwi = _numeric_series(gdf, "natwalkind")
    if nwi.empty:
        return None
    return _safe_float(nwi.mean())


def compute_variation(gdf) -> float | None:
    """Standard deviation of NWI (`natwalkind`), requires at least two rows."""
    nwi = _numeric_series(gdf, "natwalkind")
    if len(nwi) < 2:
        return None
    return _safe_float(nwi.std(ddof=1))


def compute_transit_viability(gdf) -> float | None:
    """Mean `d4a_ranked` as an average ordinal transit proximity rank (1-20)."""
    transit_rank = _numeric_series(gdf, "d4a_ranked")
    if transit_rank.empty:
        return None
    return _safe_float(transit_rank.mean())


def compute_amenity_richness(gdf) -> float | None:
    """Mean WAS 2019 score (0-30) for selected block groups.

    The Walkable Accessibility Score is defined on a 0-30 scale by Credit et al.
    (2025); see the module docstring for the full citation. Higher values mean
    more reachable destinations (groceries, shops, schools, parks, food
    services) within ~1,600 m, weighted by logistic distance decay.

    Returns None if the column is absent or has no non-null values (e.g. the
    WAS table hasn't been loaded yet, or the selected area is outside US WAS
    coverage). Callers should treat None as "data unavailable" rather than
    "score is zero".
    """
    was = _numeric_series(gdf, "was_2019")
    if was.empty:
        return None
    return _safe_float(was.mean())


def amenity_richness_label(value: float | None) -> str:
    """Map a WAS score (0-30) to a human-readable richness bucket.

    Thresholds:
    - value >= 20      -> "Full Amenity Access"
    - 10 <= value < 20 -> "Moderate Amenity Access"
    - value < 10       -> "Destination Sparse"
    - value is None    -> "Unavailable"
    """
    if value is None:
        return AMENITY_RICHNESS_LABELS["unavailable"]
    if value >= AMENITY_FULL_THRESHOLD:
        return AMENITY_RICHNESS_LABELS["full"]
    if value >= AMENITY_MODERATE_THRESHOLD:
        return AMENITY_RICHNESS_LABELS["moderate"]
    return AMENITY_RICHNESS_LABELS["sparse"]


def check_hollow_neighborhood(
    nwi_mean: float | None,
    was_mean: float | None,
    nwi_threshold: float = DEFAULT_HOLLOW_NWI_THRESHOLD,
    was_threshold: float = DEFAULT_HOLLOW_WAS_THRESHOLD,
) -> dict[str, Any]:
    """Detect "Hollow Neighborhood" signal: high NWI (good bones) + low WAS (few destinations).

    NWI measures the form of the built environment (street design, density,
    mix); WAS measures destination density. The Credit et al. (2025) paper
    (see module docstring) found the two signals are intentionally
    complementary — combining them did not improve fit with commercial Walk
    Score®, so we surface them as a combined flag rather than a composite.

    Returns a structured dict mirroring check_walkable_island's shape for UI consistency.
    If either input is None (e.g. WAS table not loaded), returns is_hollow=False with
    label=None so the UI can hide the badge gracefully.
    """
    nwi = _safe_float(nwi_mean)
    was = _safe_float(was_mean)
    if nwi is None or was is None:
        return {
            "is_hollow": False,
            "label": None,
            "nwi_threshold": nwi_threshold,
            "was_threshold": was_threshold,
        }

    is_hollow = nwi >= nwi_threshold and was <= was_threshold
    return {
        "is_hollow": is_hollow,
        "label": HOLLOW_NEIGHBORHOOD_LABEL if is_hollow else None,
        "nwi_threshold": nwi_threshold,
        "was_threshold": was_threshold,
    }


def compute_upgrade_potential(
    selected_gdf,
    search_gdf,
    min_delta: float,
    top_n: int = 3,
    search_radius_miles: float | None = None,
) -> dict[str, Any]:
    """Find nearby block groups with material NWI improvement over selected mean."""
    if top_n <= 0:
        raise ValueError("top_n must be positive")
    if min_delta < 0:
        raise ValueError("min_delta must be non-negative")

    selected_mean_nwi = compute_everyday_convenience(selected_gdf)
    if selected_mean_nwi is None:
        return {
            "found": False,
            "candidates": [],
            "selected_mean_nwi": None,
            "message": "No improvement found: selected area has no valid NWI values.",
        }

    if search_gdf is None or search_gdf.empty:
        return {
            "found": False,
            "candidates": [],
            "selected_mean_nwi": selected_mean_nwi,
            "message": _no_improvement_message(search_radius_miles),
        }

    candidates = search_gdf.copy()

    if "geoid20" in candidates.columns and selected_gdf is not None and "geoid20" in selected_gdf.columns:
        selected_geoids = set(selected_gdf["geoid20"].dropna().astype(str))
        candidates = candidates[~candidates["geoid20"].astype(str).isin(selected_geoids)]

    if "natwalkind" not in candidates.columns:
        return {
            "found": False,
            "candidates": [],
            "selected_mean_nwi": selected_mean_nwi,
            "message": _no_improvement_message(search_radius_miles),
        }

    if not pd.api.types.is_numeric_dtype(candidates["natwalkind"]):
        candidates["natwalkind"] = pd.to_numeric(candidates["natwalkind"], errors="coerce")
    candidates["delta_nwi"] = candidates["natwalkind"] - selected_mean_nwi
    candidates = candidates.dropna(subset=["natwalkind", "delta_nwi"])
    candidates = candidates[candidates["delta_nwi"] >= float(min_delta)]

    has_distance = "dist_miles" in candidates.columns
    if has_distance:
        if not pd.api.types.is_numeric_dtype(candidates["dist_miles"]):
            candidates["dist_miles"] = pd.to_numeric(candidates["dist_miles"], errors="coerce")
        candidates = candidates.dropna(subset=["dist_miles"])
        if search_radius_miles is not None:
            candidates = candidates[candidates["dist_miles"] <= float(search_radius_miles)]

    if candidates.empty:
        return {
            "found": False,
            "candidates": [],
            "selected_mean_nwi": selected_mean_nwi,
            "message": _no_improvement_message(search_radius_miles),
        }

    sort_columns = ["delta_nwi"]
    ascending = [False]
    if has_distance:
        sort_columns.append("dist_miles")
        ascending.append(True)
    if "geoid20" in candidates.columns:
        sort_columns.append("geoid20")
        ascending.append(True)

    candidates = candidates.sort_values(by=sort_columns, ascending=ascending).head(top_n)

    candidate_rows: list[dict[str, Any]] = []
    for _, row in candidates.iterrows():
        candidate_rows.append(
            {
                "geoid20": str(row["geoid20"]) if "geoid20" in row and pd.notna(row["geoid20"]) else None,
                "natwalkind": _safe_float(row.get("natwalkind")),
                "dist_miles": _safe_float(row.get("dist_miles")),
                "delta_nwi": _safe_float(row.get("delta_nwi")),
            }
        )

    return {
        "found": True,
        "candidates": candidate_rows,
        "selected_mean_nwi": selected_mean_nwi,
        "message": f"Found {len(candidate_rows)} improvement candidate(s).",
    }


def _no_improvement_message(search_radius_miles: float | None) -> str:
    if search_radius_miles is None:
        return "No improvement found within the search radius."
    return f"No improvement found within {search_radius_miles:.1f} miles."


def check_walkable_island(
    selected_mean: float | None,
    context_mean: float | None,
    high_threshold: float = DEFAULT_ISLAND_HIGH_THRESHOLD,
    low_threshold: float = DEFAULT_ISLAND_LOW_THRESHOLD,
) -> dict[str, Any]:
    """Check whether the selected area looks like a high-score island in lower context."""
    selected = _safe_float(selected_mean)
    context = _safe_float(context_mean)
    if selected is None or context is None:
        return {
            "is_island": False,
            "label": None,
            "high_threshold": high_threshold,
            "low_threshold": low_threshold,
        }

    is_island = selected >= high_threshold and context <= low_threshold
    return {
        "is_island": is_island,
        "label": "Walkable Island" if is_island else None,
        "high_threshold": high_threshold,
        "low_threshold": low_threshold,
    }


def compute_full_profile(
    selected_gdf,
    context_gdf,
    origin_lon: float,
    origin_lat: float,
    search_radius_miles: float,
    min_delta: float,
    top_n: int = 3,
    high_threshold: float = DEFAULT_ISLAND_HIGH_THRESHOLD,
    low_threshold: float = DEFAULT_ISLAND_LOW_THRESHOLD,
) -> dict[str, Any]:
    """Compute the canonical profile dictionary used by the API layer."""
    if search_radius_miles <= 0:
        raise ValueError("search_radius_miles must be positive")

    selected_mean = compute_everyday_convenience(selected_gdf)
    context_mean = compute_everyday_convenience(context_gdf)

    upgrade_potential = compute_upgrade_potential(
        selected_gdf=selected_gdf,
        search_gdf=context_gdf,
        min_delta=min_delta,
        top_n=top_n,
        search_radius_miles=search_radius_miles,
    )

    return {
        "origin": {"lon": float(origin_lon), "lat": float(origin_lat)},
        "search_radius_miles": float(search_radius_miles),
        "selected_count": int(len(selected_gdf)) if selected_gdf is not None else 0,
        "context_count": int(len(context_gdf)) if context_gdf is not None else 0,
        "everyday_convenience": selected_mean,
        "selected_mean_nwi": selected_mean,
        "context_mean_nwi": context_mean,
        "variation": compute_variation(selected_gdf),
        "transit_viability": compute_transit_viability(selected_gdf),
        "upgrade_potential": upgrade_potential,
        "walkable_island": check_walkable_island(
            selected_mean=selected_mean,
            context_mean=context_mean,
            high_threshold=high_threshold,
            low_threshold=low_threshold,
        ),
    }
