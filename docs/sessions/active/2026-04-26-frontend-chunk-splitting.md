# Frontend Chunk Splitting

**Started:** 2026-04-26
**Branch:** `optimize-frontend-chunks`
**Plan:** `\home\runner\.cursor\plans\frontend_chunk_splitting_3a87ef7c.plan.md`

## Objective

Reduce Vite chunk-size warnings by splitting route and visualization code without changing user-facing behavior.

## Success Criteria

- Baseline and final `frontend` build chunk output are captured.
- Heavy non-default routes and visualization modules are lazy-loaded where it improves initial bundle size.
- Frontend typecheck, lint, relevant tests, and production build pass.

## Progress Log

### 2026-04-26 — Kickoff

- Created branch `optimize-frontend-chunks`.
- Preparing baseline production build before code changes.

### 2026-04-26 — Implementation

- Baseline `cd frontend && npm run build`: single `index` JS chunk was 817.67 kB minified / 247.98 kB gzip and triggered the Vite 500 kB chunk warning.
- Lazy-loaded non-default routes in `frontend/src/App.tsx`: `Compare`, `Dashboard`, and `Method`.
- Post-route-split build: warning cleared; `index` JS chunk dropped to 414.95 kB minified / 128.81 kB gzip, with `Dashboard` isolated at 389.68 kB minified.
- Lazy-loaded Dashboard chart modules in `frontend/src/pages/Dashboard.tsx` so Recharts-backed charts load behind localized `Suspense` boundaries.
- Final build: warning remained clear; `Dashboard` shell dropped to 13.76 kB minified, chart code split into focused lazy chunks, and `index` stayed at 414.97 kB minified / 128.81 kB gzip.
- Verification: `npm run typecheck`, `npm run lint`, `npm run test:run`, and `npm run build` pass. Browser smoke test passed for `/`, `/compare`, `/dashboard`, and `/method`.
- Note: build currently prints the existing Node version advisory (`20.18.2`; Vite asks for `20.19+` or `22.12+`) but completes successfully.
