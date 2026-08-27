"""
Integration tests for PlaceDBConnector.

Tests run against an isolated PostgreSQL container.
"""

import pytest

from backend.database.connector import PlaceDBConnector


@pytest.mark.integration
class TestGetById:
    """Integration tests for PlaceDBConnector.get_by_id()."""

    def test_returns_existing_place(
        self,
        db_connector: PlaceDBConnector,
    ):
        """Return an existing place by ID."""
        place = db_connector.get_by_id(1)

        assert place is not None
        assert place.id == 1
        assert place.c_description == "Yerevan"
        assert place.c_language_code == "hy"

    def test_returns_none_for_nonexistent_id(
        self,
        db_connector: PlaceDBConnector,
    ):
        """Return None when place does not exist."""
        place = db_connector.get_by_id(999999)

        assert place is None


@pytest.mark.integration
class TestGetByIds:
    """Integration tests for PlaceDBConnector.get_by_ids()."""

    def test_returns_multiple_places(
        self,
        db_connector: PlaceDBConnector,
    ):
        """Return all existing places for requested IDs."""
        places = db_connector.get_by_ids([1, 2, 3])

        assert len(places) == 3

        assert {place.id for place in places} == {
            1,
            2,
            3,
        }

    def test_returns_empty_list_for_empty_input(
        self,
        db_connector: PlaceDBConnector,
    ):
        """Return empty list for empty ID list."""
        places = db_connector.get_by_ids([])

        assert places == []

    def test_skips_nonexistent_ids(
        self,
        db_connector: PlaceDBConnector,
    ):
        """Return only existing places."""
        places = db_connector.get_by_ids([1, 999999])

        assert len(places) == 1
        assert places[0].id == 1

    def test_returns_places_in_requested_set(
        self,
        db_connector: PlaceDBConnector,
    ):
        """Return only places matching requested IDs."""
        places = db_connector.get_by_ids([1, 3])

        assert {place.id for place in places} == {
            1,
            3,
        }