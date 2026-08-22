from pathlib import Path

from backend.api.connector import YandexGeocoderConnector
from backend.api.service import GeocodingService
from backend.database.connector import PlaceDBConnector
from backend.database.models import PlaceDBSettings
from backend.database.service import PlaceService
from backend.etl.service import GeocodingETLService
from backend.transformer.service import GeocodingTransformerService
from backend.writer.service import CsvConnector


def main() -> None:
    output_file = Path("data/districts.csv")

    with (
        YandexGeocoderConnector() as geocoder_connector,
        PlaceDBConnector(
            settings=PlaceDBSettings(),
        ) as place_repository,
    ):
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
            place_service=place_service,
            geocoding_service=geocoding_service,
            transformer=transformer,
            writer=writer,
        )

        etl.run(["-17.361791,14.772221"])


if __name__ == "__main__":
    main()