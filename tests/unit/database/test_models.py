"""
Unit tests for database models.
Tests Place, District and model validation.
"""
import pytest
from datetime import datetime
from shapely.geometry import Polygon

from backend.database.models import Place, District
# ====================================================================== #
# District Tests
# ====================================================================== #

class TestDistrictFromDbRow:
    def test_creates_district_from_complete_row(self):
        """Test creating District from complete database row."""
        row = {
            "name": "Tula",
            "polygon": Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        }

        district = District.from_db_row(row)

        assert district.name == "Tula"
        assert district.polygon == Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])

    def test_create_district_from_partial_row(self):
        """Test creating District from row with only required fields."""
        row = {
            "name": "Tula",
            "polygon": None,
        }

        district = District.from_db_row(row)

        assert district.name is "Tula"
        assert district.polygon is None

    def test_ignore_extra_columns(self):
        """Test that extra columns in row are ignored."""
        row = {
            "name": "Tula",
            "extra_column": "should be ignored",
            "another_extra": 123,
        }

        district = District.from_db_row(row)

        assert district.name is "Tula"
        assert not hasattr(district, "extra_column")

    def test_handles_none_values(self):
        """Test that None values are properly handled."""
        row = {
            "name": None,
            "polygon": None,
        }

        district = District.from_db_row(row)

        assert district.name is None
        assert district.polygon is None

# ====================================================================== #
# Place Tests
# ====================================================================== #

class TestPlaceFromDbRow:
    def test_creates_place_from_complete_row(self):
        """Test creating Place from complete database row."""
        row = {
            "id": 42,
            "name": "Tula",
            "polygon": Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        }

        place = Place.from_db_row(row)

        assert place.id == 42
        assert place.name == "Tula"
        assert place.polygon == Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        assert place.districts == []

    def test_creates_place_from_partial_row(self):
        """Test creating Place from row with only required fields."""
        row = {"id": 1, "name": "Moscow"}

        place = Place.from_db_row(row)

        assert place.id == 1
        assert place.name == "Moscow"
        assert place.polygon is None
        assert place.districts == []

    def test_ignores_extra_columns(self):
        """Test that extra columns in row are ignored."""
        row = {
            "id": 1,
            "name": "Tula",
            "extra_column": "should be ignored",
            "another_extra": 123,
        }

        place = Place.from_db_row(row)

        assert place.id == 1
        assert place.name == "Tula"
        assert not hasattr(place, "extra_column")

    def test_handles_none_values(self):
        """Test that None values are properly handled."""
        row = {
            "id": 1,
            "name": None,
            "polygon": None,
        }

        place = Place.from_db_row(row)

        assert place.id == 1
        assert place.name is None
        assert place.polygon is None


class TestPlaceValidation:
    def test_validates_required_fields(self):
        """Test that Place validates required fields."""
        # id is required
        with pytest.raises(Exception):  # pydantic ValidationError
            Place(name="Tula")  # missing id

    def test_accepts_minimal_valid_data(self):
        """Test that Place accepts minimal valid data."""
        place = Place(id=1)
        assert place.id == 1

class TestPlaceAddDistrict:
    """
    Test Place.add_district method.
    """
    def test_adds_district(self, place_factory, district_factory):
        district = district_factory(
            name="Tule district", 
            polygon=Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        )
        place = place_factory(id=1)
        place.add_district(district)
        assert place.districts == [district]

    def test_adds_districts(self, place_factory, district_factory):
        district1 = district_factory(
            name="Tule district 1", 
            polygon=Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        )
        district2 = district_factory(
            name="Tule district 2", 
            polygon=Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        )
        place = place_factory(id=1)
        place.add_district(district1)
        place.add_district(district2)
        assert place.districts == [district1, district2]

    def test_adds_none_district(self, place_factory):
        place = place_factory(id=1)
        with pytest.raises(TypeError):
            place.add_district(None)