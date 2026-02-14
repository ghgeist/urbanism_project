"""Tests for production static/SPA serving (API + frontend from same origin).

When frontend/dist exists, FastAPI serves the built React app so deployment
can use a single process on PORT (e.g. Replit autoscale). These tests run only
when the SPA is mounted; they assert API precedence, SPA fallback, and path safety.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _spa_is_mounted() -> bool:
    """True if the catch-all SPA route was registered (frontend/dist existed at import)."""
    return any(getattr(r, "path", "") == "/{full_path:path}" for r in app.routes)


@pytest.mark.skipif(not _spa_is_mounted(), reason="frontend/dist not present; SPA not mounted")
class TestStaticServingWhenMounted:
    """Run only when the app was started with frontend/dist (e.g. after npm run build)."""

    def test_api_routes_take_precedence_over_spa(self):
        """API routes must be matched before the SPA catch-all (e.g. /health returns JSON)."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/json")
        assert r.json() == {"status": "ok"}

    def test_root_serves_index_html(self):
        """GET / returns the SPA index.html for client-side routing."""
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        body = r.text.lower()
        assert "<!doctype html>" in body or "<html" in body

    def test_spa_route_serves_index_html(self):
        """GET /explore (or any non-API path) returns index.html for SPA routing."""
        r = client.get("/explore")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")

    def test_path_traversal_does_not_serve_files_outside_dist(self):
        """Path traversal attempts must not leak files; return index.html or safe response."""
        # URL-encoded path that would escape frontend/dist if resolved naively
        r = client.get("/..%2F..%2F..%2Fetc%2Fpasswd")
        # Should not be 200 with content-type that suggests a system file
        if r.status_code == 200:
            ct = r.headers.get("content-type", "")
            assert "text/html" in ct, "path traversal should yield HTML (index.html), not raw file"
        # Alternative: 404 is also acceptable for invalid paths
        assert r.status_code in (200, 404)
