# Lessons Learned

## 2026-02-14

- When adding `@st.cache_data` or `@st.cache_resource` functions, clear all related caches in test `setup_method()` to prevent stale cached values from bypassing mocked call assertions.
- Keep test classes aligned to the function under test; misplaced tests pass but hide intent and make maintenance/debugging slower.
- For geography distance queries on a geometry-indexed table, use an indexable geometry bbox prefilter (`geometry && ST_Expand(...)`) before exact `ST_DWithin(...::geography, ...)`.
- Geocoding (Nominatim/OSM) often uses US spelling for US addresses; if the user enters UK variants (e.g. "harbour" in a street name), normalize (e.g. harbour→harbor) and retry before treating the address as not found.
- When two pages share the same URL-driven search pattern (parse params → sync state → fetch when valid, replaceState on edit, pushState on submit), extract a generic hook (e.g. `useUrlDrivenSearch`) parameterized by parse/build/canFetch/fetch so behavior and fixes live in one place. Use a ref for options to avoid effect re-running on every render when callers pass inline fetch functions.
- When adding or changing API error codes: update the backend (where the code is set), the `ErrorResponse` docstring in `api/schemas.py` (canonical list), and the frontend `API_ERROR_MESSAGES` map in `frontend/src/api/client.ts` so user-facing messages stay in sync.
