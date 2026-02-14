# Lessons Learned

## 2026-02-14

- When adding `@st.cache_data` or `@st.cache_resource` functions, clear all related caches in test `setup_method()` to prevent stale cached values from bypassing mocked call assertions.
- Keep test classes aligned to the function under test; misplaced tests pass but hide intent and make maintenance/debugging slower.
- For geography distance queries on a geometry-indexed table, use an indexable geometry bbox prefilter (`geometry && ST_Expand(...)`) before exact `ST_DWithin(...::geography, ...)`.
- Geocoding (Nominatim/OSM) often uses US spelling for US addresses; if the user enters UK variants (e.g. "harbour" in a street name), normalize (e.g. harbour→harbor) and retry before treating the address as not found.
