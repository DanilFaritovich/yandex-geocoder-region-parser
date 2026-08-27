import csv

from backend.transformer.models import GeocodeResult
from backend.writer.service import CsvConnector


class TestCsvConnector:

    def test_save_writes_results_to_csv(
        self,
        geocode_result,
        tmp_path,
    ):
        file_path = tmp_path / "results.csv"
        connector = CsvConnector(file_path)

        connector.save([geocode_result])

        with file_path.open(
            newline="",
            encoding="utf-8",
        ) as file:
            rows = list(csv.DictReader(file, delimiter=";"))

        assert len(rows) == 1

        row = rows[0]

        assert row["geocode"] == geocode_result.geocode
        assert row["district"] == geocode_result.district
        assert row["country"] == geocode_result.country
        assert row["country_code"] == geocode_result.country_code
        assert row["formatted"] == geocode_result.formatted
        assert row["latitude"] == str(geocode_result.latitude)
        assert row["longitude"] == str(geocode_result.longitude)

    def test_save_writes_expected_header(
        self,
        geocode_result,
        tmp_path,
    ):
        file_path = tmp_path / "results.csv"
        connector = CsvConnector(file_path)

        connector.save([geocode_result])

        with file_path.open(
            newline="",
            encoding="utf-8",
        ) as file:
            reader = csv.reader(file, delimiter=";")
            header = next(reader)

        assert header == list(GeocodeResult.model_fields.keys())

    def test_save_writes_multiple_results(
        self,
        geocode_result,
        tmp_path,
    ):
        second_result = geocode_result.model_copy(
            update={"geocode": "Yerevan"},
        )

        file_path = tmp_path / "results.csv"
        connector = CsvConnector(file_path)

        connector.save([
            geocode_result,
            second_result,
        ])

        with file_path.open(
            newline="",
            encoding="utf-8",
        ) as file:
            rows = list(csv.DictReader(file, delimiter=";"))

        assert len(rows) == 2
        assert rows[0]["geocode"] == geocode_result.geocode
        assert rows[1]["geocode"] == "Yerevan"

    def test_save_appends_results_to_existing_csv(
        self,
        geocode_result,
        tmp_path,
    ):
        second_result = geocode_result.model_copy(
            update={"geocode": "Yerevan"},
        )

        file_path = tmp_path / "results.csv"
        connector = CsvConnector(file_path)

        connector.save([geocode_result])
        connector.save([second_result])

        with file_path.open(
            newline="",
            encoding="utf-8",
        ) as file:
            rows = list(csv.DictReader(file, delimiter=";"))

        assert len(rows) == 2
        assert rows[0]["geocode"] == geocode_result.geocode
        assert rows[1]["geocode"] == "Yerevan"

    def test_save_writes_header_to_existing_empty_file(
        self,
        geocode_result,
        tmp_path,
    ):
        file_path = tmp_path / "results.csv"
        file_path.touch()

        connector = CsvConnector(file_path)

        connector.save([geocode_result])

        with file_path.open(
            newline="",
            encoding="utf-8",
        ) as file:
            rows = list(csv.DictReader(file, delimiter=";"))

        assert len(rows) == 1
        assert rows[0]["geocode"] == geocode_result.geocode

    def test_save_creates_parent_directory(
        self,
        geocode_result,
        tmp_path,
    ):
        file_path = tmp_path / "output" / "results.csv"
        connector = CsvConnector(file_path)

        connector.save([geocode_result])

        assert file_path.exists()
        assert file_path.is_file()

    def test_save_does_nothing_for_empty_results(
        self,
        tmp_path,
    ):
        file_path = tmp_path / "results.csv"
        connector = CsvConnector(file_path)

        connector.save([])

        assert not file_path.exists()

    def test_save_writes_none_values_as_empty_fields(
        self,
        tmp_path,
    ):
        result = GeocodeResult(
            geocode="Yerevan",
            district=None,
            area=None,
            locality=None,
            province=None,
            country="Armenia",
            country_code="AM",
            formatted="Yerevan, Armenia",
            kind="locality",
            text="Yerevan",
            latitude=None,
            longitude=None,
            precision=None,
        )

        file_path = tmp_path / "results.csv"
        connector = CsvConnector(file_path)

        connector.save([result])

        with file_path.open(
            newline="",
            encoding="utf-8",
        ) as file:
            rows = list(csv.DictReader(file, delimiter=";"))

        assert rows[0]["geocode"] == "Yerevan"
        assert rows[0]["country"] == "Armenia"
        assert rows[0]["latitude"] == ""
        assert rows[0]["longitude"] == ""

    def test_context_manager(
        self,
        geocode_result,
        tmp_path,
    ):
        file_path = tmp_path / "results.csv"

        with CsvConnector(file_path) as connector:
            connector.save([geocode_result])

        assert file_path.exists()