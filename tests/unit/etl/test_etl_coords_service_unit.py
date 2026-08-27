from unittest.mock import Mock

import pytest
from shapely.geometry import Point, Polygon

from backend.etl.coords_service import CoordsETLService
from backend.transformer.models import GeocodeResult


@pytest.fixture
def geometry_service():
    return Mock()


@pytest.fixture
def place_service():
    return Mock()


@pytest.fixture
def geocoding_service():
    return Mock()


@pytest.fixture
def transformer():
    return Mock()


@pytest.fixture
def writer():
    return Mock()


@pytest.fixture
def service(
    geometry_service,
    place_service,
    geocoding_service,
    transformer,
    writer,
):
    return CoordsETLService(
        geometry_service=geometry_service,
        place_service=place_service,
        geocoding_service=geocoding_service,
        transformer=transformer,
        writer=writer,
    )


@pytest.fixture
def polygon():
    return Polygon([
        (44.50, 40.15),
        (44.51, 40.15),
        (44.51, 40.16),
        (44.50, 40.16),
    ])


class TestCoordsETLServiceGetPlacePolygon:

    def test_returns_place_polygon(
        self,
        service,
        place_service,
        polygon,
    ):
        place = Mock()
        place.c_polygon = polygon
        place_service.get_place_by_id.return_value = place

        result = service.get_place_polygon(42)

        assert result == polygon

        place_service.get_place_by_id.assert_called_once_with(42)

    def test_raises_when_polygon_is_missing(
        self,
        service,
        place_service,
    ):
        place = Mock()
        place.c_polygon = None
        place_service.get_place_by_id.return_value = place

        with pytest.raises(
            ValueError,
            match="Polygon not found for place_id=42",
        ):
            service.get_place_polygon(42)

        place_service.get_place_by_id.assert_called_once_with(42)


class TestCoordsETLServiceGeneratePoints:

    def test_generates_point_data(
        self,
        service,
        geometry_service,
        polygon,
    ):
        geometry_service.polygon_to_points.return_value = [
            Point(44.50, 40.15),
            Point(44.51, 40.16),
        ]

        result = service.generate_points(
            place_id=42,
            polygon=polygon,
            distance_meters=100,
        )

        assert result == [
            {
                "place_id": 42,
                "longitude": 44.50,
                "latitude": 40.15,
            },
            {
                "place_id": 42,
                "longitude": 44.51,
                "latitude": 40.16,
            },
        ]

        geometry_service.polygon_to_points.assert_called_once_with(
            polygon,
            distance_meters=100,
        )

    def test_returns_empty_list_when_no_points_generated(
        self,
        service,
        geometry_service,
        polygon,
    ):
        geometry_service.polygon_to_points.return_value = []

        result = service.generate_points(
            place_id=42,
            polygon=polygon,
            distance_meters=100,
        )

        assert result == []


class TestCoordsETLServiceProcessPoint:

    def test_processes_point(
        self,
        service,
        geocoding_service,
        transformer,
    ):
        response = Mock()
        expected_result = [
            Mock(spec=GeocodeResult),
        ]

        geocoding_service.get_districts_by_coords.return_value = response
        transformer.transform_districts.return_value = expected_result

        result = service.process_point(
            place_id=42,
            longitude=44.50,
            latitude=40.15,
        )

        assert result == expected_result

        geocoding_service.get_districts_by_coords.assert_called_once_with(
            longitude=44.50,
            latitude=40.15,
            results=service.BATCH_SIZE,
        )

        transformer.transform_districts.assert_called_once_with(
            query="42",
            response=response,
        )

    def test_returns_empty_result(
        self,
        service,
        geocoding_service,
        transformer,
    ):
        response = Mock()

        geocoding_service.get_districts_by_coords.return_value = response
        transformer.transform_districts.return_value = []

        result = service.process_point(
            place_id=42,
            longitude=44.50,
            latitude=40.15,
        )

        assert result == []


class TestCoordsETLServiceSave:

    def test_saves_results(
        self,
        service,
        writer,
    ):
        results = [
            Mock(spec=GeocodeResult),
            Mock(spec=GeocodeResult),
        ]

        service.save(results)

        writer.save.assert_called_once_with(results)

    def test_saves_empty_results(
        self,
        service,
        writer,
    ):
        service.save([])

        writer.save.assert_called_once_with([])