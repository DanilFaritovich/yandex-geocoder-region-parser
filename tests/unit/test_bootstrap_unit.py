from pathlib import Path
from unittest.mock import Mock

from backend.bootstrap import create_etl_service
from backend.etl.coords_service import CoordsETLService


def test_create_etl_service_returns_configured_service(monkeypatch):
    geometry_service = Mock()
    geocoding_service = Mock()
    place_service = Mock()
    transformer = Mock()
    writer = Mock()
    geocoder_connector = Mock()

    monkeypatch.setattr(
        "backend.bootstrap.PolygonService",
        lambda: geometry_service,
    )
    monkeypatch.setattr(
        "backend.bootstrap.YandexGeocoderConnector",
        lambda: geocoder_connector,
    )
    monkeypatch.setattr(
        "backend.bootstrap.GeocodingService",
        lambda client: geocoding_service,
    )
    monkeypatch.setattr(
        "backend.bootstrap.PlaceService",
        lambda repository: place_service,
    )
    monkeypatch.setattr(
        "backend.bootstrap.GeocodingTransformerService",
        lambda: transformer,
    )
    monkeypatch.setattr(
        "backend.bootstrap.CsvConnector",
        lambda path: writer,
    )

    result = create_etl_service()

    assert result is not None

    assert isinstance(result, CoordsETLService)

    assert result._geometry_service is geometry_service
    assert result._geocoding_service is geocoding_service
    assert result._place_service is place_service
    assert result._transformer is transformer
    assert result._writer is writer