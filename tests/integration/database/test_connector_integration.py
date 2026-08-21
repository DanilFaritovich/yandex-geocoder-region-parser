"""
Integration tests for PlaceDBConnector with real PostgreSQL database.
Tests read existing data from database.

Run with: pytest tests/integration/database -v
"""
import pytest

from backend.database.connector import PlaceDBConnector


@pytest.mark.integration
class TestGetById:
    """Tests for get_by_id method."""

    def test_returns_existing_place(
        self,
        db_connector: PlaceDBConnector,
        existing_place_ids: list[int],
    ):
        """Test that get_by_id returns existing place correctly."""
        # Arrange
        assert len(existing_place_ids) > 0, "Database has no places to test"
        place_id = existing_place_ids[0]

        # Act
        place = db_connector.get_by_id(place_id)

        # Assert
        assert place is not None
        assert place.id == place_id
        # Проверим что поля заполнены (не None для обязательных)
        assert hasattr(place, 'c_description')
        assert hasattr(place, 'c_language_code')

    def test_returns_none_for_nonexistent_id(
        self,
        db_connector: PlaceDBConnector,
    ):
        """Test that get_by_id returns None for non-existent ID."""
        # Act
        place = db_connector.get_by_id(999999999)

        # Assert
        assert place is None


@pytest.mark.integration
class TestGetByIds:
    """Tests for get_by_ids method."""

    def test_returns_multiple_existing_places(
        self,
        db_connector: PlaceDBConnector,
        existing_place_ids: list[int],
    ):
        """Test that get_by_ids returns multiple existing places."""
        # Arrange
        assert len(existing_place_ids) >= 3, "Need at least 3 places for this test"
        test_ids = existing_place_ids[:3]

        # Act
        places = db_connector.get_by_ids(test_ids)

        # Assert
        assert len(places) == 3
        for place_id in test_ids:
            assert place_id in places
            assert places[place_id].id == place_id

    def test_returns_empty_dict_for_empty_list(
        self,
        db_connector: PlaceDBConnector,
    ):
        """Test that get_by_ids returns empty dict for empty input."""
        # Act
        places = db_connector.get_by_ids([])

        # Assert
        assert places == {}
        assert isinstance(places, dict)

    def test_skips_nonexistent_ids(
        self,
        db_connector: PlaceDBConnector,
        existing_place_ids: list[int],
    ):
        """Test that get_by_ids skips non-existent IDs."""
        # Arrange
        assert len(existing_place_ids) > 0
        existing_id = existing_place_ids[0]
        nonexistent_id = 999999999

        # Act
        places = db_connector.get_by_ids([existing_id, nonexistent_id])

        # Assert
        assert len(places) == 1
        assert existing_id in places
        assert nonexistent_id not in places