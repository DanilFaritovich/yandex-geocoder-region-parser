import json

from backend.api.models import GeocoderApiResponse


class TestGeocoderApiResponse:

    def test_parses_real_yandex_response(self):
        with open("tests/fixtures/yandex_geocoder_response.json") as f:
            data = json.load(f)

        response = GeocoderApiResponse.model_validate(data)

        assert response.response.geo_object_collection.feature_member