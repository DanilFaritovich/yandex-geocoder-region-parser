"""
Business logic layer. Depends on PlaceRepository abstraction,
NOT on concrete connector.
"""
import logging
from typing import Optional, List, Dict

from backend.database.models import Place
from backend.database.repository import PlaceRepository
from backend.database.exceptions import (
    PlaceNotFoundError,
    PlaceValidationError,
)

class PlaceService:
    """
    Business service for place data operations.
    
    Depends on PlaceRepository (abstraction), not on PlaceDBConnector.
    This makes the service:
    - Testable (inject a mock repository)
    - Portable (swap PostgreSQL for any other implementation)
    """

    MAX_BATCH_SIZE = 1000

    def __init__(
        self,
        repository: PlaceRepository,
        enable_cache: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Args:
            repository: any implementation of PlaceRepository
            enable_cache: enable in-memory caching
            logger: Logger instance
        """
        self._repository = repository
        self._cache: Dict[int, Place] = {}
        self._enable_cache = enable_cache
        self._logger = logger or logging.getLogger(__name__)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def get_place_by_id(self, place_id: int) -> Place:
        """Get place by ID."""
        self._validate_place_id(place_id)

        # Check cache
        if self._enable_cache and place_id in self._cache:
            return self._cache[place_id]

        # Call repository (abstraction)
        place = self._repository.get_by_id(place_id)

        if place is None:
            raise PlaceNotFoundError(f"Place with id={place_id} not found")

        # Cache
        if self._enable_cache:
            self._cache[place_id] = place

        return place

    def get_places_by_ids(self, place_ids: List[int]) -> Dict[int, Place]:
        """Get multiple places by IDs."""
        self._validate_batch_ids(place_ids)
        if not place_ids:
            return {}

        result: Dict[int, Place] = {}
        ids_to_fetch: List[int] = []

        for pid in place_ids:
            if self._enable_cache and pid in self._cache:
                result[pid] = self._cache[pid]
            else:
                ids_to_fetch.append(pid)

        if ids_to_fetch:
            fetched = self._repository.get_by_ids(ids_to_fetch)
            result.update(fetched)

            if self._enable_cache:
                self._cache.update(fetched)

            missing = set(ids_to_fetch) - set(fetched.keys())
            if missing:
                self._logger.warning("Places not found: %s", sorted(missing))

        return result

    def clear_cache(self) -> None:
        self._cache.clear()

    # ------------------------------------------------------------------ #
    # Validation
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate_place_id(place_id: int) -> None:
        if not isinstance(place_id, int):
            raise PlaceValidationError(f"place_id must be int, got {type(place_id).__name__}")
        if place_id <= 0:
            raise PlaceValidationError(f"place_id must be positive, got {place_id}")

    def _validate_batch_ids(self, place_ids: List[int]) -> None:
        if not isinstance(place_ids, list):
            raise PlaceValidationError("place_ids must be a list")
        if len(place_ids) > self.MAX_BATCH_SIZE:
            raise PlaceValidationError(f"Batch too large: {len(place_ids)}")
        for pid in place_ids:
            self._validate_place_id(pid)

    # ------------------------------------------------------------------ #
    # Context manager
    # ------------------------------------------------------------------ #

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._repository.close()