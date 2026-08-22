import csv
from pathlib import Path
from typing import Sequence

from backend.transformer.models import GeocodeResult


class CsvConnector:
    """Connector responsible for writing geocoding results to CSV."""

    def __init__(self, file_path: Path):
        self._file_path = file_path

    def save(
        self,
        results: Sequence[GeocodeResult],
    ) -> None:
        """Append geocoding results to CSV file."""

        if not results:
            return

        self._file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fieldnames = list(
            GeocodeResult.model_fields.keys()
        )

        file_exists = self._file_path.exists()
        file_empty = (
            not file_exists
            or self._file_path.stat().st_size == 0
        )

        with self._file_path.open(
            "a",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                delimiter=";",
            )

            if file_empty:
                writer.writeheader()

            for result in results:
                writer.writerow(
                    result.model_dump()
                )

    def __enter__(self) -> "CsvConnector":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass