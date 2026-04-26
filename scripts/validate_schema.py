"""
Validate that the database schema matches expected structure.
Run this after migrations or before deployment to catch schema drift.

Exit codes:
- 0: All critical checks passed. Warnings may still be printed.
- 1: Missing NWI table / PostGIS extension (hard failure — app will not work).

The WAS table is treated as optional: if missing, we print a warning but exit 0
so developers can run the app before the WAS loader has been invoked.
"""
import sys
from pathlib import Path

# Allow running as a standalone script from the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from services.db import get_db_connection  # noqa: E402

NWI_TABLE = "national_walkability_index"
NWI_COLUMNS = {
    "geoid20": "character varying",
    "d2a_ranked": "integer",
    "d2b_ranked": "integer",
    "d3b_ranked": "integer",
    "d4a_ranked": "integer",
    "natwalkind": "double precision",
    "geometry": "USER-DEFINED",
}

WAS_TABLE = "walkable_accessibility_score"
WAS_COLUMNS = {
    "geoid": "character varying",
    "was_2019": "numeric",
    "geometry": "USER-DEFINED",
}


def _fetch_columns(cursor, table_name: str) -> dict[str, str]:
    cursor.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY column_name;
        """,
        (table_name,),
    )
    return {row[0]: row[1] for row in cursor.fetchall()}


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables WHERE table_name = %s
        );
        """,
        (table_name,),
    )
    return bool(cursor.fetchone()[0])


def _index_exists(cursor, table_name: str, index_name: str) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT FROM pg_indexes WHERE tablename = %s AND indexname = %s
        );
        """,
        (table_name, index_name),
    )
    return bool(cursor.fetchone()[0])


def _validate_nwi(cursor) -> bool:
    """Critical: fail hard if NWI is missing."""
    if not _table_exists(cursor, NWI_TABLE):
        print(f"ERROR: Table '{NWI_TABLE}' does not exist")
        return False

    actual = _fetch_columns(cursor, NWI_TABLE)
    missing = set(NWI_COLUMNS.keys()) - set(actual.keys())
    if missing:
        print(f"ERROR: {NWI_TABLE} missing columns: {missing}")
        return False

    if not _index_exists(cursor, NWI_TABLE, "geometry_idx"):
        print(f"WARNING: Spatial index 'geometry_idx' not found on {NWI_TABLE} (performance may be slow)")

    print(f"OK: {NWI_TABLE} schema valid")
    return True


def _validate_was(cursor) -> None:
    """Optional: warn but do not fail if WAS is missing or incomplete."""
    if not _table_exists(cursor, WAS_TABLE):
        print(
            f"WARNING: Table '{WAS_TABLE}' does not exist. "
            "Run `python scripts/load_walkable_accessibility_score.py` to populate it. "
            "The API will still serve NWI-only responses in the meantime."
        )
        return

    actual = _fetch_columns(cursor, WAS_TABLE)
    missing = set(WAS_COLUMNS.keys()) - set(actual.keys())
    if missing:
        print(f"WARNING: {WAS_TABLE} missing columns: {missing}")
        return

    if not _index_exists(cursor, WAS_TABLE, "was_geom_idx"):
        print(f"WARNING: Spatial index 'was_geom_idx' not found on {WAS_TABLE} (performance may be slow)")

    print(f"OK: {WAS_TABLE} schema valid")


def validate_schema() -> bool:
    """Run all schema checks. Returns True if critical checks pass."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis');")
        if not cursor.fetchone()[0]:
            print("ERROR: PostGIS extension not enabled")
            return False
        print("OK: PostGIS extension enabled")

        nwi_ok = _validate_nwi(cursor)
        _validate_was(cursor)

        if not nwi_ok:
            return False

        print("\nSchema validation passed (warnings above, if any, are non-fatal)")
        return True

    except Exception as e:
        print(f"ERROR: Schema validation failed: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    success = validate_schema()
    sys.exit(0 if success else 1)
