"""
PostgreSQL implementation of PlaceRepository.

Handles:
- PostgreSQL connection pooling
- SQL execution
- database error handling
- query performance logging

Does NOT contain business logic.
"""

import logging
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, LiteralString, Optional

from psycopg import DatabaseError, OperationalError, ProgrammingError, sql
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from backend.database.exceptions import (
    PlaceConnectionError,
    PlaceQueryError,
)
from backend.database.models import PlaceDBSettings
from backend.database.repository import PlaceRepository


class PlaceDBConnector(PlaceRepository):
    """
    PostgreSQL implementation of PlaceRepository.

    Responsibilities:
    - manage PostgreSQL connection pool
    - execute SQL queries
    - map database errors to application exceptions
    - log database-related technical events

    Business logic must stay in PlaceService.
    """

    def __init__(
        self,
        settings: Optional[PlaceDBSettings] = None,
        logger: Optional[logging.Logger] = None,
    ):
        if settings is None:
            raise ValueError("'settings' is required")

        self.settings = settings
        self._logger = logger or logging.getLogger(__name__)
        self._pool: Optional[ConnectionPool] = None

        self._init_pool()

    # ------------------------------------------------------------------ #
    # PlaceRepository interface
    # ------------------------------------------------------------------ #

    def get_by_id(self, place_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a single place by ID.

        Returns:
            Place if found, otherwise None.
        """
        rows = self.get_by_ids([place_id])
        if rows:
            return rows[0]
        return 

    def get_by_ids(self, place_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Fetch multiple places by IDs.

        Returns:
            Mapping of place ID to Place.
        """
        if not place_ids:
            return []

        placeholders = sql.SQL(", ").join(
            sql.Placeholder() for _ in place_ids
        )

        query = sql.SQL(
            self._get_sql("t_place.sql")
        ).format(
            placeholders,
        )

        rows = self._fetch_all(
            query,
            tuple(place_ids),
        )

        return rows

    def close(self) -> None:
        """Close PostgreSQL connection pool."""
        if self._pool is None:
            return

        self._pool.close()
        self._pool = None

        self._logger.debug("PostgreSQL connection pool closed")

    # ------------------------------------------------------------------ #
    # Private methods
    # ------------------------------------------------------------------ #

    def _get_sql(self, file_name: str) -> str:
        return Path(
            self.settings.sql_file_path,
            file_name,
        ).read_text(encoding="utf-8")

    # ------------------------------------------------------------------ #
    # Connection pool
    # ------------------------------------------------------------------ #

    def _init_pool(self) -> None:
        """Initialize PostgreSQL connection pool."""
        self._logger.debug(
            "Initializing PostgreSQL connection pool "
            "(min_size=%d, max_size=%d)",
            self.settings.pool_min_size,
            self.settings.pool_max_size,
        )

        try:
            self._pool = ConnectionPool(
                conninfo=self.settings.conninfo,
                min_size=self.settings.pool_min_size,
                max_size=self.settings.pool_max_size,
                open=True,
            )
        except OperationalError as exc:
            self._logger.exception(
                "Failed to initialize PostgreSQL connection pool"
            )

            raise PlaceConnectionError(
                "Cannot connect to database"
            ) from exc

    def _get_pool(self) -> ConnectionPool:
        """Return active connection pool."""
        if self._pool is None:
            raise PlaceConnectionError(
                "Connection pool is closed"
            )

        return self._pool

    # ------------------------------------------------------------------ #
    # SQL execution
    # ------------------------------------------------------------------ #

    def _execute(
        self,
        query: sql.Composed,
        params: tuple[Any, ...],
        fetcher: Callable[[Any], Any],
    ) -> Any:
        """
        Execute SQL query and process cursor with fetcher.

        Logs query execution time at DEBUG level.

        Converts psycopg exceptions into application-specific exceptions.
        """
        pool = self._get_pool()
        started_at = time.perf_counter()

        try:
            with pool.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(query, params)
                    result = fetcher(cur)

            elapsed_ms = (time.perf_counter() - started_at) * 1000

            self._logger.debug(
                "Database query completed in %.2f ms",
                elapsed_ms,
            )

            return result

        except OperationalError as exc:
            elapsed_ms = (time.perf_counter() - started_at) * 1000

            self._logger.exception(
                "Database connection error after %.2f ms",
                elapsed_ms,
            )

            raise PlaceConnectionError(
                "Database connection error"
            ) from exc

        except (ProgrammingError, DatabaseError) as exc:
            elapsed_ms = (time.perf_counter() - started_at) * 1000

            self._logger.exception(
                "Database query failed after %.2f ms",
                elapsed_ms,
            )

            raise PlaceQueryError(
                "Database query error"
            ) from exc

    def _fetch_one(
        self,
        query: sql.Composed,
        params: tuple[Any, ...],
    ) -> Optional[Dict[str, Any]]:
        """Execute query and return a single row."""
        return self._execute(
            query,
            params,
            fetcher=lambda cursor: cursor.fetchone(),
        )

    def _fetch_all(
        self,
        query: sql.Composed,
        params: tuple[Any, ...],
    ) -> List[Dict[str, Any]]:
        """Execute query and return all rows."""
        return self._execute(
            query,
            params,
            fetcher=lambda cursor: cursor.fetchall(),
        )

    # ------------------------------------------------------------------ #
    # Context manager
    # ------------------------------------------------------------------ #

    def __enter__(self) -> "PlaceDBConnector":
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        self.close()