"""
Yandex Geocoder API implementation of GeocoderClient.
"""

import logging
import time
from typing import Any, Optional

import requests
from pydantic import ValidationError

from backend.api.client import GeocoderClient
from backend.api.exceptions import (
    YandexGeocoderAPIError,
    YandexGeocoderAuthError,
    YandexGeocoderParseError,
)
from backend.api.models import (
    GeocodeDistrictCoordsRequest,
    GeocodeDistrictQueryRequest,
    GeocodeRequest,
    GeocoderApiResponse,
    GeocoderSettings,
)


class YandexGeocoderConnector(GeocoderClient):
    """
    Yandex Geocoder API client implementing GeocoderClient.

    Responsible for:
    - HTTP requests
    - retries
    - API error handling
    - API response validation

    Does not contain business logic or business models.
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
    ):        
        self.settings = GeocoderSettings()
        self._logger = logger or logging.getLogger(__name__)
        self._session = requests.Session()

        self._logger.debug(
            "Yandex Geocoder connector initialized: "
            "base_url=%s, timeout=%s, retries=%s",
            self.settings.base_url,
            self.settings.timeout,
            self.settings.retries,
        )

    # ------------------------------------------------------------------ #
    # GeocoderClient interface
    # ------------------------------------------------------------------ #

    def get_districts_by_query(
        self,
        query: str,
        results: int = 1,
        skip: int = 0,
    ) -> GeocoderApiResponse:
        """Get districts information by locality name."""

        geocode_request = GeocodeDistrictQueryRequest(
            geocode=query,
            lang=self.settings.lang,
            results=results,
            skip=skip,
        )

        return self._geocode(geocode_request)

    def get_districts_by_coords(
            self,
            longitude: float,
            latitude: float,
            results: int = 1,
            skip: int = 0,
        ) -> GeocoderApiResponse:
            """Get districts information by bbox."""

    
            geocode_request = GeocodeDistrictCoordsRequest(
                lang=self.settings.lang,
                results=results,
                skip=skip,
            )
            geocode_request.coords = (longitude, latitude)
    
            return self._geocode(geocode_request)

    def close(self) -> None:
        """Close HTTP session."""

        self._session.close()

        self._logger.debug(
            "Yandex Geocoder HTTP session closed"
        )

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _geocode(
        self,
        geocode_request: GeocodeRequest,
    ) -> GeocoderApiResponse:
        """Execute geocoding request and parse API response."""

        params = geocode_request.params(
            api_key=self.settings.api_key,
        )

        geocode = self._get_geocode_query(geocode_request)

        raw = self._request(params)

        try:
            response = GeocoderApiResponse.model_validate(raw)
        except ValidationError as exc:
            self._logger.error(
                "Failed to parse Yandex Geocoder response: query=%r",
                geocode,
            )

            raise YandexGeocoderParseError(
                f"Malformed response: {exc}"
            ) from exc

        results_count = len(
            response
            .response
            .geo_object_collection
            .feature_member
        )

        self._logger.debug(
            "Yandex Geocoder response parsed: "
            "query=%r, results=%d",
            geocode,
            results_count,
        )

        return response

    def _get_geocode_query(
        self,
        geocode_request: GeocodeRequest,
    ) -> str:
        """Execute geocoding request and parse API response."""

        if type(geocode_request) is GeocodeDistrictQueryRequest:
            return geocode_request.geocode
        elif type(geocode_request) is GeocodeDistrictCoordsRequest:
            return geocode_request.coords

        raise ValueError(
            f"Unsupported geocode request type: {type(geocode_request)}"
        )

    def _request(self, params: dict[str, Any]) -> dict:
        """Execute HTTP request with retry logic."""

        query = params.get("geocode", "<unknown>")
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.settings.retries + 1):
            self._logger.debug(
                "Sending Yandex Geocoder request: "
                "query=%r, attempt=%d/%d",
                query,
                attempt,
                self.settings.retries,
            )

            try:
                response = self._session.get(
                    self.settings.base_url,
                    params=params,
                    timeout=self.settings.timeout,
                )

                if response.status_code == 403:
                    self._logger.error(
                        "Yandex Geocoder authentication failed: "
                        "query=%r, status=%d",
                        query,
                        response.status_code,
                    )

                    raise YandexGeocoderAuthError(
                        "Invalid API key or limit exceeded"
                    )

                if response.status_code >= 400:
                    self._logger.warning(
                        "Yandex Geocoder API request failed: "
                        "query=%r, status=%d, attempt=%d/%d",
                        query,
                        response.status_code,
                        attempt,
                        self.settings.retries,
                    )

                    raise YandexGeocoderAPIError(
                        f"HTTP {response.status_code}: {response.text}"
                    )

                self._logger.debug(
                    "Yandex Geocoder response received: "
                    "query=%r, status=%d",
                    query,
                    response.status_code,
                )

                return response.json()

            except YandexGeocoderAuthError:
                # Authentication errors are not retryable.
                raise

            except (
                requests.RequestException,
                YandexGeocoderAPIError,
            ) as exc:
                last_exc = exc

                self._logger.warning(
                    "Yandex Geocoder request failed: "
                    "query=%r, attempt=%d/%d, error=%s",
                    query,
                    attempt,
                    self.settings.retries,
                    exc,
                )

                if attempt < self.settings.retries:
                    self._logger.debug(
                        "Retrying Yandex Geocoder request in %.2f seconds",
                        self.settings.retry_delay,
                    )

                    time.sleep(self.settings.retry_delay)

        self._logger.error(
            "Yandex Geocoder request failed after all retries: "
            "query=%r, attempts=%d",
            query,
            self.settings.retries,
        )

        raise YandexGeocoderAPIError(
            f"Failed after {self.settings.retries} attempts"
        ) from last_exc

    # ------------------------------------------------------------------ #
    # Context manager
    # ------------------------------------------------------------------ #

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()