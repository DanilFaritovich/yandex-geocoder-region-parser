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
        assert place['id'] == place_id
        # Проверим что поля заполнены (не None для обязательных)
        assert 'c_description' in place
        assert 'c_language_code' in place

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
    """Integration tests for PlaceDBConnector.get_by_ids()."""

    def test_returns_multiple_existing_places(
        self,
        db_connector: PlaceDBConnector,
        existing_place_ids: list[int],
    ) -> None:
        """Should return rows for all existing IDs."""
        # Arrange
        test_ids = existing_place_ids[:3]

        # Act
        rows = db_connector.get_by_ids(test_ids)

        # Assert
        assert len(rows) == 3

        returned_ids = {row["id"] for row in rows}
        assert returned_ids == set(test_ids)

    def test_returns_empty_list_for_empty_input(
        self,
        db_connector: PlaceDBConnector,
    ) -> None:
        """Should return an empty list when no IDs are provided."""
        # Act
        rows = db_connector.get_by_ids([])

        # Assert
        assert rows == []
        assert isinstance(rows, list)

    def test_skips_nonexistent_ids(
        self,
        db_connector: PlaceDBConnector,
        existing_place_ids: list[int],
    ) -> None:
        """Should return only existing rows."""
        # Arrange
        existing_id = existing_place_ids[0]
        nonexistent_id = 999999999

        # Act
        rows = db_connector.get_by_ids([existing_id, nonexistent_id])

        # Assert
        assert len(rows) == 1
        assert rows[0]["id"] == existing_id