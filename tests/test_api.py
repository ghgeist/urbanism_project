"""Tests for FastAPI endpoints."""
from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app

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
        "upgrade_potential": {
            "found": True,
            "candidates": [
                {"geoid20": "123", "natwalkind": 16.0, "dist_miles": 0.8, "delta_nwi": 4.0}
            ],
            "selected_mean_nwi": 12.0,
            "message": "Found 1 improvement candidate(s).",
        },
        "walkable_island": {
            "is_island": False,
            "label": None,
            "high_threshold": 15.26,
            "low_threshold": 10.51,
        },
    }


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_geocode_success():
    with patch("api.main.get_location", return_value=(-83.92, 35.96)):
        response = client.get("/geocode", params={"q": "Knoxville, TN"})

    assert response.status_code == 200
    assert response.json() == {"lat": 35.96, "lon": -83.92, "label": "Knoxville, TN"}


def test_geocode_not_found():
    with patch("api.main.get_location", return_value=None):
        response = client.get("/geocode", params={"q": "Nowhere, ZZ"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Location not found."


def test_nwi_summary_success():
    with patch("api.main.build_summary_from_coords", return_value=_sample_summary()) as mock_builder:
        response = client.get(
            "/nwi/summary",
            params={
                "lat": 35.96,
                "lon": -83.92,
                "selected_radius_miles": 1.0,
                "search_radius_miles": 3.0,
                "min_delta": 2.0,
                "top_n": 3,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "2026-02-14"
    assert payload["counts"]["selected_block_groups"] == 2
    mock_builder.assert_called_once()


def test_nwi_summary_value_error_returns_400():
    with patch("api.main.build_summary_from_coords", side_effect=ValueError("bad radius relationship")):
        response = client.get(
            "/nwi/summary",
            params={"lat": 35.96, "lon": -83.92, "selected_radius_miles": 2.0, "search_radius_miles": 1.0},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "bad radius relationship"

