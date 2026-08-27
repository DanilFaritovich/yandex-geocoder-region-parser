import pytest

from backend.api.models import GeocoderApiResponse
from backend.transformer.models import GeocodeResult
from backend.transformer.service import GeocodingTransformerService


class TestGeocodingTransformerService:
    """Unit tests for GeocodingTransformerService."""

    @pytest.fixture
    def service(self) -> GeocodingTransformerService:
        return GeocodingTransformerService()

    def test_transform_districts_returns_geocode_results(
        self,
        service: GeocodingTransformerService,
        yandex_geocoder_response_model: GeocoderApiResponse,
    ):
        result = service.transform_districts(
            query="Dubai",
            response=yandex_geocoder_response_model,
        )

        assert len(result) == 1
        assert isinstance(result[0], GeocodeResult)

    def test_transform_districts_maps_address_data(
        self,
        service: GeocodingTransformerService,
        yandex_geocoder_response_model: GeocoderApiResponse,
    ):
        result = service.transform_districts(
            query="Dubai",
            response=yandex_geocoder_response_model,
        )

        geocode = result[0]

        assert geocode.geocode == "Dubai"
        assert geocode.formatted is not None
        assert geocode.country is not None
        assert geocode.country_code is not None
        assert geocode.district is not None
        assert geocode.latitude is not None
        assert geocode.longitude is not None

    def test_transform_districts_maps_coordinates(
        self,
        service: GeocodingTransformerService,
        yandex_geocoder_response_model: GeocoderApiResponse,
    ):
        result = service.transform_districts(
            query="Dubai",
            response=yandex_geocoder_response_model,
        )

        geocode = result[0]

        assert geocode.longitude == pytest.approx(25.1973)
        assert geocode.latitude == pytest.approx(55.274243)

    def test_transform_districts_returns_empty_list_for_empty_response(
        self,
        service: GeocodingTransformerService,
        yandex_geocoder_response_model: GeocoderApiResponse,
    ):
        response = yandex_geocoder_response_model.model_copy(deep=True)
        response.response.geo_object_collection.feature_member = []

        result = service.transform_districts(
            query="Dubai",
            response=response,
        )

        assert result == []

    def test_transform_districts_ignores_objects_without_district(
        self,
        service: GeocodingTransformerService,
        yandex_geocoder_response_model: GeocoderApiResponse,
    ):
        response = yandex_geocoder_response_model.model_copy(deep=True)

        for member in response.response.geo_object_collection.feature_member:
            components = (
                member
                .geo_object
                .meta_data_property
                .geocoder_metadata
                .address
                .components
            )

            components[:] = [
                component
                for component in components
                if component.kind != "district"
            ]

        result = service.transform_districts(
            query="Dubai",
            response=response,
        )

        assert result == []

    def test_transform_districts_deduplicates_by_district(
        self,
        service: GeocodingTransformerService,
        yandex_geocoder_response_model: GeocoderApiResponse,
    ):
        response = yandex_geocoder_response_model.model_copy(deep=True)

        members = response.response.geo_object_collection.feature_member

        first = members[0]
        second = first.model_copy(deep=True)

        members.append(second)

        result = service.transform_districts(
            query="Dubai",
            response=response,
        )

        districts = [item.district for item in result]

        assert len(districts) == len(set(districts))

    def test_transform_districts_keeps_first_duplicate(
        self,
        service: GeocodingTransformerService,
        yandex_geocoder_response_model: GeocoderApiResponse,
    ):
        response = yandex_geocoder_response_model.model_copy(deep=True)

        members = response.response.geo_object_collection.feature_member

        first = members[0]
        second = first.model_copy(deep=True)

        members.append(second)

        first_district = next(
            component.name
            for component in (
                first
                .geo_object
                .meta_data_property
                .geocoder_metadata
                .address
                .components
            )
            if component.kind == "district"
        )

        result = service.transform_districts(
            query="Dubai",
            response=response,
        )

        assert result[0].district == first_district
        assert len(result) == 1

    def test_transform_districts_handles_invalid_coordinates(
        self,
        service: GeocodingTransformerService,
        yandex_geocoder_response_model: GeocoderApiResponse,
    ):
        response = yandex_geocoder_response_model.model_copy(deep=True)

        geo_object = (
            response
            .response
            .geo_object_collection
            .feature_member[0]
            .geo_object
        )

        geo_object.point.pos = "invalid coordinates"

        result = service.transform_districts(
            query="Dubai",
            response=response,
        )

        assert len(result) == 1
        assert result[0].latitude is None
        assert result[0].longitude is None

    def test_transform_districts_handles_empty_coordinates(
        self,
        service: GeocodingTransformerService,
        yandex_geocoder_response_model: GeocoderApiResponse,
    ):
        response = yandex_geocoder_response_model.model_copy(deep=True)

        geo_object = (
            response
            .response
            .geo_object_collection
            .feature_member[0]
            .geo_object
        )

        geo_object.point.pos = ""

        result = service.transform_districts(
            query="Dubai",
            response=response,
        )

        assert len(result) == 1
        assert result[0].latitude is None
        assert result[0].longitude is None

    def test_transform_districts_by_list_returns_results(
        self,
        service: GeocodingTransformerService,
        yandex_geocoder_response_model: GeocoderApiResponse,
    ):
        result = service.transfrom_districts_by_list(
            query="Dubai",
            responses=[
                yandex_geocoder_response_model,
            ],
        )

        assert result
        assert all(
            isinstance(item, GeocodeResult)
            for item in result
        )

    def test_transform_districts_by_list_returns_empty_for_empty_input(
        self,
        service: GeocodingTransformerService,
    ):
        result = service.transfrom_districts_by_list(
            query="Dubai",
            responses=[],
        )

        assert result == []

    def test_transform_districts_by_list_deduplicates_results(
        self,
        service: GeocodingTransformerService,
        yandex_geocoder_response_model: GeocoderApiResponse,
    ):
        result = service.transfrom_districts_by_list(
            query="Dubai",
            responses=[
                yandex_geocoder_response_model,
                yandex_geocoder_response_model,
            ],
        )

        districts = [item.district for item in result]

        assert len(districts) == len(set(districts))