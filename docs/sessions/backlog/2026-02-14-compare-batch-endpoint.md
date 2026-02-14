# Plan: Compare batch endpoint

**Created:** 2026-02-14  
**Status:** backlog  
**Tags:** api, performance, compare, frontend

## Objective

Add a single backend endpoint that returns NWI summaries for both Compare locations (A and B) in one request, and switch the Compare page to use it. This reduces HTTP round-trips and allows reusing one DB connection for both queries.

## Context

- The Compare page currently calls `nwiSummaryByQuery` twice (once for location A, once for B). Each call does one geocode and one DB query, so every compare incurs 2 geocodes + 2 DB operations and 2 HTTP requests.
- Noted in the performance-audit session as “Compare page doubles geocode + DB costs”; the chosen approach is a backend batch endpoint rather than frontend-level coordination.
- Backend already has connection pooling and geocode cache; the win here is one round-trip and one connection for both summaries.

## Scope

**In scope**

- New API endpoint (e.g. `GET /nwi/summary/compare`) that accepts two location queries and one radius, returns both summaries in one response.
- Response model and error behavior (e.g. 404 if either location not found).
- Frontend: new client function and Compare page wired to it instead of two separate calls.
- API test(s) for the new endpoint; update any frontend/Compare tests that mock the API.

**Out of scope**

- Changing Explore page or other endpoints.
- Frontend-level caching or cross-page state.
- Optional query params (e.g. `search_radius_miles`, `min_delta`, `top_n`) can be deferred: use same defaults as by-query for both A and B unless we want them in the first cut.

## Plan

### 1. API contract and response shape

- Decide path and query params: e.g. `GET /nwi/summary/compare?a=...&b=...&selected_radius_miles=...`. Reuse the same validation rules as `/nwi/summary/by-query` for each of `a` and `b` (min length, max length, no whitespace-only).
- Define response model: either `{ "a": NwiSummaryResponse, "b": NwiSummaryResponse }` or `{ "summaries": [NwiSummaryResponse, NwiSummaryResponse] }`. Document in `docs/api_contract.md` under “Evolving” (new endpoint).
- Error behavior: if either location is not found (`build_summary_from_location_query` returns `None`), return 404 with the same error envelope as by-query; no partial success in v1.

### 2. Backend implementation

- In `api/main.py` (or schemas): add the response model for the compare endpoint.
- Add the new route. Use one pooled connection; call `build_summary_from_location_query` for `a`, then for `b`, with the same `selected_radius_miles` (and default optionals if we add them). No new service-layer function required—reuse existing `build_summary_from_location_query`.
- Validate `a` and `b` (whitespace, length) the same way as `q` in the by-query endpoint; return 400/422 for invalid input before doing geocode/DB work.

### 3. Frontend implementation

- In `frontend/src/api/client.ts`: add a function (e.g. `nwiSummaryCompare(a, b, selected_radius_miles)`) that calls the new endpoint and returns a type that matches what the Compare page expects: `Promise<[NwiSummaryResponse, NwiSummaryResponse]>` (or equivalent tuple).
- In `frontend/src/pages/Compare.tsx`: replace the `fetch` implementation that currently uses `Promise.all([nwiSummaryByQuery(p.a, p.radius), nwiSummaryByQuery(p.b, p.radius)])` with a single call to the new client function. The rest of the page (params, URL sync, CompareTable) stays the same.

### 4. Tests

- **API:** Add a test (in `tests/test_api.py`) that mocks `build_summary_from_location_query` with `side_effect=[summary_a, summary_b]` and asserts the response body contains both summaries with the expected shape. Add a case where the first or second call returns `None` and assert 404 and error envelope.
- **Frontend:** If any test mocks `nwiSummaryByQuery` for the Compare flow, update it to mock the new compare client function (or the new URL) and assert a single request to the compare endpoint.

### 5. Docs and verification

- Update `docs/api_contract.md`: under “Evolving,” note that `GET /nwi/summary/compare` is added; no change to “Stable” section.
- Optional: add a one-line note in the performance-audit session that the Compare batch endpoint was implemented and the “doubles cost” item is addressed.
- Verification: run backend tests (`pytest`), frontend tests if present, and manually run Compare with two locations and confirm one network request and correct results.

## Success criteria

- Compare page triggers a single HTTP request for the compare action (and when loading with shareable URL params).
- Response contains both summaries; behavior and UI match current Compare (same validation, same error messages, same table).
- All existing tests pass; new API test covers success and 404 for one/both locations not found.
- API contract doc updated; no breaking changes to existing endpoints.

## References

- Performance audit note: `docs/sessions/active/2026-02-14-performance-audit.md` (Compare doubles geocode + DB costs).
- Existing by-query endpoint and validation: `api/main.py` (`nwi_summary_by_query`), `MAX_QUERY_LENGTH`, whitespace check.
- Compare page and hook: `frontend/src/pages/Compare.tsx`, `frontend/src/hooks/useUrlDrivenSearch.ts`.
- API client: `frontend/src/api/client.ts` (`nwiSummaryByQuery`).
