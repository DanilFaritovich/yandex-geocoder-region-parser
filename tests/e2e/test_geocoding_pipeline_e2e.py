import csv
from pathlib import Path

from backend.api.connector import YandexGeocoderConnector
from backend.api.service import GeocodingService
from backend.transformer.service import GeocodingTransformerService
from backend.writer.service import CsvConnector


class TestGeocodingE2E:

    def test_parse_district_and_save_to_csv(
        self,
        tmp_path: Path,
    ):
        output_file = tmp_path / "results.csv"

        query = "Dakar, Région Dakar, город"

        with YandexGeocoderConnector() as connector:
            geocoding_service = GeocodingService(
                client=connector,
            )

            transformer = GeocodingTransformerService()

            with CsvConnector(output_file) as writer:
                response = geocoding_service.get_districts_by_locality(
                    locality=query,
                )

                results = transformer.transform_districts(
                    query=query,
                    response=response,
                )

                writer.save(results)

        assert output_file.exists()

        with output_file.open(
            newline="",
            encoding="utf-8",
        ) as file:
            rows = list(csv.DictReader(file, delimiter=";"))

        for row in rows:
            print(row)

        assert len(rows) >= 1
        assert rows[0]["geocode"] == query
        assert any(row["district"] for row in rows)
        assert rows[0]["latitude"]
        assert rows[0]["longitude"]