"""
Unit tests for database models.

Tests Place, District and model-specific business logic.
"""

import pytest
from pydantic import ValidationError
from shapely.geometry import Polygon

from backend.database.models import District, Place


# ====================================================================== #
# District Tests
# ====================================================================== #


class TestDistrictFromDbRow:

    def test_creates_district_from_complete_row(self):
        row = {
            "name": "Tula",
            "polygon": Polygon([
                (0, 0),
                (1, 0),
                (1, 1),
                (0, 1),
            ]),
        }

        district = District.from_db_row(row)

        assert district.name == "Tula"
        assert district.polygon.equals(
            Polygon([
                (0, 0),
                (1, 0),
                (1, 1),
                (0, 1),
            ])
        )

    def test_creates_district_from_partial_row(self):
        row = {
            "name": "Tula",
            "polygon": None,
        }

        district = District.from_db_row(row)

        assert district.name == "Tula"
        assert district.polygon is None

    def test_ignores_extra_columns(self):
        row = {
            "name": "Tula",
            "extra_column": "ignored",
            "another_extra": 123,
        }

        district = District.from_db_row(row)

        assert district.name == "Tula"
        assert not hasattr(district, "extra_column")
        assert not hasattr(district, "another_extra")

    def test_handles_none_values(self):
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
        row = {
            "id": 42,
            "c_description": "Tula",
            "c_language_code": "ru",
            "c_polygon_text": (
                "POLYGON ((0 0, 1 0, 1 1, 0 0))"
            ),
        }

        place = Place.from_db_row(row)

        assert place.id == 42
        assert place.c_description == "Tula"
        assert place.c_language_code == "ru"

        assert isinstance(place.c_polygon, Polygon)
        assert place.c_polygon.equals(
            Polygon([
                (0, 0),
                (1, 0),
                (1, 1),
                (0, 0),
            ])
        )

        assert place.districts == []

    def test_creates_place_from_partial_row(self):
        row = {
            "id": 1,
            "c_description": "Moscow",
        }

        place = Place.from_db_row(row)

        assert place.id == 1
        assert place.c_description == "Moscow"
        assert place.c_language_code is None
        assert place.c_polygon is None
        assert place.districts == []

    def test_ignores_extra_columns(self):
        row = {
            "id": 1,
            "c_description": "Tula",
            "extra_column": "ignored",
            "another_extra": 123,
        }

        place = Place.from_db_row(row)

        assert place.id == 1
        assert place.c_description == "Tula"
        assert not hasattr(place, "extra_column")
        assert not hasattr(place, "another_extra")

    def test_handles_none_values(self):
        row = {
            "id": 1,
            "c_description": None,
            "c_language_code": None,
            "c_polygon_text": None,
        }

        place = Place.from_db_row(row)

        assert place.id == 1
        assert place.c_description is None
        assert place.c_language_code is None
        assert place.c_polygon is None

    def test_rejects_non_polygon_geometry(self):
        row = {
            "id": 42,
            "c_polygon_text": "POINT (10 20)",
        }

        with pytest.raises(
            ValueError,
            match="Expected Polygon geometry",
        ):
            Place.from_db_row(row)

    def test_requires_id(self):
        row = {
            "c_description": "Tula",
        }

        with pytest.raises(KeyError):
            Place.from_db_row(row)


# ====================================================================== #
# Place Validation Tests
# ====================================================================== #


class TestPlaceValidation:

    def test_requires_id(self):
        with pytest.raises(ValidationError):
            Place(c_description="Tula")

    def test_accepts_minimal_valid_data(self):
        place = Place(id=1)

        assert place.id == 1
        assert place.c_description is None
        assert place.c_language_code is None
        assert place.c_polygon is None
        assert place.districts == []


# ====================================================================== #
# Place.add_district Tests
# ====================================================================== #


class TestPlaceAddDistrict:

    def test_adds_district(self, place_factory, district_factory):
        place = place_factory(id=1)

        district = district_factory(
            name="Tula district",
            polygon=Polygon([
                (0, 0),
                (1, 0),
                (1, 1),
                (0, 1),
            ]),
        )

        place.add_district(district)

        assert place.districts == [district]

    def test_adds_multiple_districts(
        self,
        place_factory,
        district_factory,
    ):
        place = place_factory(id=1)

        district_1 = district_factory(
            name="Tula district 1",
        )
        district_2 = district_factory(
            name="Tula district 2",
        )

        place.add_district(district_1)
        place.add_district(district_2)

        assert place.districts == [
            district_1,
            district_2,
        ]

    def test_rejects_wrong_type(self, place_factory):
        place = place_factory(id=1)

        with pytest.raises(
            TypeError,
            match="district must be of type District",
        ):
            place.add_district(None)

    def test_rejects_duplicate_district_name(
        self,
        place_factory,
        district_factory,
    ):
        place = place_factory(id=1)

        place.add_district(
            district_factory(name="Tula district")
        )

        with pytest.raises(
            ValueError,
            match="District with name Tula district already exists",
        ):
            place.add_district(
                district_factory(name="Tula district")
            )

    def test_allows_multiple_unnamed_districts(
        self,
        place_factory,
        district_factory,
    ):
        place = place_factory(id=1)

        district_1 = district_factory(name=None)
        district_2 = district_factory(name=None)

        place.add_district(district_1)
        place.add_district(district_2)

        assert place.districts == [
            district_1,
            district_2,
        ]