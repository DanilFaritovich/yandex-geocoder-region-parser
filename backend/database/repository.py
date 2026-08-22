"""
Repository abstraction for Place data access.
Defines the contract that business logic depends on.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from backend.database.models import Place


class PlaceRepository(ABC):
    """
    Abstract interface for place data access.
    
    Business logic (PlaceService) depends on this abstraction,
    NOT on the concrete connector. This allows:
    - Swapping implementations (PostgreSQL -> MongoDB -> API)
    - Easy mocking in unit tests
    - Decoupling business rules from infrastructure details
    """

    @abstractmethod
    def get_by_id(self, place_id: int) -> Optional[Dict[str, Any]]:
        """Fetch single place by ID. Returns None if not found."""
        ...

    @abstractmethod
    def get_by_ids(self, place_ids: List[int]) -> List[Dict[str, Any]]:
        """Fetch multiple places by IDs. Returns {id: Place}."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Release resources."""
        ...