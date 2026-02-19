# Backend Test Suite

Lightweight smoke tests for the Python/FastAPI backend. These tests use mocks to avoid requiring a live database connection, making them fast and suitable for CI/CD.

> **📖 For comprehensive testing documentation covering both backend and frontend, see [`docs/TESTING.md`](../docs/TESTING.md)**

## Running Tests

```bash
# Run all backend tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_walkability.py

# Run a specific test class
pytest tests/test_walkability.py::TestInputValidation

# Run with coverage (if pytest-cov is installed)
pytest --cov=services --cov-report=html
```

## Test Files

- **`test_db.py`**: DB connection factory, env var validation, port parsing, connection-closed detection
- **`test_walkability.py`**: Input validation, coordinate math, geocoding (Nominatim + Census fallback), PostGIS queries, connection handling
- **`test_profile_summary.py`**: API response schemas, block group data, profile computation
- **`test_error_code_sync.py`**: Cross-cutting test ensuring backend error codes match frontend error messages
- **`test_static_serving.py`**: SPA serving behavior, API route precedence (skipped if `frontend/dist` doesn't exist)

## Test Coverage

- **Input Validation**: Location strings, buffer sizes, coordinate ranges
- **Distance Conversion**: Miles to degrees conversion logic (latitude-aware)
- **Geocoding**: Location lookup with mocked Nominatim and Census Bureau fallback
- **Data Fetching**: Database queries with mocked connections
- **API Contract**: Endpoint behavior and error envelope guarantees
- **Profile Metrics**: Core metric math, invariants, and upgrade-potential filtering
- **Connection Handling**: Closed/open DB connection behavior in walkability queries
- **Error Code Sync**: Backend/frontend error code synchronization (prevents regressions)
- **Static/SPA serving**: When `frontend/dist` exists, API routes take precedence over the SPA catch-all, root serves `index.html`, and path-traversal requests are safe

## Adding New Tests

When adding new functionality, add corresponding tests following the existing pattern:

1. **Use descriptive names**: `TestFeatureName` (class), `test_feature_behavior` (method)
2. **Mock external dependencies**: Database, geocoding services, file I/O
3. **Test both paths**: Success cases and error cases
4. **Follow existing patterns**: See `test_walkability.py` for examples

### Example Test Structure

```python
from unittest.mock import Mock, patch

class TestFeatureName:
    @patch('services.module.external_dependency')
    def test_feature_behavior(self, mock_dependency):
        # Arrange
        mock_dependency.return_value = expected_value
        
        # Act
        result = function_under_test(input)
        
        # Assert
        assert result == expected_result
        mock_dependency.assert_called_once_with(input)
```

## Mocking Patterns

All backend tests use `unittest.mock` to avoid live dependencies:

- **Database connections**: Mock `services.db.get_db_connection()` and cursor objects
- **Geocoding services**: Mock `geopy.geocoders.Nominatim` and Census API calls
- **File I/O**: Mock `pathlib.Path.read_text()` or `open()` when needed

See `test_walkability.py` for comprehensive examples of mocking patterns.

## Related Documentation

- **Full testing guide**: [`docs/TESTING.md`](../docs/TESTING.md)
- **Frontend tests**: See `frontend/README.md` and `docs/TESTING.md`
- **Project overview**: [`README.md`](../README.md)
