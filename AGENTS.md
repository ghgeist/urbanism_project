# AGENTS.md

Shared guidance for coding agents working in this repository.

## Scope and Priority

This file is platform-agnostic (Codex, Claude Code, Cursor, Gemini CLI, etc.).

Priority order when instructions conflict:
1. Direct user request
2. Runtime safety/tooling constraints
3. This file
4. Referenced docs

## Agent boundaries (do not override)

- **Do not merge branches or PRs.** Create branches, commit, push, and open or update PRs as requested. The human merges. Do not run `git merge` (or equivalent) to merge into main or any target branch unless the user explicitly instructs you to perform that specific merge.

## Project Snapshot

- App type: React + FastAPI geospatial app for EPA National Walkability Index exploration
- Core stack: React (Vite), FastAPI, Python, GeoPandas/Shapely, PostgreSQL + PostGIS, pytest
- Frontend: `frontend/` (React, React-Leaflet)
- API entry: `api/main.py`
- Core services: `services/db.py`, `services/walkability.py`

## Common Commands

```bash
uvicorn api.main:app --reload
cd frontend && npm run dev
pytest
pytest -v
pytest tests/test_walkability.py::TestInputValidation
python scripts/check_config.py
python scripts/validate_schema.py
pip-audit   # optional; check deps for known CVEs (not in CI, won't block shipping)
```

## Workflow Orchestration (Incorporated)

This section distills `agents/workflow-orchestration.md` for daily execution.

### 1) Plan before non-trivial work

- Use explicit planning for tasks with 3+ meaningful steps or architectural tradeoffs.
- If execution drifts or fails, stop and re-plan instead of compounding bad assumptions.

### 2) Session-first execution

Follow `agents/_session-management-core.md`:
- Check `docs/sessions/active/` for an existing relevant session before starting.
- Reuse an existing session when possible; otherwise create one in `docs/sessions/active/`.
- Session naming: `YYYY-MM-DD-[session-type]-[description].md`.
- Keep active sessions lean (1-2 max), update progress during work, then move completed sessions to `docs/sessions/completed/`.

### 3) Compounding engineering loop

Before and after meaningful fixes:
- Review `docs/dev_notes/lessons.md` and recent sessions for related failure patterns.
- After bug fixes or user corrections, add a concrete lessons rule to `docs/dev_notes/lessons.md`.
- Add or update tests so the same category of failure is caught automatically next time.

### 4) Verification before completion

Do not mark work done without evidence:
- Run relevant tests.
- Validate behavior of changed paths (and compare old/new behavior when relevant).
- Confirm no avoidable regressions are introduced.

### 5) Simplicity and minimal impact

- Prefer root-cause fixes over patches.
- Change only what is necessary.
- Avoid over-engineering for simple problems; demand elegance for complex ones.

## Definition of Done

A task is done when all apply:
- Requested behavior is implemented.
- Relevant tests pass (or limitations are explicitly documented).
- Session record is updated with outcomes and file links.
- Follow-up work is captured in `docs/sessions/backlog/` when needed.

## Canonical References

- Workflow orchestration: `agents/workflow-orchestration.md`
- Session rules (mandatory): `agents/_session-management-core.md`
- Session best practices: `agents/session-management-best-practices.md`
- Codex integration notes: `agents/_codex-integration-standard.md`
- Project overview/details: `README.md`, `CLAUDE.md`
