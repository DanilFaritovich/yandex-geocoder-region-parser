import pytest
from pytest_httpserver import HTTPServer

from backend.api.connector import YandexGeocoderConnector
from backend.api.exceptions import (
    YandexGeocoderAPIError,
    YandexGeocoderAuthError,
    YandexGeocoderParseError,
)
from backend.api.models import GeocoderApiResponse


@pytest.fixture
def query_params() -> dict[str, str]:
    return {
        "geocode": "Dubai",
        "results": "1",
        "skip": "0",
        "lang": "ru_RU",
        "apikey": "test-api-key",
        "format": "json",
        "kind": "district",
    }


@pytest.fixture
def coords_params() -> dict[str, str]:
    return {
        "geocode": "55.2708,25.2048",
        "results": "1",
        "skip": "0",
        "lang": "ru_RU",
        "apikey": "test-api-key",
        "format": "json",
        "kind": "district",
    }


@pytest.fixture
def configure_success_response(
    httpserver: HTTPServer,
    yandex_response: dict,
):
    """Configure successful Yandex Geocoder response."""

    def configure(
        query_string: dict[str, str],
    ) -> None:
        httpserver.expect_request(
            "/1.x/",
            method="GET",
            query_string=query_string,
        ).respond_with_json(yandex_response)

    return configure


@pytest.mark.integration
class TestYandexGeocoderQueryConnector:
    def test_get_districts_by_query_returns_response(
        self,
        geocoder_connector: YandexGeocoderConnector,
        configure_success_response,
        query_params: dict[str, str],
    ):
        configure_success_response(query_params)

        response = geocoder_connector.get_districts_by_query(
            query="Dubai",
            results=1,
        )

        assert isinstance(response, GeocoderApiResponse)

        members = response.response.geo_object_collection.feature_member

        assert len(members) == 1

    def test_get_districts_by_query_maps_geo_object(
        self,
        geocoder_connector: YandexGeocoderConnector,
        configure_success_response,
        query_params: dict[str, str],
    ):
        configure_success_response(query_params)

        response = geocoder_connector.get_districts_by_query(
            query="Dubai",
        )

        geo_object = response.response.geo_object_collection.feature_member[
            0
        ].geo_object

        metadata = geo_object.meta_data_property.geocoder_metadata

        assert metadata.kind == "house"
        assert metadata.text == ("ОАЭ, Дубай, бульвар Мухаммед Бин Рашид, дом 1")
        assert metadata.precision == "exact"

        assert metadata.address.country_code == "UAE"
        assert metadata.address.formatted == ("Дубай, бульвар Мухаммед Бин Рашид, 1")

        assert geo_object.point.pos == "25.197300 55.274243"

    def test_get_districts_by_query_sends_skip_parameter(
        self,
        geocoder_connector: YandexGeocoderConnector,
        configure_success_response,
        query_params: dict[str, str],
    ):
        query_params["results"] = "2"
        query_params["skip"] = "3"

        configure_success_response(query_params)

        response = geocoder_connector.get_districts_by_query(
            query="Dubai",
            results=2,
            skip=3,
        )

        assert isinstance(response, GeocoderApiResponse)


@pytest.mark.integration
class TestYandexGeocoderCoordsConnector:
    def test_get_districts_by_coords_returns_response(
        self,
        geocoder_connector: YandexGeocoderConnector,
        configure_success_response,
        coords_params: dict[str, str],
    ):
        configure_success_response(coords_params)

        response = geocoder_connector.get_districts_by_coords(
            longitude=55.2708,
            latitude=25.2048,
            results=1,
        )

        assert isinstance(response, GeocoderApiResponse)

        members = response.response.geo_object_collection.feature_member

        assert len(members) == 1

    def test_get_districts_by_coords_maps_geo_object(
        self,
        geocoder_connector: YandexGeocoderConnector,
        configure_success_response,
        coords_params: dict[str, str],
    ):
        configure_success_response(coords_params)

        response = geocoder_connector.get_districts_by_coords(
            longitude=55.2708,
            latitude=25.2048,
        )

        geo_object = response.response.geo_object_collection.feature_member[
            0
        ].geo_object

        metadata = geo_object.meta_data_property.geocoder_metadata

        assert metadata.kind == "house"
        assert metadata.precision == "exact"
        assert metadata.address.country_code == "UAE"
        assert metadata.address.formatted == ("Дубай, бульвар Мухаммед Бин Рашид, 1")
        assert geo_object.point.pos == "25.197300 55.274243"

    def test_get_districts_by_coords_sends_skip_parameter(
        self,
        geocoder_connector: YandexGeocoderConnector,
        configure_success_response,
        coords_params: dict[str, str],
    ):
        coords_params["results"] = "2"
        coords_params["skip"] = "3"

        configure_success_response(coords_params)

        response = geocoder_connector.get_districts_by_coords(
            longitude=55.2708,
            latitude=25.2048,
            results=2,
            skip=3,
        )

        assert isinstance(response, GeocoderApiResponse)


@pytest.mark.integration
class TestYandexGeocoderErrorHandling:
    def test_403_raises_auth_error_without_retry(
        self,
        httpserver: HTTPServer,
        geocoder_connector: YandexGeocoderConnector,
    ):
        httpserver.expect_request(
            "/1.x/",
            method="GET",
        ).respond_with_data(
            "Forbidden",
            status=403,
        )

        with pytest.raises(YandexGeocoderAuthError):
            geocoder_connector.get_districts_by_query(
                query="Dubai",
            )

        assert len(httpserver.log) == 1

    def test_500_retries_and_succeeds(
        self,
        httpserver: HTTPServer,
        geocoder_connector: YandexGeocoderConnector,
        yandex_response: dict,
    ):
        httpserver.expect_oneshot_request(
            "/1.x/",
            method="GET",
        ).respond_with_data(
            "Internal Server Error",
            status=500,
        )

        httpserver.expect_oneshot_request(
            "/1.x/",
            method="GET",
        ).respond_with_data(
            "Internal Server Error",
            status=500,
        )

        httpserver.expect_request(
            "/1.x/",
            method="GET",
        ).respond_with_json(yandex_response)

        response = geocoder_connector.get_districts_by_query(
            query="Dubai",
        )

        assert isinstance(response, GeocoderApiResponse)
        assert len(httpserver.log) == 3

    def test_500_raises_api_error_after_all_retries(
        self,
        httpserver: HTTPServer,
        geocoder_connector: YandexGeocoderConnector,
    ):
        httpserver.expect_request(
            "/1.x/",
            method="GET",
        ).respond_with_data(
            "Internal Server Error",
            status=500,
        )

        with pytest.raises(YandexGeocoderAPIError):
            geocoder_connector.get_districts_by_query(
                query="Dubai",
            )

        assert len(httpserver.log) == 3

    def test_malformed_response_raises_parse_error(
        self,
        httpserver: HTTPServer,
        geocoder_connector: YandexGeocoderConnector,
    ):
        httpserver.expect_request(
            "/1.x/",
            method="GET",
        ).respond_with_json(
            {"invalid": "response"},
        )

        with pytest.raises(YandexGeocoderParseError):
            geocoder_connector.get_districts_by_query(
                query="Dubai",
            )
