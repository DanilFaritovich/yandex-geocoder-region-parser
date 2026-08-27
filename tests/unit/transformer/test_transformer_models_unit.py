import pytest

from backend.transformer.models import GeocodeResult


class TestGeocodeResult:

    def test_creates_empty_result(self):
        result = GeocodeResult()

        assert result.coordinates is None

    def test_coordinates_returns_tuple(self):
        result = GeocodeResult(
            latitude=25.1121,
            longitude=55.2006,
        )

        assert result.coordinates == (25.1121, 55.2006)

    @pytest.mark.parametrize(
        ("latitude", "longitude"),
        [
            (None, None),
            (25.1121, None),
            (None, 55.2006),
        ],
    )
    def test_coordinates_returns_none_for_incomplete_coordinates(
        self,
        latitude,
        longitude,
    ):
        result = GeocodeResult(
            latitude=latitude,
            longitude=longitude,
        )

        assert result.coordinates is None