# Testing Guide

Comprehensive guide to the testing infrastructure for both backend (Python/FastAPI) and frontend (React/TypeScript) components.

## Overview

This project uses a multi-layered testing strategy:

- **Backend**: pytest with unittest.mock (no live database required)
- **Frontend**: Vitest + React Testing Library (unit tests) + Playwright (E2E)
- **Cross-cutting**: Error code synchronization tests

All tests use mocks to avoid external dependencies, making them fast and suitable for CI/CD.

---

## Quick Start

### Run All Tests

```bash
# Backend tests (from project root)
pytest

# Frontend unit tests (from project root)
cd frontend && npm run test:run

# Frontend E2E tests (from project root)
cd frontend && npm run e2e:run

# Run both backend and frontend tests
pytest && cd frontend && npm run test:run
```

### Run Specific Tests

```bash
# Backend: specific test file
pytest tests/test_walkability.py

# Backend: specific test class
pytest tests/test_walkability.py::TestInputValidation

# Backend: specific test method
pytest tests/test_walkability.py::TestInputValidation::test_invalid_location_string

# Frontend: specific test file
cd frontend && npm run test MapView.test.tsx

# Frontend: watch mode (development)
cd frontend && npm run test
```

---

## Backend Testing (Python/FastAPI)

### Test Framework

- **Framework**: pytest
- **Mocking**: unittest.mock (no live database connections)
- **Configuration**: `pytest.ini` (test discovery patterns)
- **Location**: `tests/` directory

### Test Structure

```
tests/
├── __init__.py
├── test_db.py              # DB connection factory, env validation
├── test_walkability.py     # Geocoding, PostGIS queries, profile computation
├── test_profile_summary.py # API response schemas, block group data
├── test_error_code_sync.py # Backend/frontend error code synchronization
└── test_static_serving.py  # SPA serving, API route precedence
```

### Running Backend Tests

```bash
# All tests
pytest

# Verbose output
pytest -v

# With coverage report
pytest --cov=services --cov-report=html

# Specific test file
pytest tests/test_walkability.py

# Specific test class
pytest tests/test_walkability.py::TestInputValidation

# Run tests matching a pattern
pytest -k "geocoding"
```

### Test Coverage Areas

- **Input Validation**: Location strings, buffer sizes, coordinate ranges
- **Distance Conversion**: Miles to degrees conversion (latitude-aware)
- **Geocoding**: Nominatim + Census Bureau fallback, error handling
- **Data Fetching**: PostGIS queries with mocked connections
- **API Contracts**: Endpoint behavior, error envelope guarantees
- **Profile Metrics**: Core metric math, invariants, filtering logic
- **Connection Handling**: DB connection lifecycle, closed connection detection
- **Error Code Sync**: Backend error codes match frontend error messages
- **Static/SPA Serving**: API route precedence, SPA catch-all behavior

### Mocking Patterns

Backend tests use `unittest.mock` to avoid live dependencies:

```python
# Example: Mocking database connection
from unittest.mock import Mock, patch

@patch('services.db.get_db_connection')
def test_walkability_query(mock_get_conn):
    mock_conn = Mock()
    mock_get_conn.return_value = mock_conn
    # ... test logic
```

**Key Mocking Principles:**
- Mock external services (Nominatim, Census API, PostgreSQL)
- Mock database connections and cursors
- Test both success and failure paths
- Verify mock calls match expected behavior

### Adding New Backend Tests

When adding new functionality:

1. **Create test file** (if new area): `tests/test_feature.py`
2. **Use descriptive names**: `TestFeatureName` (class), `test_feature_behavior` (method)
3. **Mock external dependencies**: Database, geocoding services, file I/O
4. **Test both paths**: Success cases and error cases
5. **Follow existing patterns**: See `tests/test_walkability.py` for examples

---

## Frontend Testing (React/TypeScript)

### Test Frameworks

- **Unit Tests**: Vitest + React Testing Library
- **E2E Tests**: Playwright
- **Location**: `frontend/src/**/*.test.ts` and `frontend/src/**/*.test.tsx`

### Test Structure

```
frontend/src/
├── api/
│   └── client.test.ts              # API client, error handling
├── components/
│   ├── MapView.test.tsx            # Map component, choropleth rendering
│   ├── SummaryCards.test.tsx       # Summary card display
│   └── CompareTable.test.tsx      # Comparison table
├── lib/
│   ├── exploreParams.test.ts       # URL parameter parsing (Explore page)
│   ├── compareParams.test.ts      # URL parameter parsing (Compare page)
│   └── radiusParams.test.ts       # Radius validation, canonicalization
└── hooks/
    └── useUrlDrivenSearch.test.tsx # URL-driven search hook
```

### Running Frontend Tests

```bash
# Unit tests (watch mode)
cd frontend && npm run test

# Unit tests (single run)
cd frontend && npm run test:run

# E2E tests (interactive)
cd frontend && npm run e2e

# E2E tests (headless)
cd frontend && npm run e2e:run

# Run specific test file
cd frontend && npm run test MapView.test.tsx

# Run tests matching a pattern
cd frontend && npm run test -t "renders map"
```

### Test Coverage Areas

- **Components**: Rendering, props, event handling, edge cases
- **API Client**: Request/response handling, error mapping, AbortSignal support
- **URL Parameters**: Parsing, validation, canonicalization (Explore, Compare, radius)
- **Hooks**: State management, URL synchronization, side effects
- **Type Safety**: TypeScript types match runtime behavior

### Mocking Patterns

Frontend tests use Vitest mocks:

