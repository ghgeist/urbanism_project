---
title: "Execute: Python lint setup with agent lint gate"
date: "2026-02-14"
status: "active"
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
**Status**: Active

## Objective
Add a Python linting setup that is low-friction for contributors and make lint-error resolution an explicit agent expectation.

## Success Criteria
- [ ] Ruff is configured for repository Python code.
- [ ] A documented command exists to run Python lint checks.
- [ ] Agent instructions explicitly require fixing lint errors before marking work done.
- [ ] Setup is verified with command output evidence.

## Context
The repo currently has frontend ESLint setup but no Python lint configuration (`pyproject.toml` and lint tools absent). The user requested setup and explicit guidance for AI agents to fix lint errors.

## Progress Log
- 2026-02-14: Reviewed `AGENTS.md`, `agents/_session-management-core.md`, and `docs/dev_notes/lessons.md`.
- 2026-02-14: Confirmed no existing Python lint tool config (`ruff`, `flake8`, `pylint`) at repo root.

## Outcomes
Pending.

## Related Work
- Pending.

## Next Steps
- Add `ruff` config and dependency updates.
- Update docs/agent guidance.
- Run lint/tests and record verification.
