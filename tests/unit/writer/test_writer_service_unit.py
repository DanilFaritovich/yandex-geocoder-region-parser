import csv

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
        assert rows[0]["geocode"] == geocode_result.geocode
        assert rows[0]["district"] == geocode_result.district
        assert rows[0]["latitude"] == str(geocode_result.latitude)
        assert rows[0]["longitude"] == str(geocode_result.longitude)

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

    def test_save_creates_parent_directory(
        self,
        geocode_result,
        tmp_path,
    ):
        file_path = tmp_path / "output" / "results.csv"
        connector = CsvConnector(file_path)

        connector.save([geocode_result])

        assert file_path.exists()

    def test_save_does_nothing_for_empty_results(
        self,
        tmp_path,
    ):
        file_path = tmp_path / "results.csv"
        connector = CsvConnector(file_path)

        connector.save([])

        assert not file_path.exists()