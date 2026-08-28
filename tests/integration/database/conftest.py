"""
Fixtures for PostgreSQL integration tests.
"""

from collections.abc import Generator
from pathlib import Path

import psycopg
import pytest
from testcontainers.postgres import PostgresContainer

from backend.database.connector import PlaceDBConnector
from backend.database.models import PlaceDBSettings


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer(
        "postgres:16-alpine",
        username="test",
        password="test",
        dbname="test_db",
        driver=None,
    ) as postgres:
        yield postgres


@pytest.fixture(scope="session", autouse=True)
def prepare_database(
    postgres_container: PostgresContainer,
) -> None:
    """Prepare test database schema and data."""

    schema = Path(
        "tests/fixtures/database/schema.sql",
    ).read_text(encoding="utf-8")

    data = Path(
        "tests/fixtures/database/data.sql",
    ).read_text(encoding="utf-8")

    with psycopg.connect(
        host=postgres_container.get_container_host_ip(),
        port=int(postgres_container.get_exposed_port(5432)),
        dbname=postgres_container.dbname,
        user=postgres_container.username,
        password=postgres_container.password,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(schema)
            cursor.execute(data)

        connection.commit()


@pytest.fixture(scope="session")
def db_settings(
    postgres_container: PostgresContainer,
) -> PlaceDBSettings:
    """Create settings for test PostgreSQL."""

    return PlaceDBSettings(
        host=postgres_container.get_container_host_ip(),
        port=int(postgres_container.get_exposed_port(5432)),
        dbname=postgres_container.dbname,
        user=postgres_container.username,
        password=postgres_container.password,
        sql_file_path="sql/example",
        pool_min_size=1,
        pool_max_size=3,
        connect_timeout=10,
        sslmode="disable",
    )


@pytest.fixture(scope="session")
def db_connector(
    db_settings: PlaceDBSettings,
) -> Generator[PlaceDBConnector]:
    """Create PlaceDBConnector connected to test PostgreSQL."""

    connector = PlaceDBConnector(db_settings)

    yield connector

    connector.close()
