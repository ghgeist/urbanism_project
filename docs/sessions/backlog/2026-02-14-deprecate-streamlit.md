---
title: "Plan: Deprecate Streamlit UI"
date: "2026-02-14"
status: "backlog"
session_type: "plan"
priority: "medium"
tags: ["streamlit", "deprecation", "react", "fastapi", "migration"]
related: ["docs/sessions/backlog/2026-02-14-react-deferred.md", "docs/sessions/active/2026-02-14-execute-react-explore-phase1.md"]
---

# Plan: Deprecate Streamlit Aspect of Project

**Session Type**: PLAN  
**Priority**: Medium  
**Status**: Backlog

## Objective

Define a clear, low-risk path to retire the Streamlit UI while keeping the app’s behavior available through the React + FastAPI stack. No removal of Streamlit code until the replacement is feature-complete and documented.

## Context

- **Current state**: Two UIs coexist:
  - **Streamlit**: `app.py` → `components/sidebar.py`, `components/map_display.py`; uses `services/db.py`, `services/walkability.py`; Streamlit-specific caching (`@st.cache_resource`, `@st.cache_data`) in `map_display.py`.
  - **New stack**: `api/main.py` (FastAPI), `frontend/` (React), calling the same services.
- **Scope of “Streamlit”**: Entry point (`app.py`), Streamlit-only components (`components/sidebar.py`, `components/map_display.py`), Streamlit deps in `requirements.txt`, `.streamlit/config.toml`, and tests that mock `st` in `tests/test_connection_caching.py`, `tests/test_map_display_ui.py`.
- **Out of scope**: `services/db.py` and `services/walkability.py` stay; they are framework-agnostic and shared by the API.

**Parity note (2026-02-14):** Parity is close; React UI is preferred over Streamlit. Safe to treat Phase 1 as nearly complete and move toward Phase 2 (soft deprecation) when ready.

### Parity confirmation (codebase check)

| Feature | Streamlit | React + API | Notes |
|--------|-----------|-------------|--------|
| Address/ZIP/city search | ✓ | ✓ | Same geocode → summary flow. |
| Buffer/selected radius | ✓ (0.1–10 mi) | ✓ (0.1–3 mi) | React uses single radius; API supports same semantics. |
| Search radius (for nearby-better) | ✓ (slider, up to 25 mi) | Defaults only | Not in Explore UI; API uses `selected_radius` when omitted, so upgrade search is same circle. |
| Min delta (NWI improvement threshold) | ✓ (slider) | Default 2.0 | Not in Explore UI; API default applied. |
| Summary cards (4 metrics) | ✓ | ✓ | Everyday Convenience, Transit Viability, Variation, Upgrade Potential. |
| Walkable island message | ✓ | ✓ | Shown when applicable. |
| Map | Folium choropleth (block groups) | Leaflet center + marker + radius caption | React has no block-group geometry layer yet. |
| Nearby-better candidates table | ✓ | ✓ | Same data; React table matches. |
| Raw block group data (expander) | ✓ | — | Not in React UI; API does not expose raw rows. |

**Verdict:** Core flow (search → summary → metrics → island → map → nearby-better) is in place. Gaps: no search-radius or min-delta controls in the React UI, no choropleth (evidence layer deferred), no raw block-group table. Acceptable for soft deprecation; optional to add search_radius_miles + min_delta to Explore before full removal.

## Success Criteria

- [ ] React + FastAPI delivers parity (or agreed subset) with Streamlit for: search, buffer/search radius, min delta, map, summary metrics, nearby-better candidates, raw data table.
- [ ] Docs (README, CLAUDE.md, AGENTS.md, runbooks) no longer describe Streamlit as the primary or only way to run the app.
- [ ] Streamlit code and config removed; `streamlit` and `streamlit-folium` removed from `requirements.txt`.
- [ ] Tests that targeted Streamlit UI are removed or replaced by API/frontend tests; test suite still passes.
- [ ] One clear “run the app” path (e.g. API + frontend) documented.

## Deprecation Phases

### Phase 1: Parity and documentation (before removal)

1. **Feature parity**
   - Confirm React Explore implements: address/place search, buffer radius, search radius, min delta, map (Folium or equivalent), summary metrics, “nearby-better” candidates, raw block group data (or link to API).
   - Close any gaps from [2026-02-14-react-deferred.md](2026-02-14-react-deferred.md) that are required for deprecation (e.g. shareable URL state if that’s the replacement for “share this view”).

2. **Docs and commands**
   - In README, CLAUDE.md, AGENTS.md: state that the canonical app is React + FastAPI; document `streamlit run app.py` as deprecated and scheduled for removal (with target date or “after parity”).
   - Update “Common Commands” to lead with API + frontend (e.g. `uvicorn api.main:app`, `npm run dev` in `frontend/`).
   - Add a short “Deprecation: Streamlit” section: what’s deprecated, why, and where to use the new stack.

3. **Runbooks / deployment**
   - If Replit or any env currently starts Streamlit, add a runbook step to switch to API + frontend and remove Streamlit from start command when ready.

### Phase 2: Soft deprecation (Streamlit still runnable)

