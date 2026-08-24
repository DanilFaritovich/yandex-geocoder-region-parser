from unittest.mock import Mock

import pytest

from backend.api.models import GeocoderApiResponse
from backend.api.service import GeocodingService


class TestGeocodingService:

    @pytest.fixture
    def client(self):
        return Mock()

    @pytest.fixture
    def service(self, client):
        return GeocodingService(client=client)

    def test_get_district_by_locality(
        self,
        service,
        client,
    ):
        response = Mock(spec=GeocoderApiResponse)
        client.get_districts_by_query.return_value = response

        result = service.get_district_by_locality("Dubai")

        assert result is response
        client.get_districts_by_query.assert_called_once_with(
            query="Dubai",
            results=1,
            skip=0,
        )

    def test_get_districts_by_locality(
        self,
        service,
        client,
    ):
        response = Mock(spec=GeocoderApiResponse)
        client.get_districts_by_query.return_value = response

        result = service.get_districts_by_locality(
            "Dubai",
            results=10,
            skip=5,
        )

        assert result is response
        client.get_districts_by_query.assert_called_once_with(
            query="Dubai",
            results=10,
            skip=5,
        )

    def test_get_district_by_coords(
        self,
        service,
        client,
    ):
        response = Mock(spec=GeocoderApiResponse)
        client.get_districts_by_coords.return_value = response

        result = service.get_district_by_coords(17.12441, 52.2345)

        assert result is response
        client.get_districts_by_coords.assert_called_once_with(
            longitude=17.12441,
            latitude=52.2345,
            results=1,
            skip=0,
        )

    def test_get_districts_by_coords(
        self,
        service,
        client,
    ):
        response = Mock(spec=GeocoderApiResponse)
        client.get_districts_by_coords.return_value = response

        result = service.get_districts_by_coords(
            longitude=17.12441, 
            latitude=52.2345,
            results=10,
            skip=5,
        )

        assert result is response
        client.get_districts_by_coords.assert_called_once_with(
            longitude=17.12441, 
            latitude=52.2345,
            results=10,
            skip=5,
        )

    def test_close(
        self,
        service,
        client,
    ):
        service.close()

        client.close.assert_called_once_with()