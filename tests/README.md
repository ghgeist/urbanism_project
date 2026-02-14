# Test Suite

Lightweight smoke tests for the walkability index project. These tests use mocks to avoid requiring a live database connection, making them fast and suitable for CI/CD.

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test class
pytest tests/test_walkability.py::TestInputValidation

# Run with coverage (if pytest-cov is installed)
pytest --cov=services --cov-report=html
```

## Test Coverage

- **Input Validation**: Location strings and buffer sizes
- **Distance Conversion**: Miles to degrees conversion logic
- **Geocoding**: Location lookup with mocked Nominatim
- **Data Fetching**: Database queries with mocked connections
- **API Contract**: Endpoint behavior and error envelope guarantees
- **Profile Metrics**: Core metric math, invariants, and upgrade-potential filtering
- **Connection Handling**: Closed/open DB connection behavior in walkability queries

## Adding New Tests

When adding new functionality, add corresponding tests following the existing pattern:
- Use descriptive test class names (`TestFeatureName`)
- Use descriptive test method names (`test_feature_behavior`)
- Mock external dependencies (database, geocoding service)
- Test both success and failure cases
