import logging
from collections.abc import Sequence

from backend.api.models import GeocoderApiResponse, GeoObject
from backend.transformer.models import GeocodeResult


class GeocodingTransformerService:
    """
    Service responsible for transforming Yandex Geocoder API
    response models into business-level geocoding models.
    """

    def __init__(
        self,
        logger: logging.Logger | None = None,
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

        members = response.response.geo_object_collection.feature_member

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

        results = self._deduplicate_by_district(results)

        self._logger.info(
            "Geocoder response transformed: query=%r, results=%d",
            query,
            len(results),
        )

        return results

    def transfrom_districts_by_list(
        self,
        query: str,
        responses: list[GeocoderApiResponse],
    ) -> list[GeocodeResult]:
        """Transform a list of responses."""

        results = [
            result
            for response in responses
            for result in self.transform_districts(
                query=query,
                response=response,
            )
        ]

        return self._deduplicate_by_district(results)

    def _deduplicate_by_district(
        self,
        results: Sequence[GeocodeResult],
    ) -> list[GeocodeResult]:
        unique: dict[str, GeocodeResult] = {}

        for result in results:
            if result.district is None:
                continue

            unique.setdefault(
                result.district,
                result,
            )

        return list(unique.values())

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

        metadata = geo_object.meta_data_property.geocoder_metadata

        address = metadata.address

        components = {
            component.kind: component.name for component in address.components
        }

        latitude: float | None = None
        longitude: float | None = None

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
