"""
Database fixtures for integration tests.
Connects to real PostgreSQL database using credentials from .secret/.env
"""
import os
from pathlib import Path
from typing import Generator
from psycopg import sql

import pytest

from backend.database.models import PlaceDBSettings
from backend.database.connector import PlaceDBConnector


@pytest.fixture(scope="session")
def db_settings() -> PlaceDBSettings:
    """Load database settings from secrets file."""
    return PlaceDBSettings()


@pytest.fixture(scope="session")
def db_connector(db_settings: PlaceDBSettings) -> Generator[PlaceDBConnector, None, None]:
    """Create PlaceDBConnector connected to real database."""
    connector = PlaceDBConnector(db_settings)
    yield connector
    connector.close()


@pytest.fixture
def existing_place_ids(db_connector: PlaceDBConnector) -> list[int]:
    """Get list of existing place IDs from database."""
    with db_connector._get_pool().connection() as conn:
        with conn.cursor() as cur:
            query = "\n".join(Path("sql/work/t_place.sql").open("r", encoding="utf-8").readlines()[:-1])
            query = sql.SQL(f"{query} LIMIT 10")
            cur.execute(query)
            rows = cur.fetchall()
            return [row[0] for row in rows]