import json

import pytest

from backend.api.models import GeocoderApiResponse
from backend.transformer.service import GeocodingTransformerService


@pytest.fixture
def yandex_geocoder_response():
    """Provides the YandexGeocoderResponse for creating test data."""
    with open("tests/fixtures/yandex_geocoder_response.json") as f:
        return json.load(f)


@pytest.fixture
def yandex_geocoder_response_model(yandex_geocoder_response):
    """Provides the YandexGeocoderResponse for creating test data."""
    return GeocoderApiResponse.model_validate(yandex_geocoder_response)


@pytest.fixture
def geocode_result(yandex_geocoder_response_model):
    service = GeocodingTransformerService()

    return service.transform_districts(
        query="Dubai",
        response=yandex_geocoder_response_model,
    )[0]
