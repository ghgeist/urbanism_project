---
title: "React Phase – Deferred Items"
date: "2026-02-14"
status: "backlog"
tags: ["react", "frontend", "url-state", "compare", "ux"]
related: ["docs/sessions/active/2026-02-14-execute-react-explore-phase1.md"]
---

# React Phase – Deferred Items

Items explicitly deferred from the initial React Explore phase. Pick up in order of product priority.

## 1. Shareable state (URL query params)

**Goal:** Location (query or lat/lon) and radius live in the URL so results can be shared.

- Sync `q` and `radius` (and optionally `search_radius_miles`, `min_delta`) with `?q=...&radius=...`.
- On load, read query params and run summary if valid.
- Update URL when user searches or changes radius (replaceState to avoid history spam).

**Acceptance:** Copying the URL and opening in a new tab shows the same summary (or triggers the same search).

---

## 2. Compare page

**Goal:** Two locations side-by-side with summary panels and highlighted metric differences (product plan §6).

- Route: e.g. `/compare` or `/compare?a=...&b=...`.
- Two search inputs (or shareable links for A and B).
- Render two `SummaryCards`-style panels; highlight which metrics improved or worsened for B vs A.
- No red/green moral framing—neutral difference display.

**Acceptance:** User can compare two addresses and see which metrics differ and by how much.

---

## 3. Vite API proxy (optional)

**Goal:** In dev, avoid CORS by proxying `/api` to the FastAPI backend.

- In `vite.config.ts`: `server: { proxy: { '/api': 'http://127.0.0.1:8000' } }`.
- Frontend calls `get('/api/health')` etc. when `VITE_API_URL` is unset or points to same origin.
- Document in `frontend/README.md`.

**Acceptance:** `npm run dev` works without CORS when backend runs on 8000 and frontend uses relative `/api` or configured base URL.

---

## 4. API error mapping

**Goal:** Map backend `ErrorResponse.code` to clear, user-facing messages.

- Backend returns `location_not_found`, `invalid_request`, `validation_error`, etc.
- Frontend maps these to short messages (e.g. "Location not found. Try a city or ZIP.").
- Keep generic fallback for unknown or network errors.

**Acceptance:** User sees a specific message for "location not found" vs "invalid request" vs generic failure.
