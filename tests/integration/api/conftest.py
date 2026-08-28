import json
from collections.abc import Generator
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from backend.api.connector import YandexGeocoderConnector
from backend.api.models import GeocoderSettings


@pytest.fixture
def yandex_response() -> dict:
    path = Path("tests/fixtures/yandex_geocoder_response.json")

    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def geocoder_connector(
    httpserver: HTTPServer,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[YandexGeocoderConnector]:
    settings = GeocoderSettings(
        base_url=httpserver.url_for("/1.x/"),
        api_key="test-api-key",
        lang="ru_RU",
        timeout=1,
        retries=3,
        retry_delay=0,
    )

    monkeypatch.setattr(
        "backend.api.connector.GeocoderSettings",
        lambda: settings,
    )

    connector = YandexGeocoderConnector()

    yield connector

    connector.close()
