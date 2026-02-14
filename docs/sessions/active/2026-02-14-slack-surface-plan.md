# Slack Surface Explorer — Bridge Phase Implementation Plan

## Context

The current Streamlit app is a visualization tool: enter an address, see a choropleth map of NWI scores. The product plan (`docs/sessions/active/2026-02-14-slack-surface-explorer.md`) repositions it as a **decision-support tool** that surfaces neighborhood tradeoffs through computed metrics, not just a colored map.

This plan covers the **Bridge Phase** only — building the new capabilities inside the existing Streamlit app to validate the data model before any FastAPI/React migration. The app must keep working throughout; no breaking changes.

---

## Phase 1: New metrics service (`services/metrics.py`)

**Why first:** All UI work depends on having pure-data metric functions. Building these with zero UI imports means they'll work unchanged when FastAPI wraps them later.

**Create `services/metrics.py`** with these functions:

- `compute_everyday_convenience(gdf)` → `float | None` — `mean(natwalkind)`
- `compute_variation(gdf)` → `float | None` — `stddev(natwalkind)`, returns `None` for <2 rows
- `compute_transit_viability(gdf)` → `float | None` — `mean(d4a_ranked)`. Note: `d4a_ranked` is ordinal (ranks 1–20, quantile-based). Mean of ranks is used as a practical summary statistic. UI must label as "average rank (1–20)" and must not imply it is a physical quantity.
- `compute_upgrade_potential(selected_gdf, search_gdf, min_delta, top_n=3)` → `dict` with `found`, `candidates`, `selected_mean_nwi`, `message`
  - Candidates: block groups in `search_gdf` but NOT in `selected_gdf` (exclude by `geoid20`) where `natwalkind - selected_mean >= min_delta`
  - Distance is pre-computed in SQL (see Phase 2) and arrives as a `dist_miles` column on the GDF — no Python-side Haversine needed
  - Returns explicit `"No improvement found within X miles"` when none qualify
- `check_walkable_island(selected_mean, context_mean, high_threshold=15.0, low_threshold=10.0)` → `dict` with `is_island`, `label`
  - Default thresholds anchored to published EPA NWI category breaks: `high_threshold=15.26` ("Most Walkable" cutoff), `low_threshold=10.51` ("Below Average / Above Average" boundary). These come from the EPA methodology doc and read less arbitrary than round numbers. Still parameterized — overridable via advanced settings or percentile-based computation later.
- `compute_full_profile(selected_gdf, context_gdf, origin_lon, origin_lat, search_radius_miles, min_delta, ...)` → canonical `dict` combining all metrics above — single entry point for both Streamlit and future FastAPI

**Create `tests/test_metrics.py`** — all mocked GeoDataFrames, no live DB:
- Mean/stddev correctness, empty GDF handling, NaN handling, single-row edge case
- Upgrade potential: delta filtering, distance filtering, sorting, explicit "none found" message, geoid exclusion
- Island check: threshold logic, custom thresholds
- Full profile: returns all expected keys

**Files:** Create `services/metrics.py`, create `tests/test_metrics.py`

---

## Phase 2: Query layer — single query with geography-based distance

**Why:** Currently `get_walkability_data()` takes a location string and geocodes internally. The new profile needs data at two radii for the same address. Instead of two queries, we issue **one query at the max radius** (search radius) and split the result in Python. This halves DB load and eliminates double-geocoding.

**Key correction — use PostGIS geography for distance:** The existing query uses `ST_DWithin` with degree-based radius via `miles_to_degrees()`. This is latitude-dependent and makes the "X miles" slider lie at different latitudes. The new query casts to `geography` so units are meters/miles directly.

**Add to `services/walkability.py`:**

- `query_walkability_by_coords(lon, lat, radius_miles, conn=None)` → `GeoDataFrame` — new spatial query using geography:

  ```sql
  SELECT geoid20, d2a_ranked, d2b_ranked, d3b_ranked, d4a_ranked, natwalkind,
         ST_AsBinary(geometry) as geometry,
         ST_Distance(
           geometry::geography,
           ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
         ) / 1609.344 AS dist_miles
  FROM national_walkability_index
  WHERE ST_DWithin(
    geometry::geography,
    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
    %s  -- radius in meters
  )
  ```

  Radius is passed as `radius_miles * 1609.344` (meters). Returns GDF with a `dist_miles` column pre-computed by PostGIS — this is the **minimum distance from the origin point to the polygon boundary** (0 if the point is inside the polygon), not centroid distance. This is actually better for split logic and upgrade ranking because it answers "how close does the polygon get to the point." Document this explicitly so no one "fixes" it back to centroids/Haversine later. Same memoryview handling, same connection lifecycle pattern as existing code.

