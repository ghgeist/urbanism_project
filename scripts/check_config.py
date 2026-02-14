"""
Validate that required configuration is present.
Run this at startup or in CI/CD to catch missing env vars early.
"""
import sys
from services.db import validate_pg_env


def check_config():
    """Check for required database environment variables."""
    missing = validate_pg_env()

    if not missing:
        print("Database configuration found (all PG* env vars set)")
        return True

    print(f"ERROR: Missing database environment variables: {', '.join(missing)}")
    print("   Required: PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD")
    return False


if __name__ == "__main__":
    success = check_config()
    sys.exit(0 if success else 1)
