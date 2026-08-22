"""
Business logic layer.

Depends on PlaceRepository abstraction,
NOT on concrete database connector.
"""

import logging
from typing import Dict, List, Optional

from backend.database.exceptions import (
    PlaceNotFoundError,
    PlaceValidationError,
)
from backend.database.models import Place
from backend.database.repository import PlaceRepository


class PlaceService:
    """
    Business service for place data operations.

    Depends on PlaceRepository (abstraction), not on PlaceDBConnector.

    Responsibilities:
    - validate input
    - apply business rules
    - handle business-level errors
    - log business events

    Does NOT contain database-specific logic.
    """

    MAX_BATCH_SIZE = 1000

    def __init__(
        self,
        repository: PlaceRepository,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Args:
            repository: Repository implementation.
            logger: Optional logger instance.
        """
        self._repository = repository
        self._logger = logger or logging.getLogger(__name__)

        self._logger.debug("PlaceService initialized")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def get_place_by_id(self, place_id: int) -> Place:
        """
        Get a place by ID.

        Raises:
            PlaceValidationError: If place_id is invalid.
            PlaceNotFoundError: If place does not exist.
        """
        self._validate_place_id(place_id)

        self._logger.debug(
            "Fetching place: place_id=%d",
            place_id,
        )

        row = self._repository.get_by_id(place_id)
        if row is None:
            self._logger.warning(
                "Place not found: place_id=%d",
                place_id,
            )

            raise PlaceNotFoundError(
                f"Place with id={place_id} not found"
            )

        place = Place.from_db_row(row)

        self._logger.debug(
            "Place loaded: place_id=%d",
            place_id,
        )

        return place

    def get_places_by_ids(
        self,
        place_ids: List[int],
    ) -> Dict[int, Place]:
        """
        Get multiple places by IDs.

        Missing places are not considered an error.
        They are logged as warnings and omitted from the result.

        Raises:
            PlaceValidationError: If input is invalid.
        """
        self._validate_batch_ids(place_ids)

        if not place_ids:
            self._logger.debug(
                "Empty place ID batch requested"
            )
            return {}

        self._logger.debug(
            "Fetching places: requested=%d",
            len(place_ids),
        )

        rows = self._repository.get_by_ids(place_ids)

        places = {
            row["id"]: Place.from_db_row(row)
            for row in rows
        }

        missing = set(place_ids) - set(places.keys())

        if missing:
            self._logger.warning(
                "Places not found: requested=%d, found=%d, missing=%d",
                len(place_ids),
                len(places),
                len(missing),
            )

        self._logger.debug(
            "Places loaded: requested=%d, returned=%d",
            len(place_ids),
            len(places),
        )

        return places

    def close(self) -> None:
        """Close the underlying client."""
        self._repository.close()

    # ------------------------------------------------------------------ #
    # Validation
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate_place_id(place_id: int) -> None:
        """
        Validate a single place ID.

        Raises:
            PlaceValidationError: If ID is invalid.
        """
        if isinstance(place_id, bool) or not isinstance(place_id, int):
            raise PlaceValidationError(
                f"place_id must be int, got {type(place_id).__name__}"
            )

        if place_id <= 0:
            raise PlaceValidationError(
                f"place_id must be positive, got {place_id}"
            )

    def _validate_batch_ids(
        self,
        place_ids: List[int],
    ) -> None:
        """
        Validate a batch of place IDs.

        Raises:
            PlaceValidationError: If batch is invalid.
        """
        if not isinstance(place_ids, list):
            raise PlaceValidationError(
                "place_ids must be a list"
            )

        if len(place_ids) > self.MAX_BATCH_SIZE:
            raise PlaceValidationError(
                f"Batch too large: {len(place_ids)}"
            )

        for place_id in place_ids:
            self._validate_place_id(place_id)

    # ------------------------------------------------------------------ #
    # Context manager
    # ------------------------------------------------------------------ #

    def __enter__(self) -> "PlaceService":
        return self

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ) -> None:
        self._repository.close()