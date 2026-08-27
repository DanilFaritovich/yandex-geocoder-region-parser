from pathlib import Path

from backend.api.connector import YandexGeocoderConnector
from backend.api.service import GeocodingService
from backend.database.connector import PlaceDBConnector
from backend.database.models import PlaceDBSettings
from backend.database.service import PlaceService
from backend.etl.coords_service import CoordsETLService
from backend.geometry.polygon_service import PolygonService
from backend.transformer.service import GeocodingTransformerService
from backend.writer.service import CsvConnector


def create_etl_service() -> CoordsETLService:
    geometry_service = PolygonService()

    geocoding_service = GeocodingService(
        YandexGeocoderConnector(),
    )

    place_service = PlaceService(
        PlaceDBConnector(
            settings=PlaceDBSettings(),
        ),
    )

    transformer = GeocodingTransformerService()

    writer = CsvConnector(
        Path("data/districts.csv"),
    )

    return CoordsETLService(
        geometry_service=geometry_service,
        place_service=place_service,
        geocoding_service=geocoding_service,
        transformer=transformer,
        writer=writer,
    )