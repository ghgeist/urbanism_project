# Lessons Learned

## 2026-02-14

- Keep test classes aligned to the function under test; misplaced tests pass but hide intent and make maintenance/debugging slower.
- For geography distance queries on a geometry-indexed table, use an indexable geometry bbox prefilter (`geometry && ST_Expand(...)`) before exact `ST_DWithin(...::geography, ...)`.
- Geocoding (Nominatim/OSM) often uses US spelling for US addresses; if the user enters UK variants (e.g. "harbour" in a street name), normalize (e.g. harbour→harbor) and retry before treating the address as not found.
- When two pages share the same URL-driven search pattern (parse params → sync state → fetch when valid, replaceState on edit, pushState on submit), extract a generic hook (e.g. `useUrlDrivenSearch`) parameterized by parse/build/canFetch/fetch so behavior and fixes live in one place. Use a ref for options to avoid effect re-running on every render when callers pass inline fetch functions.
- When adding or changing API error codes: update the backend (where the code is set), the `ErrorResponse` docstring in `api/schemas.py` (canonical list), and the frontend `API_ERROR_MESSAGES` map in `frontend/src/api/client.ts` so user-facing messages stay in sync.
- When adding an early-return in a sync effect (e.g. “skip when weJustSetParamsRef”), ask: “What state does the effect normally set? Is that state updated on the path that causes the skip?” If the effect usually calls setState(X), the code path that sets the skip flag must also set X (e.g. `updateDraft` must call `setParams(next)` when the effect skips and would have run `setParams(nextParams)`).
- For optional UI (tooltips, popovers): handle “no content” and “content cleared” explicitly—unbind/hide the element rather than only setting content to `""`—and add a test that clears the content and asserts the UI is removed or hidden.
- **Agents must not merge branches or PRs.** "Ship it" or "ready to ship" means commit, push, and leave the branch ready for the human to merge. See AGENTS.md "Agent boundaries."
- When deprecating a UI framework (e.g. Streamlit → React+FastAPI), migrate any valuable test coverage (e.g. connection-closed checks) to framework-agnostic test files before deleting framework-specific tests. Delete the framework's entry point, components, config, and deps in one pass; then grep the entire repo for stale references in comments and docstrings.
