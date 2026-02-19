# Design Philosophy: Fast Iteration + AI/Human Collaboration

This document explains how this experimental project balances **speed** with **maintainability** for both humans and AI coding agents.

## Core Principles

### 1. **Automated Safety Nets, Not Manual Gates**

**Problem:** Manual checks slow down iteration and are easy to forget.

**Solution:**
- ✅ CI/CD catches type errors, lint issues, and test failures automatically
- ✅ Quick validation scripts (`scripts/quick_check.sh` / `scripts/quick_check.ps1`) for local pre-commit
- ✅ Type safety enforced by TypeScript + CI (no "ship it and hope")

**Result:** You can iterate fast because automation catches mistakes before they reach main.

### 2. **Clear Patterns Over Complex Rules**

**Problem:** Too many rules slow down development; too few rules create chaos.

**Solution:**
- ✅ Documented patterns in `CLAUDE.md`, `AGENTS.md`, and `.cursor/rules/`
- ✅ Lessons learned in `docs/dev_notes/lessons.md` (concrete do/don't, not vague notes)
- ✅ Session-based work tracking (`docs/sessions/`) for context

**Result:** Both humans and AI agents can quickly understand "how we do things here."

### 3. **Failures Become Upgrades**

**Problem:** Same mistakes happen repeatedly.

**Solution:**
- ✅ Every bug fix → add test + update `lessons.md`
- ✅ CI prevents regressions automatically
- ✅ Session outcomes document what was learned

**Result:** The codebase gets better with each iteration, not worse.

### 4. **AI-Friendly Structure**

**Problem:** AI agents need clear context to work effectively.

**Solution:**
- ✅ Clear file organization (`api/`, `services/`, `frontend/src/`)
- ✅ Explicit type definitions (`frontend/src/types/api.ts`)
- ✅ Comprehensive documentation (`CLAUDE.md` for project context, `AGENTS.md` for workflow)
- ✅ Platform-agnostic agent standards (`agents/_*-integration-standard.md`)

**Result:** AI agents can quickly understand the codebase and contribute effectively.

## What Makes This Repo "AI-Friendly"?

### For AI Coding Agents

1. **Clear Entry Points:**
   - `AGENTS.md` - Start here for workflow
   - `CLAUDE.md` - Project-specific context
   - `docs/dev_notes/lessons.md` - Patterns to avoid

2. **Structured Context:**
   - Session files track work (`docs/sessions/active/`)
   - Lessons learned prevent repeated mistakes
   - API contracts documented (`docs/api_contract.md`)

3. **Automated Validation:**
   - CI catches errors automatically
   - Type checking prevents runtime issues
   - Tests ensure correctness

4. **Clear Patterns:**
   - File organization is consistent
   - Naming conventions are documented
   - Code structure follows established patterns

### For Humans

1. **Quick Onboarding:**
   - `CONTRIBUTING.md` - 5-minute quick start
   - `README.md` - Project overview
   - Clear architecture diagrams

2. **Fast Feedback:**
   - Quick check scripts for local validation
   - CI provides immediate feedback
   - Type errors caught before runtime

3. **Maintainable Structure:**
   - Clear separation of concerns
   - Well-documented code
   - Lessons learned prevent repeated mistakes

## Trade-offs

### What We Optimize For

✅ **Fast iteration** - CI catches issues, so you can move quickly  
✅ **Type safety** - Prevents entire classes of bugs  
✅ **Clear patterns** - Easy for new contributors (human or AI)  
✅ **Automated checks** - No manual gatekeeping  

### What We De-prioritize

⚠️ **Perfect test coverage** - Focus on critical paths, not 100% coverage  
⚠️ **Over-engineering** - Simple solutions over complex abstractions  
⚠️ **Premature optimization** - Optimize when needed, not before  
⚠️ **Manual processes** - Automate everything possible  

## Examples

### ✅ Good: Fast + Safe

```typescript
// Type-safe API client with clear error handling
export async function geocode(query: string): Promise<GeocodeResponse> {
  const response = await fetch(`${API_BASE_URL}/geocode?q=${encodeURIComponent(query)}`);
  if (!response.ok) {
    const error = await response.json();
    throw new ApiError(error.code, error.message);
  }
  return response.json();
}
```

**Why:** TypeScript catches type errors, CI validates it, clear error handling.

### ❌ Bad: Fast but Unsafe

```typescript
// No types, no error handling, breaks at runtime
async function geocode(q) {
  return fetch(`/geocode?q=${q}`).then(r => r.json());
}
```

**Why:** No type safety, no error handling, runtime failures.

### ✅ Good: Clear Pattern

```python
# Service layer with clear separation
def get_walkability_data(lat: float, lon: float, conn=None):
    """Get walkability data for coordinates."""
    if conn is None:
        conn = get_db_connection()
    # ... implementation
```

**Why:** Clear function signature, documented behavior, testable.

## Iteration Speed vs. Quality

**The Balance:**

- **Fast iteration:** CI catches issues automatically, so you can commit frequently
- **Quality:** Type safety + tests + lessons learned prevent regressions
- **Maintainability:** Clear patterns + documentation make changes easy

**The Result:** You can move fast **because** the safety nets are automated, not **despite** them.

## For New Contributors (Human or AI)

1. **Read:** `CONTRIBUTING.md` → `AGENTS.md` → `CLAUDE.md`
2. **Check:** `docs/sessions/active/` for existing work
3. **Review:** `docs/dev_notes/lessons.md` for patterns
4. **Work:** Make changes, run `quick_check.sh`, commit
5. **Learn:** Update `lessons.md` if you discover something new

## Summary

This repo is designed for **experimental projects** where:
- ✅ Speed matters (fast iteration)
- ✅ Quality matters (type safety, tests)
- ✅ Maintainability matters (clear patterns, documentation)
- ✅ AI collaboration matters (structured context, clear patterns)

**The key:** Automated safety nets enable fast iteration, not slow it down.
