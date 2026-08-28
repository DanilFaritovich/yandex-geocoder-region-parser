import logging

from backend.api.client import GeocoderClient
from backend.api.models import GeocoderApiResponse


class GeocodingService:
    """
    Application service for geocoding operations.

    Depends on the GeocoderClient abstraction, allowing different
    geocoding providers to be used without changing consumers.
    """

    def __init__(
        self,
        client: GeocoderClient,
        logger: logging.Logger | None = None,
    ):
        self._client = client
        self._logger = logger or logging.getLogger(__name__)

    # ================================================================
    # Get district info by locality
    # ================================================================

    def get_district_by_locality(
        self,
        locality: str,
    ) -> GeocoderApiResponse:
        """Get geocoding data for a locality."""

        return self.get_districts_by_locality(
            locality=locality,
            results=1,
        )

    def get_districts_by_locality(
        self,
        locality: str,
        results: int = 10,
        skip: int = 0,
    ) -> GeocoderApiResponse:
        """Get geocoding data for a locality with pagination."""

        self._logger.debug(
            "Requesting districts: locality=%r, results=%d, skip=%d",
            locality,
            results,
            skip,
        )

        response = self._client.get_districts_by_query(
            query=locality,
            results=results,
            skip=skip,
        )

        self._logger.info(
            "District data received: locality=%r",
            locality,
        )

        return response

    # ================================================================
    # Get district info by coords
    # ================================================================

    def get_district_by_coords(
        self, longitude: float, latitude: float
    ) -> GeocoderApiResponse:
        """Get geocoding data for a coords."""

        return self.get_districts_by_coords(
            longitude,
            latitude,
            results=1,
        )

    def get_districts_by_coords(
        self,
        longitude: float,
        latitude: float,
        results: int = 10,
        skip: int = 0,
    ) -> GeocoderApiResponse:
        """Get geocoding data for a coords with pagination."""

        self._logger.debug(
            "Requesting districts: longitude=%r, latidude=%r, results=%d, skip=%d",
            longitude,
            latitude,
            results,
            skip,
        )

        response = self._client.get_districts_by_coords(
            longitude=longitude,
            latitude=latitude,
            results=results,
            skip=skip,
        )

        self._logger.info(
            "District data received: longitude=%r, latidude=%r",
            longitude,
            latitude,
        )

        return response

    def close(self) -> None:
        """Close the underlying geocoder client."""

        self._client.close()

    def __enter__(self) -> GeocodingService:
        return self

    def __exit__(self) -> None:
        self.close()
