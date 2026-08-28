import pytest
from shapely.geometry import Point, Polygon

from backend.geometry.polygon_service import PolygonService


class TestPolygonService:
    """Unit tests for PolygonService."""

    @pytest.fixture
    def polygon_service(self) -> PolygonService:
        return PolygonService()

    @pytest.fixture
    def square_polygon(self) -> Polygon:
        return Polygon(
            [
                (44.50, 40.15),
                (44.51, 40.15),
                (44.51, 40.16),
                (44.50, 40.16),
                (44.50, 40.15),
            ]
        )

    def test_returns_points_for_polygon(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
    ):
        points = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=50,
        )

        assert points
        assert all(isinstance(point, Point) for point in points)

    def test_all_points_are_inside_polygon(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
    ):
        points = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=50,
        )

        assert points
        assert all(square_polygon.covers(point) for point in points)

    def test_generated_points_have_valid_coordinates(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
    ):
        points = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=50,
        )

        for point in points:
            assert -180 <= point.x <= 180
            assert -90 <= point.y <= 90

    def test_empty_polygon_raises_value_error(
        self,
        polygon_service: PolygonService,
    ):
        with pytest.raises(
            ValueError,
            match="Polygon must not be empty",
        ):
            polygon_service.polygon_to_points(
                Polygon(),
                distance_meters=50,
            )

    @pytest.mark.parametrize(
        "distance",
        [-100, -1, 0],
    )
    def test_non_positive_distance_raises_value_error(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
        distance: int,
    ):
        with pytest.raises(ValueError):
            polygon_service.polygon_to_points(
                square_polygon,
                distance_meters=distance,
            )

    @pytest.mark.parametrize(
        "distance",
        ["50", None, [], object()],
    )
    def test_invalid_distance_type_raises_error(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
        distance,
    ):
        with pytest.raises((TypeError, ValueError)):
            polygon_service.polygon_to_points(
                square_polygon,
                distance_meters=distance,
            )

    def test_smaller_distance_produces_more_points(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
    ):
        points_50 = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=50,
        )

        points_100 = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=100,
        )

        assert len(points_50) > len(points_100)

    def test_large_distance_returns_valid_result(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
    ):
        points = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=10_000,
        )

        assert isinstance(points, list)
        assert all(isinstance(point, Point) for point in points)
        assert all(square_polygon.covers(point) for point in points)

    def test_same_input_produces_same_number_of_points(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
    ):
        points_first = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=50,
        )

        points_second = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=50,
        )

        assert len(points_first) == len(points_second)

    @pytest.mark.parametrize(
        "distance",
        [10, 25, 50, 100, 500],
    )
    def test_supported_distances(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
        distance: int,
    ):
        points = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=distance,
        )

        assert isinstance(points, list)
        assert all(isinstance(point, Point) for point in points)
        assert all(square_polygon.covers(point) for point in points)
