from contextlib import contextmanager
from typing import Generator, Optional

from psycopg_pool import ConnectionPool

from .settings import settings

pool: Optional[ConnectionPool] = None


def init_pool() -> None:
    """Initialise the global connection pool if not already opened."""
    global pool
    if pool is None:
        pool = ConnectionPool(settings.database_url, open=True)
    elif pool.closed:
        pool.open()


def close_pool() -> None:
    """Close the pool on application shutdown."""
    global pool
    if pool and not pool.closed:
        pool.close()


@contextmanager
def get_connection():
    """Context manager yielding a pooled connection."""
    if pool is None or pool.closed:
        init_pool()
    assert pool is not None  # for type checkers
    with pool.connection() as conn:
        yield conn


def connection_dependency() -> Generator:
    """FastAPI dependency for a database connection."""
    with get_connection() as conn:
        yield conn


def signal_exists(
    conn,
    *,
    source_id: int,
    evidence_url: str | None,
    title: str | None,
    signal_time: str | None,
    org_name: str | None,
    signal_type: str | None = None,
) -> bool:
    """
    Check if a signal already exists with the given uniqueness criteria.
    Null-safe comparison for org_name and optional signal_type.
    """
    sql = """
        SELECT 1
        FROM signals
        WHERE source_id = %s
          AND coalesce(evidence_url, '') = coalesce(%s, '')
          AND coalesce(title, '') = coalesce(%s, '')
          AND coalesce(signal_time::text, '') = coalesce(%s, '')
          AND coalesce(org_name, '') = coalesce(%s, '')
    """
    params = [source_id, evidence_url, title, signal_time, org_name]
    if signal_type is not None:
        sql += " AND coalesce(signal_type, '') = coalesce(%s, '')"
        params.append(signal_type)
    sql += " LIMIT 1;"
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() is not None
