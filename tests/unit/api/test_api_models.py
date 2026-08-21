import json

from backend.api.models import GeocoderApiResponse


class TestGeocoderApiResponse:

    def test_parses_real_yandex_response(self, yandex_geocoder_response):

        response = GeocoderApiResponse.model_validate(yandex_geocoder_response)

        assert response.response.geo_object_collection.feature_member