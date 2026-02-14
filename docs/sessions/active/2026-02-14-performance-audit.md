---
title: "Execute: Performance Audit"
date: "2026-02-14"
status: "active"
session_type: "execute"
priority: "high"
tags: ["performance", "connection-pooling", "caching", "fastapi"]
---

# Performance Audit

**Session Type**: EXECUTE
**Priority**: High
**Branch**: `performance-audit`

## Objective

Identify and fix the highest-impact performance bottlenecks in the API request path.

## Findings (Discovery + Measurement)

### Critical (every request pays this cost)

1. **No DB connection pooling** — `get_db_connection()` opens a new TCP connection per request and closes it after. On cloud Postgres (Neon/Replit) this adds 50-200ms per request.
2. **No geocoding cache** — every `/nwi/summary/by-query` call hits Nominatim over the network. Repeated queries for the same location pay full round-trip cost.
3. **New `Nominatim` instance per call** — no HTTP session reuse; each call creates a new `urllib3` session.

### Moderate

4. **Redundant `pd.to_numeric` coercions** — same columns coerced 3-4 times per request across `_rows_to_gdf`, `_numeric_series`, `_safe_numeric`, and `compute_upgrade_potential`.
5. **`on_event("shutdown")` deprecation** — FastAPI warns about deprecated shutdown hook pattern.

### Noted but not addressed

- No query `LIMIT` on large-radius searches (acceptable for current use; max buffer is 50mi).
- No `AbortController` in frontend fetch (cosmetic; stale results are discarded).
- `create_map()` / `folium` are dead code (not called by API or frontend).

## Changes Made

### 1. Connection pooling (`services/db.py`)

**Preserved**: `get_db_connection()` for scripts and one-off use.
**Added**: `get_pool()`, `get_pooled_connection()`, `return_connection()`, `close_pool()`.
- `ThreadedConnectionPool` (psycopg2.pool), min=1, max=5, lazy-initialized on first call.
- Thread-safe via double-checked locking.
- API endpoints now call `get_pooled_connection()` and `return_connection()` in try/finally.
- Pool is closed on app shutdown via FastAPI `lifespan`.

### 2. Geocoding cache (`services/walkability.py`)

**Preserved**: `get_location()` signature and behavior.
**Added**: `@lru_cache(maxsize=256)` on `get_location()`.
**Changed**: Module-level `_geolocator = Nominatim(...)` reuses HTTP session. Internal `_geocode_nominatim()` wrapper carries the tenacity retry decorator.

### 3. Redundant type coercion elimination (`services/metrics.py`, `services/profile_summary.py`)

**Preserved**: All function signatures and return values.
**Changed**: `_numeric_series()`, `_safe_numeric()`, `compute_upgrade_potential()`, and `_split_selected_context()` now check `pd.api.types.is_numeric_dtype()` before calling `pd.to_numeric()`. Columns coerced once at boundary (`_rows_to_gdf`) skip redundant coercion downstream.

### 4. Lifespan pattern (`api/main.py`)

**Changed**: Replaced deprecated `@app.on_event("shutdown")` with `@asynccontextmanager` lifespan handler.

## Test Updates

- `test_api.py`: API tests that hit pool-using endpoints now mock `get_pooled_connection` and `return_connection`.
- `test_walkability.py`: Geocoding tests patch `_geocode_nominatim` instead of `Nominatim` class; `setup_method` clears `get_location.cache_clear()`.
- `test_shipping_guardrails.py`: Pool mocks added to summary endpoint test.

## Verification

- `pytest -v`: 81 passed, 0 failed, 1 warning (third-party folium deprecation).

## Expected Impact

| Optimization | Estimated per-request savings |
|---|---|
| Connection pooling | 50-200ms (eliminates TCP handshake + TLS + auth) |
| Geocoding cache (cache hit) | 100-500ms (eliminates Nominatim round-trip) |
| Type coercion skip | <1ms (micro-optimization, correctness benefit) |
