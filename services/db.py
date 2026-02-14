"""
Framework-agnostic database connection factory.

Reads PostgreSQL credentials from environment variables (PGHOST, PGPORT,
PGDATABASE, PGUSER, PGPASSWORD). No Streamlit, Flask, or other framework
imports.
"""
import os
import psycopg2

REQUIRED_PG_VARS = ['PGDATABASE', 'PGHOST', 'PGPASSWORD', 'PGPORT', 'PGUSER']


def validate_pg_env():
    """Return a sorted list of missing PG* environment variable names.

    Returns an empty list when all required vars are present.
    """
    return sorted(v for v in REQUIRED_PG_VARS if not os.environ.get(v))


def get_pg_env():
    """Read and validate PG* environment variables.

    Returns:
        dict with keys: host, port (int), database, user, password.

    Raises:
        EnvironmentError: if any required PG* vars are missing.
        ValueError: if PGPORT is not a valid integer.
    """
    missing = validate_pg_env()
    if missing:
        raise EnvironmentError(
            f"Missing required database environment variables: {', '.join(missing)}. "
            "Set PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD."
        )

    raw_port = os.environ['PGPORT']
    try:
        port = int(raw_port)
    except (ValueError, TypeError):
        raise ValueError(f"PGPORT must be an integer, got '{raw_port}'")

    return {
        'host': os.environ['PGHOST'],
        'port': port,
        'database': os.environ['PGDATABASE'],
        'user': os.environ['PGUSER'],
        'password': os.environ['PGPASSWORD'],
    }


def get_db_connection():
    """Create a PostgreSQL connection using environment variables.

    Returns:
        psycopg2 connection object.

    Raises:
        EnvironmentError: if required env vars are missing.
        ValueError: if PGPORT is not a valid integer.
        psycopg2.OperationalError: if the connection attempt fails.
    """
    env = get_pg_env()
    return psycopg2.connect(
        host=env['host'],
        port=env['port'],
        database=env['database'],
        user=env['user'],
        password=env['password'],
    )


def is_connection_closed(conn):
    """Check if a database connection is closed or broken.

    psycopg2 semantics: conn.closed is 0 when open, nonzero when the
    connection is closed or broken (e.g. server dropped it).  This
    function also handles None connections, missing ``closed`` attribute
    (e.g. Streamlit SQL wrappers), and boolean mocks.
    """
    if conn is None:
        return True
    closed_value = getattr(conn, "closed", 0)
    if isinstance(closed_value, bool):
        return closed_value
    if isinstance(closed_value, int):
        return closed_value != 0
    return False
