import pytest
from pydantic import ValidationError

from backend.api.models import (
    GeocodeDistrictCoordsRequest,
    GeocodeDistrictQueryRequest,
    GeocoderApiResponse,
)


class TestGeocoderApiResponse:
    def test_parses_real_yandex_response(
        self,
        yandex_geocoder_response,
    ):
        response = GeocoderApiResponse.model_validate(yandex_geocoder_response)

        collection = response.response.geo_object_collection

        assert collection.feature_member

    def test_parses_geocoder_metadata(
        self,
        yandex_geocoder_response,
    ):
        response = GeocoderApiResponse.model_validate(yandex_geocoder_response)

        metadata = (
            response.response.geo_object_collection.meta_data_property.geocoder_response
        )

        assert metadata.request
        assert metadata.found
        assert metadata.results

    def test_parses_geo_object(
        self,
        yandex_geocoder_response,
    ):
        response = GeocoderApiResponse.model_validate(yandex_geocoder_response)

        geo_object = response.response.geo_object_collection.feature_member[
            0
        ].geo_object

        assert geo_object.point.pos

        assert geo_object.meta_data_property.geocoder_metadata.kind

    def test_parses_address_components(
        self,
        yandex_geocoder_response,
    ):
        response = GeocoderApiResponse.model_validate(yandex_geocoder_response)

        address = response.response.geo_object_collection.feature_member[
            0
        ].geo_object.meta_data_property.geocoder_metadata.address

        assert address.country_code
        assert address.formatted
        assert address.components

        for component in address.components:
            assert component.kind
            assert component.name

    def test_rejects_invalid_response(self):
        with pytest.raises(ValidationError):
            GeocoderApiResponse.model_validate({})


class TestGeocodeDistrictQueryRequest:
    def test_builds_params(self):
        request = GeocodeDistrictQueryRequest(
            geocode="Москва, Тверской район",
        )

        params = request.params("test-api-key")

        assert params == {
            "apikey": "test-api-key",
            "lang": "ru_RU",
            "format": "json",
            "results": 1,
            "skip": 0,
            "kind": "district",
            "geocode": "Москва, Тверской район",
        }

    def test_builds_params_with_custom_values(self):
        request = GeocodeDistrictQueryRequest(
            geocode="Москва",
            lang="en_RU",
            results=5,
            skip=2,
        )

        params = request.params("test-api-key")

        assert params["apikey"] == "test-api-key"
        assert params["lang"] == "en_RU"
        assert params["results"] == 5
        assert params["skip"] == 2
        assert params["kind"] == "district"
        assert params["geocode"] == "Москва"

    def test_rejects_empty_geocode(self):
        with pytest.raises(ValidationError):
            GeocodeDistrictQueryRequest(
                geocode="",
            )


class TestGeocodeDistrictCoordsRequest:
    def test_coords_setter_formats_coordinates(self):
        request = GeocodeDistrictCoordsRequest()

        request.coords = (37.6176, 55.7558)

        assert request.coords == "37.6176,55.7558"
        assert request.geocode == "37.6176,55.7558"

    def test_coords_are_used_in_params(self):
        request = GeocodeDistrictCoordsRequest()

        request.coords = (37.6176, 55.7558)

        params = request.params("test-api-key")

        assert params["apikey"] == "test-api-key"
        assert params["kind"] == "district"
        assert params["geocode"] == "37.6176,55.7558"

    @pytest.mark.parametrize(
        "coords",
        [
            (0.0, 0.0),
            (-17.440357471588047, 14.688329205319283),
            (37.6176, 55.7558),
        ],
    )
    def test_coords_formats_different_coordinates(
        self,
        coords,
    ):
        request = GeocodeDistrictCoordsRequest()

        request.coords = coords

        longitude, latitude = coords

        assert request.coords == (f"{longitude},{latitude}")
