import pytest

from backend.api.models import GeocoderApiResponse
from backend.api.connector import YandexGeocoderConnector


@pytest.mark.integration
class TestYandexGeocoderConnector:

    def test_get_districts_returns_api_response(self):
        with YandexGeocoderConnector() as connector:
            response = connector.get_districts(
                query="Dubai",
                results=1,
            )

        assert isinstance(response, GeocoderApiResponse)

        members = (
            response
            .response
            .geo_object_collection
            .feature_member
        )

        assert members

    @pytest.mark.integration
    def test_get_districts_returns_expected_geo_object(self):
        with YandexGeocoderConnector() as connector:
            response = connector.get_districts(
                query="Dubai",
                results=1,
            )

        member = (
            response
            .response
            .geo_object_collection
            .feature_member[0]
        )

        geo_object = member.geo_object

        assert geo_object.meta_data_property.geocoder_metadata.kind
        assert geo_object.meta_data_property.geocoder_metadata.address
        assert geo_object.point.pos

    @pytest.mark.integration
    def test_get_districts_respects_results_parameter(self):
        with YandexGeocoderConnector() as connector:
            response = connector.get_districts(
                query="Dubai",
                results=2,
            )

        members = (
            response
            .response
            .geo_object_collection
            .feature_member
        )

        assert len(members) <= 2