from collections.abc import Sequence
import logging
from typing import Optional

from shapely import Polygon

from backend.api.service import GeocodingService
from backend.database.service import PlaceService
from backend.etl.models import PointData
from backend.transformer.models import GeocodeResult
from backend.transformer.service import GeocodingTransformerService
from backend.writer.service import CsvConnector
from backend.geometry.polygon_service import PolygonService


class CoordsETLService:
    """Orchestrates the geocoding ETL pipeline."""

    BATCH_SIZE = 50

    def __init__(
        self,
        geometry_service: PolygonService,
        place_service: PlaceService,
        geocoding_service: GeocodingService,
        transformer: GeocodingTransformerService,
        writer: CsvConnector,
        logger: Optional[logging.Logger] = None,
    ):
        self._geometry_service = geometry_service
        self._place_service = place_service
        self._geocoding_service = geocoding_service
        self._transformer = transformer
        self._writer = writer
        self._logger = logger or logging.getLogger(__name__)

    def get_place_polygon(self, place_id: int) -> Polygon:
        self._logger.info(
            "Getting polygon for place: place_id=%d",
            place_id,
        )

        place = self._place_service.get_place_by_id(place_id)

        polygon = place.c_polygon

        if polygon is None:
            self._logger.error(
                "Polygon not found for place: place_id=%d",
                place_id,
            )
            raise ValueError(
                f"Polygon not found for place_id={place_id}"
            )

        self._logger.info(
            "Polygon received: place_id=%d, geometry_type=%s",
            place_id,
            polygon.geom_type,
        )

        return polygon

    def generate_points(
        self,
        place_id: int,
        polygon: Polygon,
        distance_meters: int,
    ) -> list[PointData]:
        self._logger.info(
            "Generating points: place_id=%d, distance_meters=%d",
            place_id,
            distance_meters,
        )

        coords = self._geometry_service.polygon_to_points(
            polygon,
            distance_meters=distance_meters,
        )

        self._logger.info(
            "Points generated: place_id=%d, points=%d",
            place_id,
            len(coords),
        )

        return [
            {
                "place_id": place_id,
                "longitude": point.x,
                "latitude": point.y,
            }
            for point in coords
        ]

    def process_point(
        self,
        place_id: int,
        longitude: float,
        latitude: float,
    ) -> list[GeocodeResult]:
        """Geocode a single polygon point."""

        self._logger.info(
            "Processing point: place_id=%d, longitude=%f, latitude=%f",
            place_id,
            longitude,
            latitude,
        )

        response = self._geocoding_service.get_districts_by_coords(
            longitude=longitude,
            latitude=latitude,
            results=self.BATCH_SIZE,
        )

        self._logger.debug(
            "Geocoder response received: place_id=%d, longitude=%f, "
            "latitude=%f, response_type=%s",
            place_id,
            longitude,
            latitude,
            type(response).__name__,
        )

        result = self._transformer.transform_districts(
            query=str(place_id),
            response=response,
        )

        self._logger.info(
            "Point processed: place_id=%d, longitude=%f, "
            "latitude=%f, results=%d",
            place_id,
            longitude,
            latitude,
            len(result),
        )

        return result

    def save(self, results: Sequence[GeocodeResult]) -> None:
        self._logger.info(
            "Saving geocoding results: results=%d",
            len(results),
        )

        self._writer.save(results)

        self._logger.info(
            "Geocoding results saved: results=%d",
            len(results),
        )