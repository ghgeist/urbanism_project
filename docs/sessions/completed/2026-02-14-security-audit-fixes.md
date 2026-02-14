---
title: "Security audit and implementation (idiot insurance)"
date: "2026-02-14"
status: "completed"
session_type: "execute"
tags: ["security", "api", "fastapi", "audit"]
---

# Security audit and implementation

**Status:** Completed  
**Branch:** `security/audit-fixes` (not yet merged to main)

## Objective

- Perform a security audit per `agents/security_agent.md` (assessment only, no code).
- Implement the recommended fixes: cap query length, generic 500 handler, security headers.
- Add minimal production checklist docs (CORS, debug log, pip-audit) without blocking shipping.

## What was done

### Audit (no code)

- Mapped entry points, input validation, DB layer, error handling, config.
- Ranked gaps: unbounded `q`, no 500 handler, 422 details, no security headers, no rate limiting.
- Recommended one improvement: enforce `q` max length and reject whitespace-only at API boundary.

### Implementation (branch `security/audit-fixes`)

- **API (`api/main.py`):** `MAX_QUERY_LENGTH = 200`; `Query(max_length=200)` and whitespace check on `q` for `/geocode` and `/nwi/summary/by-query`. Global `Exception` handler returning generic 500 (`code=internal_error`). Security headers middleware: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.
- **Schemas:** `ErrorResponse` docstring updated with `internal_error` and empty-query `invalid_request`.
- **Tests (`tests/test_api.py`):** Query too long (422), whitespace-only (400), uncaught exception → 500, security headers present.

### Documentation (main or same branch)

- **README:** Production checklist under Deployment (CORS, no WALKABILITY_DEBUG_LOG, optional pip-audit).
- **.env.example:** Comments for production (API_CORS_ORIGINS, do not set debug log).
- **AGENTS.md:** pip-audit in common commands (optional).
- **CLAUDE.md:** API_CORS_ORIGINS and WALKABILITY_DEBUG_LOG in config.

### Follow-up (review-driven)

- **Frontend:** Added `internal_error` to `API_ERROR_MESSAGES` in `frontend/src/api/client.ts`.
- **README:** "20 smoke tests" → "100+ tests" in Testing & Validation.
- **walkability.py:** Docstring note in `validate_location_input` that API enforces same 200-char limit.
- **Session:** This file. **Review:** `docs/dev_notes/2026-02-14-security-audit-review.md`.

## Key files

- `api/main.py` — endpoints, middleware, exception handlers
- `api/schemas.py` — ErrorResponse docstring
- `tests/test_api.py` — API and security tests
- `README.md` — Production checklist
- `agents/security_agent.md` — Audit process

## Outcomes

- Idiot insurance in place without blocking iteration.
- Single branch with one commit for code; docs updated on same branch or main as appropriate.
- Future agents/humans can use the review doc and this session to see what was done and what was intentionally skipped (rate limiting, CI for pip-audit, 422 detail sanitization).
