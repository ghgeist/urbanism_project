"""Test that backend error codes stay in sync with frontend error messages.

This test prevents a common regression: adding or changing error codes in the backend
without updating the frontend API_ERROR_MESSAGES mapping.
"""
import re
from pathlib import Path

import pytest


def test_error_codes_sync():
    """Backend error codes documented in api/schemas.py must have frontend messages."""
    # Read backend canonical error codes from ErrorResponse docstring
    schemas_path = Path(__file__).parent.parent / "api" / "schemas.py"
    schemas_content = schemas_path.read_text()
    
    # Extract codes from the docstring (format: "code: description")
    docstring_match = re.search(
        r'Canonical codes used by this API:\s*(.*?)(?=\n\s*"""|\Z)',
        schemas_content,
        re.DOTALL,
    )
    assert docstring_match, "Could not find ErrorResponse docstring with canonical codes"
    
    docstring = docstring_match.group(1)
    backend_codes = set()
    for line in docstring.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Handle bullet point format: "- code: description" or "code: description"
        # Strip leading "- " if present
        if line.startswith("-"):
            line = line[1:].strip()
        # Extract code from lines like "location_not_found: description"
        code_match = re.match(r"^(\w+):", line)
        if code_match:
            backend_codes.add(code_match.group(1))
    
    # Also check for http_<status> pattern mentioned in docstring
    if "http_<status>" in docstring or "http_404" in docstring or "http_422" in docstring:
        backend_codes.add("http_404")
        backend_codes.add("http_422")
    
    assert backend_codes, "No error codes found in backend docstring"
    
    # Read frontend error messages
    client_path = Path(__file__).parent.parent / "frontend" / "src" / "api" / "client.ts"
    client_content = client_path.read_text()
    
    # Extract codes from API_ERROR_MESSAGES object
    messages_match = re.search(
        r"const API_ERROR_MESSAGES[^=]*=\s*\{([^}]+)\}",
        client_content,
        re.DOTALL,
    )
    assert messages_match, "Could not find API_ERROR_MESSAGES in frontend client"
    
    messages_block = messages_match.group(1)
    frontend_codes = set()
    for line in messages_block.split("\n"):
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        # Extract code from lines like "code: message,"
        code_match = re.match(r"^(\w+):", line)
        if code_match:
            frontend_codes.add(code_match.group(1))
    
    assert frontend_codes, "No error codes found in frontend API_ERROR_MESSAGES"
    
    # Check that all backend codes have frontend messages
    missing = backend_codes - frontend_codes
    assert not missing, (
        f"Backend error codes missing from frontend API_ERROR_MESSAGES: {missing}. "
        f"Add mappings in frontend/src/api/client.ts"
    )
    
    # Warn about frontend codes not in backend (might be intentional, but worth checking)
    extra = frontend_codes - backend_codes
    if extra:
        # These might be intentional (e.g., http_404/http_422 are documented as fallbacks)
        # So we warn but don't fail
        print(f"Warning: Frontend codes not in backend docstring: {extra}")


def test_error_response_schema_matches_implementation():
    """ErrorResponse schema fields match what the API actually returns."""
    # This is a basic check - the actual response shape is tested in test_api.py
    # But we can verify the schema definition is reasonable
    from api.schemas import ErrorResponse
    
    # ErrorResponse should have code, message, and optional details
    assert hasattr(ErrorResponse, "model_fields")
    fields = ErrorResponse.model_fields
    assert "code" in fields
    assert "message" in fields
    assert "details" in fields
    
    # details should be optional (Any | None)
    assert fields["details"].is_required() is False
