import pytest

from backend.api.models import GeocoderApiResponse
from backend.api.connector import YandexGeocoderConnector


@pytest.mark.integration
class TestYandexGeocoderQueryConnector:

    def test_get_districts_returns_api_response(self):
        with YandexGeocoderConnector() as connector:
            response = connector.get_districts_by_query(
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
            response = connector.get_districts_by_query(
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
            response = connector.get_districts_by_query(
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

@pytest.mark.integration
class TestYandexGeocoderCoordsConnector:

    def test_get_districts_by_coords_returns_api_response(self):
        """Should return a valid response for geographic coordinates."""
        with YandexGeocoderConnector() as connector:
            response = connector.get_districts_by_coords(
                longitude=55.2708,
                latitude=25.2048,  # Dubai
                results=1,
            )

        assert isinstance(response, GeocoderApiResponse)

        members = (
            response
            .response
            .geo_object_collection
            .feature_member
        )

        assert len(members) == 1

    def test_get_districts_by_coords_returns_geo_object(self):
        """Should return geo object with metadata and coordinates."""
        with YandexGeocoderConnector() as connector:
            response = connector.get_districts_by_coords(
                longitude=55.2708,
                latitude=25.2048,
                results=1,
            )

        geo_object = (
            response
            .response
            .geo_object_collection
            .feature_member[0]
            .geo_object
        )

        metadata = geo_object.meta_data_property.geocoder_metadata

        assert metadata.kind
        assert metadata.address.formatted
        assert geo_object.point.pos

    def test_get_districts_by_coords_respects_results_parameter(self):
        """Should not return more objects than requested."""
        with YandexGeocoderConnector() as connector:
            response = connector.get_districts_by_coords(
                longitude=55.2708,
                latitude=25.2048,
                results=2,
            )

        members = (
            response
            .response
            .geo_object_collection
            .feature_member
        )

        assert len(members) <= 2

    def test_get_districts_by_query_respects_skip_parameter(self):
        """Should return another page when skip is used."""
        with YandexGeocoderConnector() as connector:
            first = connector.get_districts_by_query(
                query="Dubai",
                results=1,
                skip=0,
            )

            second = connector.get_districts_by_query(
                query="Dubai",
                results=1,
                skip=1,
            )

        first_text = (
            first.response
            .geo_object_collection
            .feature_member[0]
            .geo_object
            .meta_data_property
            .geocoder_metadata
            .text
        )

        second_text = (
            second.response
            .geo_object_collection
            .feature_member[0]
            .geo_object
            .meta_data_property
            .geocoder_metadata
            .text
        )

        assert first_text != second_text