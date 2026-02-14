---
title: "Debug: Discard dead pooled DB connections"
date: "2026-02-14"
status: "completed"
session_type: "debug"
priority: "high"
tags: ["database", "pooling", "psycopg2", "reliability"]
author: "codex"
related: ["docs/sessions/completed/2026-02-14-performance-audit.md"]
---

# Debug: Discard dead pooled DB connections

**Session Type**: DEBUG  
**Priority**: High  
**Estimated Duration**: 30m  
**Status**: Completed

## 🎯 Objective
Fix `services/db.py:return_connection` so dead psycopg2 connections are discarded from the pool instead of returned to it.

## 📋 Success Criteria
- [x] `return_connection` calls `_pool.putconn(conn, close=True)` for closed/dead connections.
- [x] Tests cover dead-connection return path and pass.
- [x] Relevant lint/tests pass for changed files.

## 🔍 Context
Cursor bugbot reported that closed connections skip rollback but are still returned via `_pool.putconn(conn)`, which can poison pool reuse on dropped cloud connections.

## 📝 Progress Log
- Confirmed current implementation in `services/db.py` returns closed connections without `close=True`.
- Confirmed current test `tests/test_db.py::TestReturnConnection::test_no_rollback_when_conn_closed` asserts the buggy behavior.
- Patched `services/db.py:return_connection` to discard closed connections with `_pool.putconn(conn, close=True)` and to best-effort discard on return errors.
- Updated `tests/test_db.py` assertions for closed/failed return paths to require `close=True`.
- Ran `.\.venv\Scripts\python.exe -m pytest -v tests/test_db.py` (18 passed).
- Ran `.\.venv\Scripts\python.exe -m ruff check --no-cache api services scripts tests` (all checks passed).

## 🎉 Outcomes
- Dead connections are no longer recycled into the pool, preventing persistent failure loops after dropped DB sessions.
- Regression coverage now enforces discard behavior for both explicitly closed connections and rollback-failure paths.

## 🔗 Related Work
- `services/db.py`
- `tests/test_db.py`

## 📈 Next Steps
1. Monitor production logs for any residual `Discarding connection after return failure` warnings.
