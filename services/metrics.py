"""Pure metric computation helpers for walkability profile summaries."""
from __future__ import annotations

from typing import Any

import pandas as pd

DEFAULT_ISLAND_HIGH_THRESHOLD = 15.26
DEFAULT_ISLAND_LOW_THRESHOLD = 10.51


def _numeric_series(gdf, column_name: str) -> pd.Series:
    """Return a numeric, NaN-dropped series for a GeoDataFrame column."""
    if gdf is None or column_name not in gdf.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(gdf[column_name], errors="coerce").dropna()


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

    candidates["natwalkind"] = pd.to_numeric(candidates["natwalkind"], errors="coerce")
    candidates["delta_nwi"] = candidates["natwalkind"] - selected_mean_nwi
    candidates = candidates.dropna(subset=["natwalkind", "delta_nwi"])
    candidates = candidates[candidates["delta_nwi"] >= float(min_delta)]

    has_distance = "dist_miles" in candidates.columns
    if has_distance:
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
    """Compute the canonical profile dictionary used by Streamlit and API layers."""
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
