"""Database connection management module.

This module provides functionality for creating and managing a connection pool
to the database. It implements a singleton pattern for the connection pool
to ensure efficient reuse of database connections across the application.

The module supports both direct PostgreSQL connections and connections via
PgBouncer, based on the application configuration.

Side effects:
    - Creates a connection pool on first access.
    - Maintains open database connections in the pool.
"""

from typing import Optional

from psycopg_pool import ConnectionPool

from settings.config import config

_pool: Optional[ConnectionPool] = None


def get_connection_pool() -> ConnectionPool:
    """Get or create a database connection pool.

    Implements a singleton pattern to ensure only one connection pool
    is created for the application. On first call, initializes the pool
    using configuration settings (either direct PostgreSQL connection or
    via PgBouncer, depending on USE_PGBOUNCER setting).

    Returns:
        ConnectionPool: A reusable pool of database connections.

    Side effects:
        - On first call, creates a connection pool with the specified parameters.
        - Maintains open database connections.
    """
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=config.db_url,
            min_size=2,
            max_size=20,
            open=True
        )
    return _pool