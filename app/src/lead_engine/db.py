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
