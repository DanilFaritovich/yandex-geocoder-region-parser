import pytest

from backend.api.models import GeocoderApiResponse
from backend.transformer.models import GeocodeResult
from backend.transformer.service import GeocodingTransformerService


class TestGeocodingTransformerService:
    """Unit tests for GeocodingTransformerService."""

    def test_transform_districts_returns_geocode_results(
        self,
        yandex_geocoder_response: GeocoderApiResponse,
    ):
        service = GeocodingTransformerService()

        response = GeocoderApiResponse.model_validate(yandex_geocoder_response)

        result = service.transform_districts(
            query="Dubai",
            response=response,
        )

        assert len(result) == 1
        assert isinstance(result[0], GeocodeResult)

    def test_transform_districts_maps_address_data(
        self,
        yandex_geocoder_response: GeocoderApiResponse,
    ):
        service = GeocodingTransformerService()

        response = GeocoderApiResponse.model_validate(yandex_geocoder_response)

        result = service.transform_districts(
            query="Dubai",
            response=response,
        )

        geocode = result[0]

        assert geocode.geocode == "Dubai"
        assert geocode.formatted is not None
        assert geocode.country is not None
        assert geocode.country_code is not None
        assert geocode.latitude is not None
        assert geocode.longitude is not None

    def test_transform_districts_maps_coordinates(
        self,
        yandex_geocoder_response: GeocoderApiResponse,
    ):
        service = GeocodingTransformerService()

        response = GeocoderApiResponse.model_validate(yandex_geocoder_response)

        result = service.transform_districts(
            query="Dubai",
            response=response,
        )

        geocode = result[0]

        assert isinstance(geocode.latitude, float)
        assert isinstance(geocode.longitude, float)

    def test_transform_districts_returns_empty_list_for_empty_response(
        self,
        yandex_geocoder_response: GeocoderApiResponse,
    ):
        service = GeocodingTransformerService()

        response = GeocoderApiResponse.model_validate(yandex_geocoder_response)
        response = response.model_copy(deep=True)
        response.response.geo_object_collection.feature_member = []

        result = service.transform_districts(
            query="Dubai",
            response=response,
        )

        assert result == []