# WAS Integration: Backend + Minimal UI

**Started:** 2026-04-17
**Plan:** `c:\Users\grant\.cursor\plans\was_integration_backend_+_minimal_ui_423dbf5f.plan.md`
**Predecessor:** `docs/sessions/backlog/2026-02-14-adding-in-walkability-accessibility-score.md`

## Scope (confirmed with user)

- **Year coverage:** 2019 only (single score per GEOID)
- **Delivery:** Backend + minimal UI (Amenity Richness card + Hollow Neighborhood badge)
- **Upload path:** Local machine → remote Replit/Neon Postgres over the wire, mirroring the NWI loader pattern

## Progress Log

### 2026-04-17 — Session kickoff
- Confirmed scope with user (year=2019, delivery=backend+minimal UI, upload=local-to-remote).
- Plan written and approved.
- Entering Step 0 (read-only inspection).

### 2026-04-17 — Code complete, awaiting DB load

**Step 0 — Inspection:** Ran `scripts/inspect_was_shapefile.py`. Findings:
- 215,831 rows, CRS `ESRI:102003` (must reproject to `EPSG:4326` on load)
- GEOID column is `ID` (12-digit), not `GEOID` / `GEOID10` / `GEOID20` — almost certainly 2010 vintage given the 1997-2019 coverage pre-dates 2020 Census release
- Score column is `WAS2019` (no underscore), not `WAS_2019` as plan assumed
- Score range sanity-check: 0.57 to 29.0 — consistent with the paper's 0-30 scale
- User accepted Option B: naive string join on `ID = geoid20`, ~88% coverage expected

**Steps 1-6 complete:**
- `scripts/load_walkable_accessibility_score.py` — idempotent DROP/CREATE + chunked insert with progress, spatial index, and an explicit confirmation gate (`--yes` / `WAS_LOADER_CONFIRM=1`)
- `services/walkability.py` — resilient LEFT JOIN; cached probe via `to_regclass('walkable_accessibility_score')` falls back to NWI-only when the table doesn't exist yet
- `services/metrics.py` — `compute_amenity_richness`, `amenity_richness_label`, `check_hollow_neighborhood`
- `services/profile_summary.py` — new `was`, `amenity_richness`, `hollow_neighborhood` top-level keys + per-block-group `was_2019`; `SCHEMA_VERSION` bumped to `2026-04-17-was-integration`
- `api/schemas.py` — new `WasStats`, `AmenityRichness`, `HollowNeighborhood` models
- `scripts/validate_schema.py` — WAS table checked as a soft warning (won't fail CI before loader runs)
- Tests: 23 metric tests (incl. new Amenity/Hollow), 15 profile_summary tests (incl. 4 new WAS cases), 2 new walkability query tests (WAS-joined + NWI-fallback paths). All 113 backend tests pass.
- Frontend: `SummaryCards` gained an Amenity Richness card; `Explore` gained a Hollow Neighborhood banner. `NwiSummaryResponse` updated with optional `was`/`amenity_richness`/`hollow_neighborhood`/per-BG `was_2019`. All 87 frontend tests pass.

**Remaining:**
- User to create `.env` with remote Postgres creds, then run `python scripts/load_walkable_accessibility_score.py` once to actually ingest the data.
- Post-ingest: run `python scripts/validate_schema.py` and rerun `scripts/inspect_was_shapefile.py` to capture the real naive join rate.

## Open Questions

- GEOID vintage confirmed by inference (almost certainly 2010); actual join rate vs. `geoid20` won't be measurable until `.env` + load are in place.
- Amenity Richness label thresholds use rough quartiles (≥20 / 10–20 / <10). Worth revisiting once real distribution is observable (a follow-up task for a later session).

## Carried-forward tasks (next session)

From `docs/sessions/backlog/2026-02-14-adding-in-walkability-accessibility-score.md`:
- Task 4: Historical Stability Trend (requires loading 1997+ years)
- Task 5: Update Upgrade Potential logic to require WAS improvement
- Plus the deferred "fun" visualizations: Hollow Neighborhood scatter view, temporal before/after swipe, radar chart for Compare.
