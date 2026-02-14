"""Shared service/API constraints to reduce validation drift."""

# Query parameter maximum length for location strings.
MAX_QUERY_LENGTH = 200

# Service-level radius bounds (in miles).
MIN_RADIUS_MILES = 0.0
MAX_RADIUS_MILES = 50.0