- Keep `get_walkability_data()` intact (delegates to `query_walkability_by_coords` internally) so existing callers and tests don't break.

**Note on index usage:** `ST_DWithin` with `::geography` casts can still use the existing GIST index on the `geometry` column — PostGIS optimizes this internally. Unlikely to be a problem at 203k rows, but add a verification step: run `EXPLAIN (ANALYZE, BUFFERS)` on the query once in prod-like conditions to confirm no sequential scan.

**Add to `tests/test_walkability.py`:**
- Tests for `query_walkability_by_coords` — verify `dist_miles` column is present, same pattern as existing `TestWalkabilityData` class

**Files:** Modify `services/walkability.py`, modify `tests/test_walkability.py`

---

## Phase 3: Profile data layer in `map_display.py`

**Why:** The Streamlit caching boundary needs a new function that fetches both GDFs and returns the computed profile.

**Add to `components/map_display.py`:**

- `cached_get_profile(location_string, buffer_radius_miles, search_radius_miles, min_delta)` → `dict | None`
  - Uses `cached_get_location()` (already cached) for geocoding
  - Calls `query_walkability_by_coords()` **once** with `search_radius_miles` (the larger radius)
  - Splits the result: `selected_gdf = full_gdf[full_gdf['dist_miles'] <= buffer_radius_miles]`
  - Calls `compute_full_profile()` from `services/metrics.py` with both GDFs
  - Returns profile dict augmented with `location` and `selected_gdf` (for map rendering)
  - Same closed-connection recovery pattern as existing `cached_get_walkability_data`

**Add to `tests/test_connection_caching.py`:**
- `TestCachedGetProfile` class — mock chain, verify single query with search radius, verify GDF split logic, verify None on geocode failure

**Files:** Modify `components/map_display.py`, modify `tests/test_connection_caching.py`

---

## Phase 4: Sidebar controls + summary cards UI

**Why:** With the data layer complete, wire up the new UI layout.

**Modify `components/sidebar.py`:**
- Add search radius slider (range: buffer+0.1 to 25 miles, default 3.0)
- Add min delta slider (range: 0.5 to 10.0, default 2.0)
- Update return to `(city_name, buffer_radius_miles, search_radius_miles, min_delta)`

**Modify `app.py`:**
- Unpack four values from `render_sidebar()`
- Pass all four to `render_main_content()`

**Modify `components/map_display.py` — `render_main_content`:**
- Accept four parameters instead of two
- Call `cached_get_profile()` instead of separate geocode + data fetch
- New layout order:
  1. **Summary cards** (top) — 4 columns via `st.columns(4)`: Everyday Convenience, Transit Viability, Variation, Upgrade Potential. Each with numeric value + tooltip from metric definition. No red/green color coding.
  2. **Walkable Island banner** — `st.info()` if island check triggers
  3. **Map** (middle) — existing choropleth, demoted from headline to evidence layer
  4. **Nearby-better list** — ranked table of qualifying upgrade candidates, or explicit "none found"
  5. **Raw data table** (bottom, collapsed) — existing table inside `st.expander()`

**Add `render_summary_cards(profile)` and `render_nearby_better_list(profile)` functions** to `map_display.py`.

**Files:** Modify `components/sidebar.py`, `app.py`, `components/map_display.py`

---

## Phase 5: Map rendering cleanup

**Why:** The current `create_map` uses `RdYlBu` (red/green moral framing) and blue dot markers. The product plan requires neutral presentation.

**Modify `services/walkability.py` — `create_map`:**
- Extract palette to a module-level constant: `CHOROPLETH_COLORMAP = "Blues"` (single-hue sequential — no green/red moral implication). `YlGnBu` still has green baked in; single-hue is safest for the guardrail.
- Replace individual `folium.Circle` markers with `folium.GeoJsonTooltip` on the GeoJson layer — shows Block Group, NWI Score, Transit Proximity Rank, Land-Use Mix Rank, Intersection Density Rank on hover
- Update popup/legend text to use consistent metric names (e.g., "NWI Score" not "NatWalkInd")
- Label `d4a_ranked` as **"Transit Proximity Rank (lower = closer to transit)"** everywhere — the directionality must be explicit because rank fields are ambiguous about which end is "good"
- All `d4a_ranked` tooltip/label text must include "(proxy)" to comply with interpretation guardrails

**Directionality reference (EPA NWI dataset):**
- `d2a_ranked`: 1 = lowest employment+housing mix, 20 = highest
- `d2b_ranked`: 1 = lowest employment type diversity, 20 = highest
- `d3b_ranked`: 1 = lowest intersection density, 20 = highest
- `d4a_ranked`: 1 = farthest from transit, 20 = closest to transit
- `natwalkind`: 1 = least walkable, 20 = most walkable

