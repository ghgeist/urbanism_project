---
title: "Execute: Python lint setup with agent lint gate"
date: "2026-02-14"
status: "completed"
session_type: "execute"
priority: "medium"
tags: ["python", "lint", "ruff", "agents"]
author: "codex"
related: ["AGENTS.md", "README.md", "requirements.txt", "docs/dev_notes/lessons.md"]
---

# Execute: Python lint setup with agent lint gate

**Session Type**: EXECUTE
**Priority**: Medium
**Estimated Duration**: 30-45 minutes
**Status**: Completed

## Objective
Add a Python linting setup that is low-friction for contributors and make lint-error resolution an explicit agent expectation.

## Success Criteria
- [x] Ruff is configured for repository Python code.
- [x] A documented command exists to run Python lint checks.
- [x] Agent instructions explicitly require fixing lint errors before marking work done.
- [x] Setup is verified with command output evidence.

## Context
The user requested Python lint setup and explicit guidance for AI agents to fix lint errors. During implementation, Ruff config/dependency were already present in the current branch, so the primary work became enforcing and documenting lint execution expectations for agents and contributors.

## Progress Log
- 2026-02-14: Reviewed `AGENTS.md`, `agents/_session-management-core.md`, and `docs/dev_notes/lessons.md`.
- 2026-02-14: Confirmed Ruff config and dependency are present in the branch (`pyproject.toml`, `requirements.txt`).
- 2026-02-14: Updated repo guidance/docs to make lint checks and lint-error resolution explicit (`AGENTS.md`, `README.md`, `CLAUDE.md`, and platform integration standards under `agents/`).
- 2026-02-14: Standardized lint commands to `--no-cache` to avoid Ruff cache path failures in this OneDrive workspace.
- 2026-02-14: Verified setup with:
  - `python -m ruff check --no-cache api services scripts tests` → pass
  - `python -m pytest -v` (then `-q` re-run) → 73 passed

## Outcomes
- Python linting is present and validated; lint command usage is now standardized in docs for this workspace.
- Agent-facing docs now explicitly require fixing lint errors before completion.
- Verification passed with Ruff and full backend test suite.

## Related Work
- `pyproject.toml`
- `requirements.txt`
- `AGENTS.md`
- `README.md`
- `CLAUDE.md`
- `docs/dev_notes/lessons.md`

## Next Steps
- Optional: add Ruff to CI workflow so lint checks run automatically on every PR.
