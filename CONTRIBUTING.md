# Contributing Guide

This guide helps both **humans** and **AI coding agents** work effectively in this experimental project.

## Quick Start (5 minutes)

1. **Clone & setup:**
   ```bash
   git clone <repo-url>
   cd urbanism_project
   python -m venv .venv
   source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   cd frontend && npm install
   ```

2. **Set environment variables** (see `.env.example`):
   ```bash
   export PGHOST=...
   export PGDATABASE=...
   # ... etc
   ```

3. **Verify setup:**
   ```bash
   python scripts/check_config.py  # Check env vars
   cd frontend && npm run typecheck  # Check TypeScript
   ```

## Development Workflow

### For Humans

**Before starting work:**
- Check `docs/sessions/active/` for existing work
- Review `docs/dev_notes/lessons.md` for recent patterns
- Read relevant docs (`CLAUDE.md`, `AGENTS.md`)

**While working:**
- Run `cd frontend && npm run typecheck` frequently (or let CI catch it)
- Run `pytest` after backend changes
- Commit incrementally (especially before context limits)

**Before committing:**
- ✅ Type check: `cd frontend && npm run typecheck`
- ✅ Lint: `cd frontend && npm run lint` and `python -m ruff check --no-cache api services scripts tests`
- ✅ Tests: `pytest` and `cd frontend && npm run test:run`
- ✅ CI will catch issues automatically on push/PR

### For AI Agents

**Read these files first:**
- `AGENTS.md` - Core agent guidelines
- `CLAUDE.md` - Project-specific context
- `docs/dev_notes/lessons.md` - Patterns to avoid repeating
- `.cursor/rules/*.mdc` - Implementation patterns

**Session management:**
- Check `docs/sessions/active/` before starting
- Create session files: `docs/sessions/active/YYYY-MM-DD-[type]-[description].md`
- Update progress as you work
- Move completed sessions to `docs/sessions/completed/`

**Verification:**
- Always run type checks and lint before marking complete
- Add tests for bug fixes (per `AGENTS.md` compounding fixes)
- Update `docs/dev_notes/lessons.md` after fixes

## Code Patterns

### TypeScript/React
- Use `npm run typecheck` (not `npx tsc --noEmit`)
- Keep pure logic in `lib/` (no React imports)
- Extract reusable hooks to `hooks/`
- Route components in `pages/`, reusable UI in `components/`

### Python/FastAPI
- Service logic in `services/`, routes in `api/`
- Use `services/db.py` for all DB connections
- Mock database in tests (no live DB needed)
- Run `python -m ruff check --no-cache` before committing

## Common Tasks

**Add a new API endpoint:**
1. Add route in `api/main.py`
2. Add service logic in `services/`
3. Add tests in `tests/`
4. Update `docs/api_contract.md` if contract changes

**Add a new React page:**
1. Create component in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Add types in `frontend/src/types/`
4. Add tests if needed

**Fix a bug:**
1. Reproduce the issue
2. Fix the code
3. Add a test that would have caught it
4. Update `docs/dev_notes/lessons.md` with the pattern
5. Run all checks before committing

## CI/CD

GitHub Actions automatically runs on every push/PR:
- ✅ Frontend type check
- ✅ Frontend lint
- ✅ Frontend tests
- ✅ Backend lint
- ✅ Backend tests

**Don't merge if CI fails** - fix the issues first.

## Getting Help

- **Architecture questions:** See `CLAUDE.md` Architecture section
- **Agent workflow:** See `AGENTS.md` and `agents/workflow-orchestration.md`
- **Testing:** See `docs/TESTING.md`
- **Lessons learned:** See `docs/dev_notes/lessons.md`

## Experimental Project Notes

This is an experimental project - **speed and iteration matter**, but so does maintainability:

- ✅ **Do:** Add tests for critical paths, fix type errors, document patterns
- ✅ **Do:** Use CI to catch issues automatically
- ✅ **Do:** Update lessons.md when you learn something
- ⚠️ **Don't:** Over-engineer for edge cases
- ⚠️ **Don't:** Skip type checking (CI will catch it anyway)
- ⚠️ **Don't:** Commit broken code (CI blocks it)

**Balance:** Fast iteration + automated safety nets = sustainable experimentation
