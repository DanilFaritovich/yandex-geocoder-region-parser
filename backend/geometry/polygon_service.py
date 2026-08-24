from math import ceil
from typing import Iterable

from pyproj import Transformer
from shapely.geometry import Point, Polygon
from shapely.ops import transform


class PolygonService:
    """Service for generating points inside geographic polygons."""

    def polygon_to_points(
        self,
        polygon: Polygon,
        distance_meters: float = 50,
    ) -> list[Point]:
        """
        Generate points inside a polygon with a given distance between them.

        The input polygon must use WGS84 coordinates:
            longitude, latitude

        Args:
            polygon: Polygon in WGS84 coordinates.
            distance_meters: Distance between generated points in meters.

        Returns:
            List of points in WGS84 coordinates.

        Raises:
            ValueError: If distance is not positive or polygon is empty.
        """
        if distance_meters <= 0:
            raise ValueError(
                "distance_meters must be greater than zero"
            )

        if polygon.is_empty:
            raise ValueError("Polygon must not be empty")

        if not polygon.is_valid:
            raise ValueError("Polygon must be valid")

        metric_polygon = self._to_metric(polygon)

        points = self._generate_points(
            metric_polygon,
            distance_meters,
        )

        return [
            self._from_metric(point)
            for point in points
        ]

    def _generate_points(
        self,
        polygon: Polygon,
        distance_meters: float,
    ) -> list[Point]:
        """Generate a regular grid of points inside a metric polygon."""
        min_x, min_y, max_x, max_y = polygon.bounds

        columns = ceil((max_x - min_x) / distance_meters)
        rows = ceil((max_y - min_y) / distance_meters)

        points: list[Point] = []

        for row in range(rows + 1):
            y = min_y + row * distance_meters

            for column in range(columns + 1):
                x = min_x + column * distance_meters

                point = Point(x, y)

                if polygon.contains(point):
                    points.append(point)

        return points

    @staticmethod
    def _to_metric(polygon: Polygon) -> Polygon:
        """Transform WGS84 polygon to a metric coordinate system."""
        transformer = Transformer.from_crs(
            "EPSG:4326",
            "EPSG:3857",
            always_xy=True,
        )

        return transform(
            transformer.transform,
            polygon,
        )

    @staticmethod
    def _from_metric(point: Point) -> Point:
        """Transform a metric point back to WGS84."""
        transformer = Transformer.from_crs(
            "EPSG:3857",
            "EPSG:4326",
            always_xy=True,
        )

        return transform(
            transformer.transform,
            point,
        )