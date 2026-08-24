"""
Abstraction for geocoding clients.
Business logic depends on this interface, not on Yandex implementation.
"""
from abc import ABC, abstractmethod
from typing import Optional

from backend.api.models import GeocoderApiResponse


class GeocoderClient(ABC):
    """
    Abstract geocoding client.
    
    Allows swapping Yandex for Google, Nominatim, or a mock in tests.
    """

    @abstractmethod
    def get_districts_by_query(self, query: str, results: int = 1, skip: int = 0) -> GeocoderApiResponse:
        """Get district info by locality name."""
        ...

    @abstractmethod
    def get_districts_by_coords(self, longitude: float, latitude: float, results: int = 1, skip: int = 0) -> GeocoderApiResponse:
        """Get district info by coords."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Release resources."""
        ...