```typescript
// Example: Mocking Leaflet (requires DOM)
import { vi } from "vitest";

vi.mock("leaflet", () => {
  return {
    map: vi.fn(() => mockMap),
    tileLayer: vi.fn(),
    marker: vi.fn(),
    geoJSON: vi.fn(),
    // ... other Leaflet exports
  };
});
```

**Key Mocking Principles:**
- Mock browser APIs (Leaflet, fetch, window.location)
- Mock React Router for route-dependent components
- Use React Testing Library for component testing (queries, user events)
- Test user interactions, not implementation details

### Adding New Frontend Tests

When adding new functionality:

1. **Create test file**: `ComponentName.test.tsx` or `utility.test.ts`
2. **Use React Testing Library**: `render`, `screen`, `userEvent`
3. **Mock external dependencies**: Leaflet, fetch, React Router
4. **Test user-facing behavior**: What users see and interact with
5. **Follow existing patterns**: See `frontend/src/components/MapView.test.tsx` for examples

---

## Cross-Cutting Tests

### Error Code Synchronization

**File**: `tests/test_error_code_sync.py`

**Purpose**: Ensures backend error codes (`api/schemas.py`) stay synchronized with frontend error messages (`frontend/src/api/client.ts`).

**How it works**:
1. Parses backend `ErrorResponse` docstring to extract canonical error codes
2. Parses frontend `API_ERROR_MESSAGES` object to extract error codes
3. Verifies all backend codes have corresponding frontend messages
4. Warns (but doesn't fail) on frontend codes not in backend (may be intentional)

**When to run**: Automatically runs with `pytest`. Should pass before merging PRs that change error handling.

**Adding new error codes**:
1. Add code to `ErrorResponse` docstring in `api/schemas.py`
2. Add message to `API_ERROR_MESSAGES` in `frontend/src/api/client.ts`
3. Run `pytest tests/test_error_code_sync.py` to verify sync

---

## Test Organization & Conventions

### Naming Conventions

- **Backend**: `test_*.py` files, `Test*` classes, `test_*` functions
- **Frontend**: `*.test.ts` or `*.test.tsx` files, `describe` blocks, `it` or `test` functions

### Test Structure

```python
# Backend example
class TestFeatureName:
    def test_feature_behavior(self):
        # Arrange
        # Act
        # Assert
```

```typescript
// Frontend example
describe("ComponentName", () => {
  it("should render correctly", () => {
    // Arrange
    // Act
    // Assert
  });
});
```

### Best Practices

1. **Fast tests**: All tests should run quickly (< 1 second per test)
2. **Isolated tests**: Tests should not depend on each other
3. **Clear assertions**: One logical assertion per test
4. **Descriptive names**: Test names should describe what they test
5. **Mock external dependencies**: Don't require live services or databases
6. **Test behavior, not implementation**: Focus on what users/consumers see

---

## CI/CD Integration

### Automated CI (GitHub Actions)

A GitHub Actions workflow (`.github/workflows/ci.yml`) automatically runs on every push and pull request:

- ✅ **Frontend Type Check**: `cd frontend && npx tsc --noEmit`
- ✅ **Frontend Lint**: `cd frontend && npm run lint`
- ✅ **Frontend Tests**: `cd frontend && npm run test:run`
- ✅ **Backend Lint**: `python -m ruff check --no-cache api services scripts tests`
- ✅ **Backend Tests**: `pytest --tb=short`

**Type errors will now be caught automatically in CI** before code is merged.

### Running Tests in CI

Tests are designed to run in CI/CD pipelines without external dependencies:

```bash
# Backend
pytest --tb=short

# Frontend
cd frontend && npm run test:run
cd frontend && npm run e2e:run
```

### Pre-commit Checklist

Before committing code (or rely on CI to catch issues):

- [ ] Backend tests pass: `pytest`
- [ ] Frontend unit tests pass: `cd frontend && npm run test:run`
- [ ] Python lint passes: `python -m ruff check --no-cache api services scripts tests`
- [ ] TypeScript type check passes: `cd frontend && npm run typecheck` (or `npx tsc --noEmit`)
- [ ] ESLint passes: `cd frontend && npm run lint`
- [ ] Error code sync test passes: `pytest tests/test_error_code_sync.py`

---

## Troubleshooting

### Backend Tests

**Issue**: Tests fail with database connection errors
- **Solution**: Tests use mocks; check that mocks are properly configured

**Issue**: Import errors
- **Solution**: Run tests from project root: `pytest` (not `python -m pytest tests/`)

### Frontend Tests

**Issue**: Leaflet/DOM errors
- **Solution**: Ensure Leaflet is mocked (see `MapView.test.tsx` for example)

**Issue**: Module resolution errors
- **Solution**: Run tests from `frontend/` directory or ensure paths are correct

**Issue**: E2E tests fail
- **Solution**: Ensure dev server is running or Playwright can start it automatically

---

## Test Coverage Goals

Current coverage focuses on:

- ✅ **Critical paths**: User-facing features, API contracts
- ✅ **Error handling**: All error codes and failure modes
- ✅ **Input validation**: All user inputs and edge cases
- ✅ **Regression prevention**: Tests catch breaking changes

Not currently targeting:
- ❌ 100% line coverage (focus on meaningful tests)
- ❌ Implementation details (focus on behavior)
- ❌ Third-party library internals

---

## Related Documentation

- **Backend test details**: `tests/README.md`
- **Frontend setup**: `frontend/README.md`
- **Project overview**: `README.md`
- **Development guide**: `CLAUDE.md`
- **Testing agent**: `agents/testing_agent.md`

---

## Questions?

If you're unsure about testing patterns or need help adding tests:

1. Check existing tests in the same area for patterns
2. Review this guide for conventions
3. See `agents/testing_agent.md` for testing philosophy
4. Follow the "compounding fixes" principle: every bug fix should include a test