4. **Deprecation warnings**
   - In `app.py`, log or print a one-time deprecation notice when the app starts (e.g. “Streamlit UI is deprecated; use the React app and API. See README.”).
   - Optionally add a banner in the Streamlit UI (e.g. `st.warning("This UI is deprecated…")` at top of main content).

5. **Tests**
   - Ensure all behavior covered by `test_connection_caching.py` and `test_map_display_ui.py` is covered by API or frontend tests (e.g. `test_api.py`, frontend e2e). Then mark the Streamlit UI tests as deprecated or move them to a “legacy” suite that’s excluded from default `pytest` run, with a comment that they will be removed when Streamlit is removed.

### Phase 3: Removal

6. **Delete Streamlit surface**
   - Remove or replace entry point: delete `app.py` or replace with a minimal script that prints “Use the React app and API” and exits (or redirects to docs).
   - Remove `components/sidebar.py` and `components/map_display.py` (or move to `docs/archive/` / `_deprecated/` if you want to keep a reference).
   - Remove `streamlit` and `streamlit-folium` from `requirements.txt`.
   - Remove `.streamlit/` directory (e.g. `config.toml`).

7. **Caching and connection logic**
   - `map_display.py` holds `get_cached_db_connection()` and `@st.cache_data` wrappers. Before deletion, ensure the API has equivalent behavior (e.g. connection pooling or per-request connections as already used by FastAPI). Migrate any caching logic that’s still needed into `api/` or `services/` (e.g. in-memory or response caching for expensive geocode/DB calls).

8. **Tests**
   - Remove `tests/test_connection_caching.py` and `tests/test_map_display_ui.py` (or their Streamlit-specific parts). Keep or add API tests for connection handling and for any “map display” behavior that’s now in the API (e.g. summary response shape).
   - Run full test suite and fix any imports or references to removed modules.

9. **Docs and config**
   - Remove all Streamlit references from README, CLAUDE.md, AGENTS.md, and any runbooks.
   - Remove deprecation notice from old `app.py` if you kept a stub; or delete the stub once no longer needed.
   - Update Replit or other deployment config so the app starts only the API (and optionally serves or builds the frontend).

### Phase 4: Cleanup and lessons

10. **Final checks**
    - Grep for `streamlit`, `st.`, `streamlit_folium`, `folium_static` across the repo; fix or remove any remaining references.
    - Confirm `pytest` and any CI pass; confirm “run the app” instructions work for a new contributor.

11. **Lessons**
    - In `docs/dev_notes/lessons.md`, add a short note: “Streamlit was deprecated in favor of React + FastAPI; migration required moving caching/connection logic into API and retiring Streamlit-only components and tests.”

## Files and Directories to Touch

| Action   | Path |
|----------|------|
| Delete or stub | `app.py` |
| Delete         | `components/sidebar.py`, `components/map_display.py` |
| Edit           | `requirements.txt` (drop streamlit, streamlit-folium) |
| Delete         | `.streamlit/` (e.g. `config.toml`) |
| Edit           | `README.md`, `CLAUDE.md`, `AGENTS.md` |
| Migrate/remove | Caching in `map_display.py` → API or services |
| Remove or replace | `tests/test_connection_caching.py`, `tests/test_map_display_ui.py` |
| Update         | Replit or deployment config (if applicable) |

## Dependencies and Ordering

- Phase 1 depends on React Explore phase 1 (and possibly deferred items) being done enough to declare parity.
- Phase 2 can start as soon as parity is agreed and docs are updated.
- Phase 3 should only start after a defined deprecation period (e.g. one release or 2–4 weeks) and after Phase 2 is done.
- Phase 4 is final verification and documentation.

## Risks and Mitigations

- **Risk**: Users or scripts still run `streamlit run app.py`.  
  **Mitigation**: Clear deprecation notice in Phase 2; README and CLI message point to new stack; remove entry point in Phase 3.

- **Risk**: Connection/caching behavior regresses when removing `map_display.py`.  
  **Mitigation**: Ensure API already uses `services/db.py` and has appropriate connection handling; add or keep API-level tests for that behavior before deleting Streamlit.

- **Risk**: Lost capability (e.g. a Streamlit-only feature).  
  **Mitigation**: Parity checklist in Phase 1; explicitly list any “we will not migrate” features and document them (e.g. “Compare page not in initial deprecation scope”).

## Next Steps

1. Confirm React + FastAPI parity (or agreed subset) with product/owner.
2. Create an active session for “Execute Streamlit deprecation” when ready (e.g. `docs/sessions/active/YYYY-MM-DD-execute-streamlit-deprecation.md`) and work through phases in order.
3. Optionally add a single backlog item: “Remove Streamlit after deprecation period” with a target date, and link it to this plan.

## Related Work

- [2026-02-14-react-deferred.md](2026-02-14-react-deferred.md) — React follow-ups (URL state, compare page, etc.).
- React Explore phase 1 active session (see `docs/sessions/active/`).
- `api/main.py`, `frontend/` — Replacement stack.
- `services/db.py`, `services/walkability.py` — Shared services; unchanged by this deprecation.
