from unittest.mock import Mock

import pytest

from backend.api.client import GeocoderClient
from backend.api.models import GeocoderApiResponse
from backend.api.service import GeocodingService


class TestGeocodingService:
    @pytest.fixture
    def client(self):
        return Mock(spec=GeocoderClient)

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

    def test_get_districts_by_locality_propagates_exception(
        self,
        service,
        client,
    ):
        client.get_districts_by_query.side_effect = RuntimeError("API error")

        with pytest.raises(RuntimeError, match="API error"):
            service.get_districts_by_locality("Dubai")

    def test_get_district_by_coords(
        self,
        service,
        client,
    ):
        response = Mock(spec=GeocoderApiResponse)
        client.get_districts_by_coords.return_value = response

        result = service.get_district_by_coords(
            17.12441,
            52.2345,
        )

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

    def test_get_districts_by_coords_propagates_exception(
        self,
        service,
        client,
    ):
        client.get_districts_by_coords.side_effect = RuntimeError("API error")

        with pytest.raises(RuntimeError, match="API error"):
            service.get_districts_by_coords(
                longitude=17.12441,
                latitude=52.2345,
            )

    def test_close(
        self,
        service,
        client,
    ):
        service.close()

        client.close.assert_called_once_with()

    def test_context_manager_closes_client(
        self,
        service,
        client,
    ):
        with service:
            pass

        client.close.assert_called_once_with()
