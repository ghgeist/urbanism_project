"""Tests for FastAPI endpoints."""
from __future__ import annotations

from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

# Shared mock so pool-using endpoints don't need real DB env vars.
_mock_conn = Mock()


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
    with patch("api.main.build_summary_from_coords", return_value=_sample_summary()) as mock_builder, \
         patch("api.main.get_pooled_connection", return_value=_mock_conn), \
         patch("api.main.return_connection"):
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
    with patch("api.main.build_summary_from_coords", side_effect=ValueError("bad radius relationship")), \
         patch("api.main.get_pooled_connection", return_value=_mock_conn), \
         patch("api.main.return_connection"):
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
    with patch("api.main.build_summary_from_location_query", return_value=summary) as mock_builder, \
         patch("api.main.get_pooled_connection", return_value=_mock_conn), \
         patch("api.main.return_connection"):
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
    with patch("api.main.build_summary_from_location_query", return_value=None), \
         patch("api.main.get_pooled_connection", return_value=_mock_conn), \
         patch("api.main.return_connection"):
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


def test_geocode_query_too_long_returns_422():
    """Query param q over 200 chars is rejected at API boundary (security audit)."""
    response = client.get("/geocode", params={"q": "x" * 201})
    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "validation_error"


def test_geocode_whitespace_only_returns_400():
    """Whitespace-only q is rejected with invalid_request (security audit)."""
    response = client.get("/geocode", params={"q": "   "})
    assert response.status_code == 400
    assert response.json() == {
        "code": "invalid_request",
        "message": "Query must not be empty or whitespace only.",
        "details": None,
    }


def test_nwi_summary_by_query_whitespace_only_returns_400():
    """Whitespace-only q on by-query is rejected (security audit)."""
    response = client.get(
        "/nwi/summary/by-query",
        params={"q": " \t ", "selected_radius_miles": 1.0},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_request"
    assert "whitespace" in response.json()["message"].lower()


def test_uncaught_exception_returns_generic_500():
    """Unhandled exceptions return generic 500; no stack trace or internal details (security audit)."""
    with patch("api.main.get_location", side_effect=RuntimeError("internal failure")):
        # TestClient(raise_server_exceptions=False) so we get the 500 response instead of the exception
        no_raise_client = TestClient(app, raise_server_exceptions=False)
        response = no_raise_client.get("/geocode", params={"q": "Knoxville, TN"})
    assert response.status_code == 500
    payload = response.json()
    assert payload["code"] == "internal_error"
    assert payload["message"] == "An unexpected error occurred."
    assert payload["details"] is None
    assert "internal failure" not in str(payload)
    assert "RuntimeError" not in str(payload)


def test_security_headers_present():
    """Responses include X-Frame-Options and X-Content-Type-Options (security audit)."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-content-type-options") == "nosniff"
