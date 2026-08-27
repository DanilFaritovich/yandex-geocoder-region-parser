from collections.abc import Sequence
import logging
from typing import List, Optional, Union

from shapely import Polygon

from backend.api.models import GeocoderApiResponse
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

    def get_place_polygon(self, place_id: int):
        place = self._place_service.get_place_by_id(place_id)
        polygon = place.c_polygon
        if polygon is None:
            self._logger.error("No locality found: id_place=%d", place_id)
            raise ValueError
        return polygon

    def generate_points(self, place_id, polygon: Polygon, distance_meters: int) -> List[PointData]:

        coords = self._geometry_service.polygon_to_points(polygon, distance_meters=distance_meters)
        
        self._logger.info(
            "Processing locality: locality=%r, coords=%d",
            polygon,
            len(coords),
        )

        return [
            {
                "place_id": place_id,
                "longitude": point.x,
                "latitude": point.y
            }
            for point in coords
        ]

    def process_point(
        self,
        place_id: int,
        longitude: float,
        latitude: float
    ) -> List[GeocodeResult]:
        """Geocode a single polygon point."""

        response = self._geocoding_service.get_districts_by_coords(
            longitude=longitude,
            latitude=latitude,
            results=self.BATCH_SIZE,
        )

        result = self._transformer.transform_districts(
            query=str(place_id),
            response=response,
        )

        return result

    def save(self, results: Sequence[GeocodeResult]):
        self._writer.save(results)