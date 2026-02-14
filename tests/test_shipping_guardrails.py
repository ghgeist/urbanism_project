"""Shipping-mode guardrails: small tests for high-value API safety checks."""
from __future__ import annotations

from unittest.mock import patch

import geopandas as gpd
from fastapi.testclient import TestClient
from shapely.geometry import Point

from api.main import app
from services.profile_summary import build_summary_from_coords

client = TestClient(app)


def _sample_summary() -> dict:
    return {
        "schema_version": "2026-02-14",
        "origin": {"lat": 35.96, "lon": -83.92, "label": None},
        "selected_radius_miles": 1.0,
        "search_radius_miles": 3.0,
        "min_delta": 2.0,
        "counts": {"selected_block_groups": 2, "context_block_groups": 3},
        "nwi": {"mean": 12.0, "min": 10.0, "max": 14.0, "spread": 4.0},
        "components": {
            "employment_housing_mix_rank_mean": 10.0,
            "employment_type_diversity_rank_mean": 9.0,
            "intersection_density_rank_mean": 8.0,
            "transit_proximity_rank_mean_proxy": 10.0,
        },
        "metrics": {"everyday_convenience": 12.0, "variation": 2.82, "transit_viability": 10.0},
        "upgrade_potential": {"found": False, "candidates": [], "selected_mean_nwi": 12.0, "message": "None"},
        "walkable_island": {
            "is_island": False,
            "label": None,
            "high_threshold": 15.26,
            "low_threshold": 10.51,
        },
    }


def test_happy_path_health_and_summary():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    with patch("api.main.build_summary_from_coords", return_value=_sample_summary()), \
         patch("api.main.get_pooled_connection"), \
         patch("api.main.return_connection"):
        summary = client.get(
            "/nwi/summary",
            params={"lat": 35.96, "lon": -83.92, "selected_radius_miles": 1.0},
        )

    assert summary.status_code == 200
    payload = summary.json()
    for key in ("schema_version", "origin", "counts", "nwi", "components", "metrics"):
        assert key in payload


def test_error_envelope_shape_guardrail():
    with patch("api.main.get_location", return_value=None):
        not_found = client.get("/geocode", params={"q": "Nowhere, ZZ"})
    assert not_found.status_code == 404
    assert set(not_found.json().keys()) == {"code", "message", "details"}

    invalid = client.get("/nwi/summary", params={"lon": -83.92, "selected_radius_miles": 1.0})
    assert invalid.status_code == 422
    assert set(invalid.json().keys()) == {"code", "message", "details"}


def test_summary_invariants_guardrail():
    full_gdf = gpd.GeoDataFrame(
        {
            "geoid20": ["A", "B", "C"],
            "natwalkind": [10.0, 12.0, 18.0],
            "d2a_ranked": [7.0, 9.0, 14.0],
            "d2b_ranked": [6.0, 10.0, 13.0],
            "d3b_ranked": [8.0, 11.0, 15.0],
            "d4a_ranked": [5.0, 12.0, 19.0],
            "dist_miles": [0.2, 0.8, 2.2],
            "geometry": [
                Point(-83.92, 35.96).buffer(0.01),
                Point(-83.93, 35.97).buffer(0.01),
                Point(-83.94, 35.98).buffer(0.01),
            ],
        },
        crs="EPSG:4326",
    )

    with patch("services.profile_summary.query_walkability_by_coords", return_value=full_gdf):
        summary = build_summary_from_coords(
            lat=35.96,
            lon=-83.92,
            selected_radius_miles=1.0,
            search_radius_miles=3.0,
            min_delta=2.0,
        )

    assert summary["search_radius_miles"] >= summary["selected_radius_miles"]
    assert summary["counts"]["selected_block_groups"] <= summary["counts"]["context_block_groups"]

    nwi = summary["nwi"]
    if nwi["mean"] is not None and nwi["min"] is not None and nwi["max"] is not None:
        assert nwi["min"] <= nwi["mean"] <= nwi["max"]
