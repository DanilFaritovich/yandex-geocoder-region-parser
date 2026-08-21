import logging
from typing import Optional

from backend.api.models import GeoObject, GeocoderApiResponse
from backend.transformer.models import GeocodeResult


class GeocodingTransformerService:
    """
    Service responsible for transforming Yandex Geocoder API
    response models into business-level geocoding models.
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize transformer service with an optional logger."""

        self._logger = logger or logging.getLogger(__name__)

    def transform_districts(
        self,
        query: str,
        response: GeocoderApiResponse,
    ) -> list[GeocodeResult]:
        """
        Transform all geo objects from an API response.

        Converts Yandex-specific API models into GeocodeResult
        business models that can be used by downstream ETL steps.
        """

        members = (
            response
            .response
            .geo_object_collection
            .feature_member
        )

        self._logger.debug(
            "Transforming geocoder response: query=%r, objects=%d",
            query,
            len(members),
        )

        results = [
            self._transform_geo_object(
                query=query,
                geo_object=member.geo_object,
            )
            for member in members
        ]

        self._logger.info(
            "Geocoder response transformed: query=%r, results=%d",
            query,
            len(results),
        )

        return results

    @staticmethod
    def _transform_geo_object(
        query: str,
        geo_object: GeoObject,
    ) -> GeocodeResult:
        """
        Transform a single API GeoObject into a GeocodeResult.

        Extracts address components and geographic coordinates
        from the Yandex-specific response structure.
        """

        metadata = (
            geo_object
            .meta_data_property
            .geocoder_metadata
        )

        address = metadata.address

        components = {
            component.kind: component.name
            for component in address.components
        }

        latitude: Optional[float] = None
        longitude: Optional[float] = None

        try:
            longitude_str, latitude_str = geo_object.point.pos.split()

            longitude = float(longitude_str)
            latitude = float(latitude_str)

        except (ValueError, IndexError):
            # Invalid coordinates should not prevent transformation
            # of the remaining address data.
            pass

        return GeocodeResult(
            geocode=query,
            kind=metadata.kind,
            text=metadata.text,
            precision=metadata.precision,
            formatted=address.formatted,
            country_code=address.country_code,
            district=components.get("district"),
            area=components.get("area"),
            locality=components.get("locality"),
            province=components.get("province"),
            country=components.get("country"),
            latitude=latitude,
            longitude=longitude,
        )