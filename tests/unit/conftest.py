import json

import pytest


@pytest.fixture
def yandex_geocoder_response():
    """Provides the YandexGeocoderResponse for creating test data."""
    with open("tests/fixtures/yandex_geocoder_response.json") as f:
        return json.load(f)