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


def test_cors_preflight_allows_localhost_3000():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_geocode_success():
    with patch("api.main.get_location", return_value=(-83.92, 35.96)):
        response = client.get("/geocode", params={"q": "Knoxville, TN"})

    assert response.status_code == 200
    assert response.json() == {"lat": 35.96, "lon": -83.92, "label": "Knoxville, TN"}


def test_geocode_not_found_uses_error_envelope():
    with patch("api.main.get_location", return_value=None):
        response = client.get("/geocode", params={"q": "Nowhere, ZZ"})

    assert response.status_code == 404
    assert response.json() == {
        "code": "location_not_found",
        "message": "Location not found.",
        "details": {"query": "Nowhere, ZZ"},
    }


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


def test_nwi_summary_value_error_returns_error_envelope():
    with patch("api.main.build_summary_from_coords", side_effect=ValueError("bad radius relationship")):
        response = client.get(
            "/nwi/summary",
            params={"lat": 35.96, "lon": -83.92, "selected_radius_miles": 2.0, "search_radius_miles": 1.0},
        )

    assert response.status_code == 400
    assert response.json() == {
        "code": "invalid_request",
        "message": "bad radius relationship",
        "details": None,
    }


def test_nwi_summary_validation_error_uses_error_envelope():
    response = client.get("/nwi/summary", params={"lon": -83.92, "selected_radius_miles": 1.0})
    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["message"] == "Request validation failed."
    assert isinstance(payload["details"], list)


def test_nwi_summary_by_query_success():
    summary = _sample_summary()
    summary["origin"]["label"] = "Knoxville, TN"
    with patch("api.main.build_summary_from_location_query", return_value=summary) as mock_builder:
        response = client.get(
            "/nwi/summary/by-query",
            params={
                "q": "Knoxville, TN",
                "selected_radius_miles": 1.0,
                "search_radius_miles": 3.0,
                "min_delta": 2.0,
                "top_n": 3,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["origin"]["label"] == "Knoxville, TN"
    mock_builder.assert_called_once()


def test_nwi_summary_by_query_not_found_returns_error_envelope():
    with patch("api.main.build_summary_from_location_query", return_value=None):
        response = client.get(
            "/nwi/summary/by-query",
            params={"q": "Nowhere, ZZ", "selected_radius_miles": 1.0},
        )

    assert response.status_code == 404
    assert response.json() == {
        "code": "location_not_found",
        "message": "Location not found.",
        "details": {"query": "Nowhere, ZZ"},
    }
