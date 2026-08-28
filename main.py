import logging
from pathlib import Path

from backend.api.connector import YandexGeocoderConnector
from backend.api.service import GeocodingService
from backend.database.connector import PlaceDBConnector
from backend.database.models import PlaceDBSettings
from backend.database.service import PlaceService
from backend.etl.service import GeocodingETLService
from backend.geometry.polygon_service import PolygonService
from backend.transformer.service import GeocodingTransformerService
from backend.writer.service import CsvConnector


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format=("%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    setup_logging()
    output_file = Path("data/districts.csv")

    with (
        YandexGeocoderConnector() as geocoder_connector,
        PlaceDBConnector(
            settings=PlaceDBSettings(),
        ) as place_repository,
    ):
        geometry_service = PolygonService()

        geocoding_service = GeocodingService(
            geocoder_connector,
        )

        place_service = PlaceService(
            place_repository,
        )

        transformer = GeocodingTransformerService()

        writer = CsvConnector(
            output_file,
        )

        etl = GeocodingETLService(
            geometry_service=geometry_service,
            place_service=place_service,
            geocoding_service=geocoding_service,
            transformer=transformer,
            writer=writer,
        )

        etl.run_by_coords([37592])


if __name__ == "__main__":
    main()
