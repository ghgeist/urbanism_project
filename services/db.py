"""
Framework-agnostic database connection factory.

Reads PostgreSQL credentials from either:
- DATABASE_URL (single connection string), or
- PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD.

Provides both raw connections (get_db_connection) and a process-level
connection pool (get_pool / get_pooled_connection) to avoid per-request
TCP handshake overhead on cloud-hosted Postgres.

No framework imports.
"""
import logging
import os
import threading

import psycopg2
from psycopg2 import pool as _pg_pool

REQUIRED_PG_VARS = ['PGDATABASE', 'PGHOST', 'PGPASSWORD', 'PGPORT', 'PGUSER']

_pool: _pg_pool.ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()

logger = logging.getLogger(__name__)


def _has_database_url():
    """True if DATABASE_URL is set and non-empty."""
    return bool(os.environ.get('DATABASE_URL', '').strip())


def validate_pg_env():
    """Return a sorted list of missing PG* environment variable names.

    Returns an empty list when all required vars are present, or when
    DATABASE_URL is set (in which case PG* are not required).
    """
    if _has_database_url():
        return []
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

    Uses DATABASE_URL if set; otherwise requires PGHOST, PGPORT, PGDATABASE,
    PGUSER, PGPASSWORD.

    Returns:
        psycopg2 connection object.

    Raises:
        EnvironmentError: if required env vars are missing.
        ValueError: if PGPORT is not a valid integer.
        psycopg2.OperationalError: if the connection attempt fails.
    """
    if _has_database_url():
        return psycopg2.connect(os.environ['DATABASE_URL'].strip())
    env = get_pg_env()
    return psycopg2.connect(
        host=env['host'],
        port=env['port'],
        database=env['database'],
        user=env['user'],
        password=env['password'],
    )


# ---------------------------------------------------------------------------
# Connection pool
# ---------------------------------------------------------------------------

def get_pool(minconn: int = 1, maxconn: int = 5) -> _pg_pool.ThreadedConnectionPool:
    """Return the process-level connection pool, creating it on first call.

    Thread-safe: uses a lock so concurrent callers don't create duplicate pools.
    The pool is backed by the same env-var logic as get_db_connection().
    """
    global _pool
    if _pool is not None and not _pool.closed:
        return _pool

    with _pool_lock:
        # Double-check after acquiring lock.
        if _pool is not None and not _pool.closed:
            return _pool

        if _has_database_url():
            _pool = _pg_pool.ThreadedConnectionPool(
                minconn, maxconn, dsn=os.environ['DATABASE_URL'].strip()
            )
        else:
            env = get_pg_env()
            _pool = _pg_pool.ThreadedConnectionPool(
                minconn,
                maxconn,
                host=env['host'],
                port=env['port'],
                database=env['database'],
                user=env['user'],
                password=env['password'],
            )
        logger.info("DB connection pool created (min=%d, max=%d)", minconn, maxconn)
        return _pool


def get_pooled_connection():
    """Get a connection from the pool.

    Caller MUST return it via return_connection() when done.
    """
    return get_pool().getconn()


def return_connection(conn):
    """Return a connection to the pool (or close it if the pool is gone)."""
    if _pool is not None and not _pool.closed:
        _pool.putconn(conn)
    elif conn and not is_connection_closed(conn):
        conn.close()


def close_pool():
    """Shut down the connection pool. Called during app shutdown."""
    global _pool
    if _pool is not None and not _pool.closed:
        _pool.closeall()
        logger.info("DB connection pool closed")
    _pool = None


def is_connection_closed(conn):
    """Check if a database connection is closed or broken.

    psycopg2 semantics: conn.closed is 0 when open, nonzero when the
    connection is closed or broken (e.g. server dropped it).  This
    function also handles None connections, missing ``closed`` attribute
    (e.g. ORM wrappers), and boolean mocks.
    """
    if conn is None:
        return True
    closed_value = getattr(conn, "closed", 0)
    if isinstance(closed_value, bool):
        return closed_value
    if isinstance(closed_value, int):
        return closed_value != 0
    return False
