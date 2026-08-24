import pytest
from shapely.geometry import Point, Polygon

from backend.geometry.polygon_service import PolygonService


@pytest.fixture
def polygon_service() -> PolygonService:
    """Create polygon service."""
    return PolygonService()


@pytest.fixture
def square_polygon() -> Polygon:
    """Create test square polygon."""
    return Polygon(
        [
            (44.50, 40.15),
            (44.51, 40.15),
            (44.51, 40.16),
            (44.50, 40.16),
            (44.50, 40.15),
        ]
    )


class TestPolygonService:
    """Tests for PolygonService."""

    def test_returns_points_for_polygon(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
    ):
        """Test that polygon is converted into points."""
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
        """Test that generated points belong to polygon."""
        points = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=50,
        )

        assert points

        for point in points:
            assert square_polygon.covers(point)

    def test_points_are_not_outside_polygon(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
    ):
        """Test that no generated point is outside polygon."""
        points = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=50,
        )

        for point in points:
            assert not point.disjoint(square_polygon)

    def test_empty_polygon_raises_value_error(
        self,
        polygon_service: PolygonService,
    ):
        """Test that empty polygon raises ValueError."""
        polygon = Polygon()

        with pytest.raises(
            ValueError,
            match="Polygon must not be empty",
        ):
            polygon_service.polygon_to_points(
                polygon,
                distance_meters=50,
            )

    def test_invalid_distance_raises_error(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
    ):
        """Test that invalid distance is rejected."""
        with pytest.raises(ValueError):
            polygon_service.polygon_to_points(
                square_polygon,
                distance_meters=0,
            )

    @pytest.mark.parametrize(
        "distance",
        [-1, 0],
    )
    def test_non_positive_distance_raises_error(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
        distance: float,
    ):
        """Test that distance must be positive."""
        with pytest.raises(ValueError):
            polygon_service.polygon_to_points(
                square_polygon,
                distance_meters=distance,
            )

    def test_smaller_distance_produces_more_points(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
    ):
        """Test that smaller distance produces more points."""
        points_50 = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=50,
        )

        points_100 = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=100,
        )

        assert len(points_50) > len(points_100)

    def test_larger_distance_produces_fewer_points(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
    ):
        """Test that larger distance produces fewer points."""
        points_50 = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=50,
        )

        points_500 = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=500,
        )

        assert len(points_50) >= len(points_500)

    def test_points_have_valid_coordinates(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
    ):
        """Test generated point coordinates."""
        points = polygon_service.polygon_to_points(
            square_polygon,
            distance_meters=50,
        )

        for point in points:
            assert -180 <= point.x <= 180
            assert -90 <= point.y <= 90

    def test_different_distances_are_supported(
        self,
        polygon_service: PolygonService,
        square_polygon: Polygon,
    ):
        """Test different sampling distances."""
        for distance in (10, 25, 50, 100, 500):
            points = polygon_service.polygon_to_points(
                square_polygon,
                distance_meters=distance,
            )

            assert isinstance(points, list)
            assert all(isinstance(point, Point) for point in points)