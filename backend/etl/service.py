from collections.abc import Sequence
import logging
from typing import Optional, Union

from shapely import Polygon

from backend.api.models import GeocoderApiResponse
from backend.api.service import GeocodingService
from backend.database.service import PlaceService
from backend.transformer.models import GeocodeResult
from backend.transformer.service import GeocodingTransformerService
from backend.writer.service import CsvConnector
from backend.geometry.polygon_service import PolygonService


class GeocodingETLService:
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

    def run_by_query(
        self,
        localities: Sequence[Union[int, str]],
    ) -> None:
        """Parse all districts for each locality by query."""

        for locality in localities:
            if isinstance(locality, int):
                locality = self._place_service.get_place_by_id(locality).c_description
                if locality is None:
                    self._logger.error("No locality found: id_place=%d", locality)
                    raise ValueError
            self._process_locality_by_query(locality)

    def _process_locality_by_query(self, locality: str) -> None:
        """Parse all districts for a single locality by query."""

        skip = 0
        ret_results: list[GeocodeResult] = []

        while True:
            self._logger.debug(
                "Requesting districts: locality=%r, results=%d, skip=%d",
                locality,
                self.BATCH_SIZE,
                skip,
            )

            response = self._geocoding_service.get_districts_by_locality(
                locality=locality,
                results=self.BATCH_SIZE,
                skip=skip,
            )

            results = self._transformer.transform_districts(
                query=locality,
                response=response,
            )

            if len(results) - skip < self.BATCH_SIZE:
                self._logger.debug(
                    "No more districts found: locality=%r, skip=%d",
                    locality,
                    skip,
                )
                self._writer.save(results)
                break
            else:
                ret_results.extend(results)

            skip += self.BATCH_SIZE