"""
Validate that the database schema matches expected structure.
Run this after migrations or before deployment to catch schema drift.
"""
import sys
import psycopg2
from services.walkability import get_db_connection

EXPECTED_COLUMNS = {
    'geoid20': 'character varying',
    'd2a_ranked': 'integer',
    'd2b_ranked': 'integer',
    'd3b_ranked': 'integer',
    'd4a_ranked': 'integer',
    'natwalkind': 'double precision',
    'geometry': 'USER-DEFINED'  # PostGIS geometry type
}

def validate_schema():
    """Check that national_walkability_index table has expected structure."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'national_walkability_index'
            );
        """)
        if not cursor.fetchone()[0]:
            print("❌ ERROR: Table 'national_walkability_index' does not exist")
            return False
        
        # Check columns
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'national_walkability_index'
            ORDER BY column_name;
        """)
        actual_columns = {row[0]: row[1] for row in cursor.fetchall()}
        
        missing_columns = set(EXPECTED_COLUMNS.keys()) - set(actual_columns.keys())
        if missing_columns:
            print(f"❌ ERROR: Missing columns: {missing_columns}")
            return False
        
        # Check spatial index exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_indexes 
                WHERE tablename = 'national_walkability_index' 
                AND indexname = 'geometry_idx'
            );
        """)
        if not cursor.fetchone()[0]:
            print("⚠️  WARNING: Spatial index 'geometry_idx' not found (performance may be slow)")
        
        # Check PostGIS extension
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis');")
        if not cursor.fetchone()[0]:
            print("❌ ERROR: PostGIS extension not enabled")
            return False
        
        print("✅ Schema validation passed")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Schema validation failed: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    success = validate_schema()
    sys.exit(0 if success else 1)
