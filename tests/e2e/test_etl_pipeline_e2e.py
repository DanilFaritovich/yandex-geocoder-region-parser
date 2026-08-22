import csv
from pathlib import Path

from backend.api.models import GeocoderApiResponse
from backend.api.service import GeocodingService
from backend.api.connector import YandexGeocoderConnector
from backend.database.connector import PlaceDBConnector
from backend.database.models import PlaceDBSettings
from backend.database.service import PlaceService
from backend.transformer.service import GeocodingTransformerService
from backend.writer.service import CsvConnector
from backend.etl.service import GeocodingETLService


def test_parse_all_districts_for_locality(tmp_path: Path):
    output_file = tmp_path / "districts.csv"

    with (
        YandexGeocoderConnector() as geocoder_connector,
        PlaceDBConnector(settings=PlaceDBSettings()) as place_repository,
    ):
        geocoding_service = GeocodingService(geocoder_connector)
        place_service = PlaceService(place_repository)
        geocoding_service = GeocodingService(geocoder_connector)
        transformer = GeocodingTransformerService()
        writer = CsvConnector(output_file)

        etl = GeocodingETLService(
            place_service=place_service,
            geocoding_service=geocoding_service,
            transformer=transformer,
            writer=writer,
        )

        etl.run([37592])

    assert output_file.exists()

    with output_file.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file, delimiter=";"))

    assert rows

    # Хотя бы один объект должен содержать район.
    assert any(row["district"] for row in rows)