All labels must reflect this (e.g., "higher = more walkable" for NWI).

Note: Keeping `create_map` in `walkability.py` for now to minimize churn. Moving it to the component layer is a clean-up for the FastAPI migration phase, when Folium rendering must be fully separated from the service layer.

**Add to `tests/test_walkability.py`:**
- Assert `CHOROPLETH_COLORMAP == "Blues"` (test the constant, not Folium object introspection — Folium internals are not stable for assertions)
- Mock `folium.Choropleth` and verify `fill_color` kwarg matches the constant

**Files:** Modify `services/walkability.py`, modify `tests/test_walkability.py`

---

## Phase 6: Edge case hardening

- Empty GDF (rural ZIP with 0-2 block groups) → cards show "N/A", no crashes
- `search_radius_miles <= buffer_radius_miles` → `ValueError` from service layer
- Single block group → variation returns `None`, displayed as "N/A"
- All-NaN natwalkind column → all metrics return `None`
- Add edge case tests to `tests/test_metrics.py`

**Files:** Modify `services/metrics.py`, modify `tests/test_metrics.py`

---

## Verification Plan

After each phase:
1. `pytest -v` — all tests pass, no regressions
2. `pytest --cov=services --cov-report=term` — new functions have coverage

After Phase 2 (geography query):
1. Run `EXPLAIN (ANALYZE, BUFFERS)` on the new `ST_DWithin(::geography)` query against the production DB to confirm the GIST index is used (no sequential scan)
2. Manually verify `d4a_ranked` directionality: spot-check a few rows where `d4a_ranked=20` are near known transit stops

After Phase 4 (full integration):
1. `streamlit run app.py` — app loads without errors
2. Enter "Knoxville, TN", 1-mile radius → four summary cards render with numeric values
3. Set min_delta=0.5 → upgrade candidates appear in list
4. Set min_delta=10.0 → explicit "No improvement found" message
5. Enter a rural ZIP → cards show "N/A" gracefully
6. Verify no red/green color coding on map (Phase 5)
7. Hover block groups → tooltip shows all metric columns with "(proxy)" labels where applicable

---

## Key Files Summary

| File | Action |
|---|---|
| `services/metrics.py` | **Create** — all metric computations |
| `services/walkability.py` | **Modify** — add `query_walkability_by_coords` (geography-based SQL + `dist_miles`), update `create_map` palette/tooltips/directionality |
| `components/map_display.py` | **Modify** — add `cached_get_profile`, `render_summary_cards`, `render_nearby_better_list`, update `render_main_content` |
| `components/sidebar.py` | **Modify** — add search radius + min delta sliders |
| `app.py` | **Modify** — unpack new sidebar values |
| `tests/test_metrics.py` | **Create** — full test coverage for metrics |
| `tests/test_walkability.py` | **Modify** — tests for `query_walkability_by_coords` + map cleanup |
| `tests/test_connection_caching.py` | **Modify** — tests for `cached_get_profile` |

---

## Out of Scope (Future)

- FastAPI wrapper — only after bridge phase validates the data model
- React frontend — only after FastAPI is stable
- Comparison mode (side-by-side) — Phase 2 of the product plan
- `docs/dev_notes/lessons.md` creation — will be created with the first bug fix during implementation

---

## Execution Update (2026-02-14)

Status: Completed

Implemented:
- Phase 1: Added pure metrics service in `services/metrics.py` and full unit coverage in `tests/test_metrics.py`.
- Phase 2: Added `query_walkability_by_coords()` with geography distance and `dist_miles`; `get_walkability_data()` now delegates to this query.
- Phase 3: Added `cached_get_profile()` and profile composition in `components/map_display.py`.
- Phase 4: Added sidebar controls (`search_radius_miles`, `min_delta`) and profile-first UI flow (summary cards, island banner, nearby-better list, collapsed raw table).
- Phase 5: Updated map rendering to `CHOROPLETH_COLORMAP = "Blues"` and GeoJSON tooltips with explicit proxy/directionality labels.
- Phase 6: Added edge-case handling in metrics/profile flow (empty data, NaN values, invalid radius relationship) with tests.

Verification:
- `.\.venv\Scripts\python.exe -m pytest -v` passed.
- `.\.venv\Scripts\python.exe -m pytest --cov=services --cov-report=term` passed after installing `pytest-cov` (`TOTAL 88%`, `services/metrics.py 89%`, `services/walkability.py 85%`, `services/db.py 100%`).

Related files:
- `services/metrics.py`
- `services/walkability.py`
- `components/map_display.py`
- `components/sidebar.py`
- `app.py`
- `tests/test_metrics.py`
- `tests/test_walkability.py`
- `tests/test_connection_caching.py`
- `docs/dev_notes/lessons.md`
