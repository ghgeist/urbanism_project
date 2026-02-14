---
title: "Execute: React Explore Phase 1"
date: "2026-02-14"
status: "active"
session_type: "execute"
priority: "high"
tags: ["react", "frontend", "explore", "vite", "leaflet"]
related: ["docs/sessions/active/2026-02-14-slack-surface-explorer_product_plan.md"]
---

# Execute: React Explore Phase 1

**Branch:** `feature/react-explore-phase1`

## Objective

Build the first React UI that consumes the FastAPI walkability API: Explore page with search, radius, summary cards, map, and nearby-better table.

## Success Criteria

- [x] New branch created from `main`.
- [x] React app scaffold (Vite + React + TypeScript) in `frontend/`.
- [x] API client and types aligned with `NwiSummaryResponse`.
- [x] Explore page: address/ZIP/city search, radius slider, "Get summary" → call `/nwi/summary/by-query`.
- [x] Four summary cards: Everyday Convenience, Transit Viability, Variation, Upgrade Potential (neutral, no moral coloring).
- [x] Map (Leaflet) centered on origin with marker.
- [x] Walkable Island notice when applicable.
- [x] Nearby-better candidates table when available.
- [x] Shareable state via URL query params (Phase 1.1).
- [ ] Compare page (Phase 2).

## Progress Log

- 2026-02-14: Confirmed React-phase readiness: bridge phase and FastAPI with canonical schema and CORS in place.
- 2026-02-14: Created branch `feature/react-explore-phase1`.
- 2026-02-14: Scaffolded `frontend/` with Vite (react-ts), added react-router-dom, leaflet, react-leaflet, @types/leaflet.
- 2026-02-14: Added `src/types/api.ts` (NwiSummaryResponse and related), `src/api/client.ts` (geocode, nwiSummaryByQuery, health).
- 2026-02-14: Implemented `SummaryCards`, `MapView` (Leaflet, default icon fix), and `Explore` page with form, error state, island notice, nearby-better table.
- 2026-02-14: Wired `App.tsx` with BrowserRouter and `/` → Explore. Styling in `App.css` (metrics-first layout, neutral cards).
- 2026-02-14: `npm run build` succeeds; no linter errors.
- 2026-02-14: Phase 1.1 shareable URL state: `frontend/src/lib/exploreParams.ts` (parse/validate/canonicalize q and radius); Explore syncs from URL, replaceState on edit (no fetch on slider/input), pushState on "Get summary"; popstate restores and fetches; validation message for invalid params.

## Files Created/Modified

| Path | Change |
|------|--------|
| `frontend/` | New (Vite + React + TS + Leaflet) |
| `frontend/src/types/api.ts` | New – API types |
| `frontend/src/api/client.ts` | New – API client |
| `frontend/src/components/SummaryCards.tsx` | New |
| `frontend/src/components/MapView.tsx` | New |
| `frontend/src/pages/Explore.tsx` | New |
| `frontend/src/App.tsx` | Replaced – router + Explore route |
| `frontend/src/App.css` | Replaced – explore + summary card styles |
| `frontend/.env.example` | New – VITE_API_URL |
| `frontend/src/test/setup.ts` | New – Vitest setup (jest-dom, cleanup) |
| `frontend/src/api/client.test.ts` | New – API client unit tests |
| `frontend/src/components/SummaryCards.test.tsx` | New – SummaryCards unit tests |
| `frontend/e2e/explore.spec.ts` | New – Playwright E2E smoke tests |
| `frontend/playwright.config.ts` | New – Playwright config + webServer |
| `docs/sessions/backlog/2026-02-14-react-deferred.md` | New – Deferred items backlog |
| `frontend/src/lib/exploreParams.ts` | New – URL param parse/validate/canonicalize (Phase 1.1) |
| `frontend/src/pages/Explore.tsx` | Modified – URL sync, replaceState on edit, pushState on submit |

## How to Run

1. Start the API: `uvicorn api.main:app --reload` (from repo root, with PG* env set).
2. Start the frontend: `cd frontend && npm run dev` (default port 5173).
3. Open http://localhost:5173, enter an address or city, set radius, click "Get summary".

## Quick E2E and tooling (2026-02-14)

- Added Vitest + `src/test/setup.ts`, unit tests for `client` and `SummaryCards`. Run: `npm run test` / `npm run test:run`.
- Added Playwright: `playwright.config.ts`, `e2e/explore.spec.ts`. Smoke tests: page load, form present, search yields cards or error. Run: `npm run e2e` or `npm run e2e:run`. First time: `npx playwright install chromium`. If the dev server fails to start (e.g. Windows/OneDrive Vite deps cache), start the frontend manually (`npm run dev`) then run `npm run e2e:run` so Playwright reuses the existing server.
- ESLint: scoped to `src/**` and config/e2e with Node globals where needed. Run: `npm run lint`.

## Deferred items (documented)

The following are intentionally left for a later slice and tracked in backlog:

| Item | Description | Backlog |
|------|-------------|---------|
| **Shareable state** | Location + radius in URL query params so results can be shared | [2026-02-14-react-deferred.md](../backlog/2026-02-14-react-deferred.md) |
| **Compare page** | Two locations side-by-side with highlighted metric differences | Same |
| **Vite API proxy** | Optional `/api` proxy to backend for same-origin dev | Same |
| **API error mapping** | Map API `ErrorResponse.code` (e.g. `location_not_found`) to user-facing copy | Same |

## Next Steps

- Add Compare page when Explore is stable (Phase 2).
- Optional: proxy `/api` in Vite; improve error messages from API codes.
