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

### 2026-04-17 — Polish pass

Plan: `c:\Users\grant\.cursor\plans\was_integration_polish_pass_1e286cf8.plan.md` (all 20 todos complete).

- Citation added to Method page (new WAS subsection + glossary entries for Amenity Richness and Hollow Neighborhood), Footer (compact `EPA NWI · Credit et al. WAS 2019`), Amenity Richness card tooltip, README Data section, and `services/metrics.py` module + function docstrings.
- Single-sourced labels: `AMENITY_RICHNESS_LABELS` / `HOLLOW_NEIGHBORHOOD_LABEL` in `services/metrics.py`; Pydantic schemas narrowed to `Literal[...]`; frontend union in `types/api.ts` mirrors the same set. New test asserts the three sides stay in lock-step.
- Refactors: `_build_column_stats` helper collapses NWI/WAS stat builders; `get_sqlalchemy_url()` in `services/db.py` de-duplicates the URL logic and is reused by the loader.
- Loader retry: `_insert_chunk_with_retry` wraps `chunk.to_postgis` with `tenacity.retry` on `psycopg2.OperationalError` / SQLAlchemy `OperationalError`. Five tests in `tests/test_load_walkable_accessibility_score.py` (fast — tenacity sleep monkeypatched).
- Cache TTL: `_was_table_cache` is now `(value, expires_at_monotonic)` with a 5-min default TTL (overridable via `WAS_CACHE_TTL_SECONDS`). Public `reset_was_cache()` replaces direct attribute mutation; the `test_walkability.py` `autouse` fixture calls it. New tests cover caching, expiry, reset, and the invalid-env fallback.
- UI: new `.explore__hollow` CSS (amber stripe) decouples the Hollow banner from Walkable Island styling so dual-signal areas render two distinct banners.
- Docs: `.env.example` (created with full WAS section), README "WAS setup (one-time)" subsection, CLAUDE.md + AGENTS.md database description updated to describe both tables, two new lessons.md entries (Replit-internal hostnames, `.env` autoload placement), and this "Paper findings" + completion entry.
- Verification: ruff clean (0), 126 backend tests pass, 87 frontend tests pass, TypeScript + ESLint clean.

## Open Questions

- GEOID vintage confirmed by inference (almost certainly 2010); actual join rate vs. `geoid20` won't be measurable until `.env` + load are in place.
- Amenity Richness label thresholds use rough quartiles (≥20 / 10–20 / <10). Worth revisiting once real distribution is observable (a follow-up task for a later session).

## Paper findings (Credit et al. 2025)

Read-through of `docs/research/a-spatially-granular-open-source-measure-of-walkability-for.pdf`
and the [GitHub repo](https://github.com/kcredit/Walkable-Accessibility-Score):

- **Score range confirmed: 0–30.** The paper caps WAS at 30 by construction
  (sum of logistic-decay-weighted destination counts across the defined
  categories). Observed max across the continental US is 29.641, consistent
  with the inspection output (local max 29.0 on the sample).
- **Non-zero coverage.** Roughly 169,003 block groups across the continental
  US have non-zero WAS in 2019; most of the rest genuinely have no
  qualifying destinations within walking distance, i.e. `was = 0` is real
  signal, not a null.
- **Census vintage: 2010 block groups.** The paper explicitly uses 2015
  block-group population centroids as the demand units, which are the 2010
  Census block groups. This confirms our inspection-script assumption and
  the need to live with a partial join against NWI's 2020-vintage GEOID20
  (roughly 88% match expected).
- **NWI / WAS complementarity.** In the paper's §Conclusions the authors
  tested combining NWI and WAS and found it did not improve fit with
  commercial Walk Score®. That's the formal backing for surfacing them as
  independent signals in this app (and for the Hollow Neighborhood flag
  treating the high-NWI/low-WAS combination as informative rather than
  contradictory).
- **Distribution is heavy-tailed.** The top-50 block groups are concentrated
  in Manhattan and a handful of dense urban cores. The current Amenity
  Richness thresholds (≥20 Full / 10-20 Moderate / <10 Sparse) are
  eyeballed quartiles and are very likely miscalibrated — most US block
  groups will fall in "Sparse". Recheck after a real load and consider
  percentile-based cutoffs derived from the observed distribution.

## Carried-forward tasks (next session)

From `docs/sessions/backlog/2026-02-14-adding-in-walkability-accessibility-score.md`:
- Task 4: Historical Stability Trend (requires loading 1997+ years)
- Task 5: Update Upgrade Potential logic to require WAS improvement
- Plus the deferred "fun" visualizations: Hollow Neighborhood scatter view, temporal before/after swipe, radar chart for Compare.

### 2026-04-26 — WAS analytics follow-up

- Created branch `feature/was-analytics-followup`.
- Real database validation is complete: `python scripts/validate_schema.py` passes with both `national_walkability_index` and `walkable_accessibility_score` present.
- Added `scripts/summarize_was_distribution.py` for repeatable read-only checks after WAS loads.
- Current shared DB summary: 215,831 WAS rows, 215,831 distinct GEOIDs, 199,388 direct NWI matches, 92.38% naive join rate.
- Observed WAS 2019 distribution: min 0.00, p25 0.50, median 8.45, p75 21.19, p90 26.87, max 29.62.
- Amenity Richness thresholds remain at 10 and 20. Those cutoffs are rounded interpretation breakpoints near the live median / upper quartile, not exact quartiles.
- Added a Dashboard `NWI vs WAS` tab that visualizes per-block-group agreement/divergence between NWI and WAS, including Hollow Neighborhood quadrant counts.
- Pinned frontend `jsdom` to `26.1.0` because the current Node runtime (`v20.18.2`) cannot run `jsdom@28`'s transitive `require(ESM)` dependency path.
- Verification: `python -m ruff check --no-cache api services scripts tests`, `pytest` (137 passed), `cd frontend && npm run typecheck`, `cd frontend && npm run lint`, `cd frontend && npm run test:run` (92 passed), `npm audit --omit=dev` (0 production vulnerabilities).
