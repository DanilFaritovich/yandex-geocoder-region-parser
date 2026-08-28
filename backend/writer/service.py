import csv
import logging
from collections.abc import Sequence
from pathlib import Path
from types import TracebackType
from typing import Self

from backend.transformer.models import GeocodeResult


class CsvConnector:
    """Connector responsible for writing geocoding results to CSV."""

    def __init__(
        self,
        file_path: Path,
        logger: logging.Logger | None = None,
    ):
        self._file_path = file_path
        self._logger = logger or logging.getLogger(__name__)

    def save(
        self,
        results: Sequence[GeocodeResult],
    ) -> None:
        """Append geocoding results to CSV file."""

        if not results:
            self._logger.debug(
                "No results to save to CSV: path=%s",
                self._file_path,
            )
            return

        self._logger.info(
            "Saving %d geocoding results to CSV: path=%s",
            len(results),
            self._file_path,
        )

        if not self._file_path.parent.exists():
            self._file_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            self._logger.debug(
                "Created output directory: path=%s",
                self._file_path.parent,
            )

        fieldnames = list(GeocodeResult.model_fields.keys())

        file_exists = self._file_path.exists()
        file_empty = not file_exists or self._file_path.stat().st_size == 0

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

                self._logger.debug(
                    "CSV header written: path=%s",
                    self._file_path,
                )

            for result in results:
                writer.writerow(result.model_dump())

        self._logger.info(
            "Successfully saved %d geocoding results: path=%s",
            len(results),
            self._file_path,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass
