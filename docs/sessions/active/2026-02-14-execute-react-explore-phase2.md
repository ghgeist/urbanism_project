---
title: "Execute: React Explore Phase 2 (Compare)"
date: "2026-02-14"
status: "active"
session_type: "execute"
priority: "high"
tags: ["react", "frontend", "compare", "phase2"]
related: ["docs/sessions/active/2026-02-14-execute-react-explore-phase1.md", "docs/sessions/backlog/2026-02-14-react-deferred.md"]
---

# Execute: React Explore Phase 2 – Compare Page

**Branch:** `feature/react-explore-phase2` (created from `feature/react-explore-phase1`)

## Objective

Implement the Compare page: two locations side-by-side with summary panels and neutral metric differences (B vs A). Shareable URL state (`a`, `b`, `radius`).

## Success Criteria

- [x] Branch created from current (phase1).
- [x] Compare page at `/compare`: two search inputs, shared radius, "Compare" button.
- [x] URL params `a`, `b`, `radius`; parse/validate/canonicalize; replaceState on edit, pushState on submit.
- [x] Fetch both summaries via `nwiSummaryByQuery` (two calls); render two panels.
- [x] Panel B shows neutral deltas vs A (e.g. "+0.5 vs A", "same as A") in card hints; no red/green.
- [x] Unit tests for compareParams and SummaryCards with diffFrom; build and lint pass.

## Progress Log

- 2026-02-14: Created branch `feature/react-explore-phase2` from `feature/react-explore-phase1`.
- 2026-02-14: Added `frontend/src/lib/compareParams.ts` (parse/build/canFetchCompare, reuses radius bounds).
- 2026-02-14: Extended `SummaryCards` with optional `diffFrom` and `diffLabel`; neutral delta hints (formatDelta).
- 2026-02-14: Replaced Compare placeholder with full page: form, URL sync, dual fetch, two panels; B panel uses `diffFrom={summaryA}`.
- 2026-02-14: Compare CSS in `App.css` (form, panels grid, panel styling, mobile stack).
- 2026-02-14: Added `compareParams.test.ts` (9 tests), SummaryCards test for diffFrom (5 tests total in SummaryCards); 30 tests pass, build and lint pass.

## Files Created/Modified

| Path | Change |
|------|--------|
| `frontend/src/lib/compareParams.ts` | New – URL param parse/build for Compare |
| `frontend/src/lib/compareParams.test.ts` | New – unit tests |
| `frontend/src/components/SummaryCards.tsx` | Modified – optional diffFrom, diffLabel, formatDelta |
| `frontend/src/components/SummaryCards.test.tsx` | Modified – test for diffFrom/diffLabel |
| `frontend/src/pages/Compare.tsx` | Replaced – full Compare page |
| `frontend/src/App.css` | Modified – Compare page styles |
| **Refactors** | |
| `frontend/src/lib/radiusParams.ts` | New – single source for radius + MAX_QUERY_LENGTH, canonicalRadius, parseRadiusParam |
| `frontend/src/lib/radiusParams.test.ts` | New – unit tests |
| `frontend/src/lib/exploreParams.ts` | Modified – use radiusParams, parseRadiusParam |
| `frontend/src/lib/compareParams.ts` | Modified – use radiusParams instead of exploreParams |
| `frontend/src/hooks/useUrlDrivenSearch.ts` | New – generic URL-driven search hook |
| `frontend/src/hooks/useUrlDrivenSearch.test.tsx` | New – hook unit tests |
| `frontend/src/pages/Explore.tsx` | Refactored – use useUrlDrivenSearch |
| `frontend/src/pages/Compare.tsx` | Refactored – use useUrlDrivenSearch |
| `frontend/e2e/compare.spec.ts` | New – Compare page E2E smoke tests |
| `docs/dev_notes/lessons.md` | Modified – lesson on extracting URL-driven search hook |

## How to Run

1. API: `uvicorn api.main:app --reload` (PG* env set).
2. Frontend: `cd frontend && npm run dev`.
3. Open http://localhost:5173/compare; set Location A, Location B, radius; click "Compare". Shareable: `/compare?a=Cambridge%2C+MA&b=Somerville%2C+MA&radius=0.5`.

## Reflection & future refactors

**What went well:** Reused Explore patterns (URL-driven state, radius bounds, API client). Extended SummaryCards with optional diffFrom/diffLabel instead of duplicating; single source of truth for card layout. Tests for new code (compareParams, diffFrom). Session and backlog docs updated.

**What could be better:** If one of the two fetches fails, we clear both panels; partial results could improve UX. Compare has no map/island/upgrade table (Explore-only for now).

**Refactors completed (same branch):**
- **radiusParams:** `frontend/src/lib/radiusParams.ts` — single source for MIN_RADIUS, MAX_RADIUS, STEP, RADIUS_PRECISION, MAX_QUERY_LENGTH, canonicalRadius, parseRadiusParam. exploreParams and compareParams import from it.
- **useUrlDrivenSearch:** `frontend/src/hooks/useUrlDrivenSearch.ts` — generic hook (parse, build, canFetch, fetch, emptyFetchMessage). Explore and Compare both use it; URL sync, replaceState/pushState, and fetch-on-valid-params live in one place.
- **Explore & Compare refactored** to use the hook; pages are thinner and no longer duplicate effect/handler logic.
- **E2E for Compare:** `frontend/e2e/compare.spec.ts` — smoke tests: load/heading/button, A/B inputs and radius, submit yields panels or alert. Run with `npm run e2e:run` (ensure port 5000 free or dev server already up).
- **Hook test:** `frontend/src/hooks/useUrlDrivenSearch.test.tsx` — initial params from URL, empty URL.

**Still optional (backlog):** Backend `GET /nwi/compare`; partial result UX when one compare fetch fails.

## Next Steps

- Optional: Vite API proxy, API error mapping (backlog).
- Merge phase2 into phase1 (or main) when ready.
