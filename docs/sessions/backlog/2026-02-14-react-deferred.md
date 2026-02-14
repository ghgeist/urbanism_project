---
title: "React Phase – Deferred Items"
date: "2026-02-14"
status: "backlog"
tags: ["react", "frontend", "url-state", "compare", "ux"]
related: ["docs/sessions/active/2026-02-14-execute-react-explore-phase1.md"]
---

# React Phase – Deferred Items

Items explicitly deferred from the initial React Explore phase. Pick up in order of product priority.

## ~~1. Shareable state (URL query params)~~ ✅ Done (Phase 1.1)

Implemented in Phase 1.1: `exploreParams.ts`, replaceState on edit, pushState on submit, validation. See session progress log.

---

## ~~1. Compare page~~ ✅ Done (Phase 2)

Implemented on branch `feature/react-explore-phase2`: `/compare` with `a`, `b`, `radius` URL params; two panels; B shows neutral deltas vs A (e.g. "+0.5 vs A"). See `docs/sessions/active/2026-02-14-execute-react-explore-phase2.md`.

---

## 2. Vite API proxy (optional)

**Goal:** In dev, avoid CORS by proxying `/api` to the FastAPI backend.

- In `vite.config.ts`: `server: { proxy: { '/api': 'http://127.0.0.1:8000' } }`.
- Frontend calls `get('/api/health')` etc. when `VITE_API_URL` is unset or points to same origin.
- Document in `frontend/README.md`.

**Acceptance:** `npm run dev` works without CORS when backend runs on 8000 and frontend uses relative `/api` or configured base URL.

---

## 3. API error mapping

**Goal:** Map backend `ErrorResponse.code` to clear, user-facing messages.

- Backend returns `location_not_found`, `invalid_request`, `validation_error`, etc.
- Frontend maps these to short messages (e.g. "Location not found. Try a city or ZIP.").
- Keep generic fallback for unknown or network errors.

**Acceptance:** User sees a specific message for "location not found" vs "invalid request" vs generic failure.
