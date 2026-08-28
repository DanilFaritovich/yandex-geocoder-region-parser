import pytest

from backend.database.exceptions import (
    PlaceNotFoundError,
    PlaceValidationError,
)
from tests.unit.database.conftest import PlaceFactory


class TestPlaceServiceGetPlaceById:
    """Tests for PlaceService.get_place_by_id()."""

    @pytest.mark.parametrize(
        "place_id",
        [0, -1],
    )
    def test_rejects_non_positive_id(
        self,
        place_service,
        place_repository,
        place_id,
    ):
        with pytest.raises(PlaceValidationError):
            place_service.get_place_by_id(place_id)

        place_repository.get_by_id.assert_not_called()

    @pytest.mark.parametrize(
        "place_id",
        [
            "1",
            1.5,
            None,
            True,
            [],
        ],
    )
    def test_rejects_invalid_id_type(
        self,
        place_service,
        place_repository,
        place_id,
    ):
        with pytest.raises(PlaceValidationError):
            place_service.get_place_by_id(place_id)

        place_repository.get_by_id.assert_not_called()

    def test_raises_when_place_not_found(
        self,
        place_service,
        place_repository,
    ):
        place_repository.get_by_id.return_value = None

        with pytest.raises(
            PlaceNotFoundError,
            match="Place with id=1 not found",
        ):
            place_service.get_place_by_id(1)

        place_repository.get_by_id.assert_called_once_with(1)

    def test_returns_place(
        self,
        place_service,
        place_repository,
    ):
        place = PlaceFactory.build(id=1)
        place_repository.get_by_id.return_value = place

        result = place_service.get_place_by_id(1)

        assert result == place
        place_repository.get_by_id.assert_called_once_with(1)


class TestPlaceServiceGetPlacesByIds:
    """Tests for PlaceService.get_places_by_ids()."""

    def test_returns_empty_dict_for_empty_list(
        self,
        place_service,
        place_repository,
    ):
        result = place_service.get_places_by_ids([])

        assert result == {}
        place_repository.get_by_ids.assert_not_called()

    @pytest.mark.parametrize(
        "place_ids",
        [
            None,
            "1,2,3",
            (1, 2, 3),
            {1, 2, 3},
            1,
        ],
    )
    def test_rejects_invalid_input_type(
        self,
        place_service,
        place_repository,
        place_ids,
    ):
        with pytest.raises(PlaceValidationError):
            place_service.get_places_by_ids(place_ids)

        place_repository.get_by_ids.assert_not_called()

    @pytest.mark.parametrize(
        "place_ids",
        [
            [0],
            [-1],
            [1, 0],
            [1, -5, 10],
        ],
    )
    def test_rejects_non_positive_ids(
        self,
        place_service,
        place_repository,
        place_ids,
    ):
        with pytest.raises(PlaceValidationError):
            place_service.get_places_by_ids(place_ids)

        place_repository.get_by_ids.assert_not_called()

    @pytest.mark.parametrize(
        "place_ids",
        [
            [1, "2"],
            [1, 2.5],
            [None],
            [True],
        ],
    )
    def test_rejects_invalid_id_types(
        self,
        place_service,
        place_repository,
        place_ids,
    ):
        with pytest.raises(PlaceValidationError):
            place_service.get_places_by_ids(place_ids)

        place_repository.get_by_ids.assert_not_called()

    def test_rejects_batch_larger_than_max_size(
        self,
        place_service,
        place_repository,
    ):
        place_ids = list(range(1, place_service.MAX_BATCH_SIZE + 2))

        with pytest.raises(
            PlaceValidationError,
            match="Batch too large",
        ):
            place_service.get_places_by_ids(place_ids)

        place_repository.get_by_ids.assert_not_called()

    def test_returns_places_by_id(
        self,
        place_service,
        place_repository,
    ):
        places = [
            PlaceFactory.build(id=1),
            PlaceFactory.build(id=2),
        ]

        place_repository.get_by_ids.return_value = places

        result = place_service.get_places_by_ids([1, 2])

        assert result == {
            1: places[0],
            2: places[1],
        }

        place_repository.get_by_ids.assert_called_once_with([1, 2])

    def test_omits_missing_places(
        self,
        place_service,
        place_repository,
    ):
        place = PlaceFactory.build(id=1)

        place_repository.get_by_ids.return_value = [place]

        result = place_service.get_places_by_ids([1, 2])

        assert result == {
            1: place,
        }

        place_repository.get_by_ids.assert_called_once_with([1, 2])

    def test_does_not_fail_when_all_places_are_missing(
        self,
        place_service,
        place_repository,
    ):
        place_repository.get_by_ids.return_value = []

        result = place_service.get_places_by_ids([1, 2, 3])

        assert result == {}

        place_repository.get_by_ids.assert_called_once_with(
            [1, 2, 3],
        )


class TestPlaceServiceClose:
    """Tests for PlaceService.close()."""

    def test_close(
        self,
        place_service,
        place_repository,
    ):
        place_service.close()

        place_repository.close.assert_called_once_with()


class TestPlaceServiceContextManager:
    """Tests for PlaceService context manager."""

    def test_enter_returns_service(
        self,
        place_service,
    ):
        result = place_service.__enter__()

        assert result is place_service

    def test_exit_closes_repository(
        self,
        place_service,
        place_repository,
    ):
        place_service.__exit__(None, None, None)

        place_repository.close.assert_called_once_with()
