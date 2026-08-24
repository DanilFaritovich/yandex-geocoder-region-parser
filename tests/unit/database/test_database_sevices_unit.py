from unittest.mock import Mock

import pytest

from backend.database.exceptions import (
    PlaceNotFoundError,
    PlaceValidationError,
)
from backend.database.models import Place
from backend.database.service import PlaceService
from tests.unit.database.conftest import PlaceFactory

class TestPlaceServiceClose:
    def test_close(
        self,
        place_service,
        place_repository,
    ):
        place_service.close()

        place_repository.close.assert_called_once_with()


class TestPlaceServiceGetById:
    """
    Unit tests for PlaceService.get_place_by_id().
    """

    @pytest.mark.parametrize(
        "place_id",
        [
            0,
            -1,
        ],
    )
    def test_get_place_by_id_rejects_non_positive_id(
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
    def test_get_place_by_id_rejects_invalid_id_type(
        self,
        place_service,
        place_repository,
        place_id,
    ):
        with pytest.raises(PlaceValidationError):
            place_service.get_place_by_id(place_id)

        place_repository.get_by_id.assert_not_called()

    def test_get_place_by_id_raises_if_place_not_found(
        self,
        place_service,
        place_repository,
    ):
        place_repository.get_by_id.return_value = None

        with pytest.raises(PlaceNotFoundError):
            place_service.get_place_by_id(1)

        place_repository.get_by_id.assert_called_once_with(1)

    def test_get_place_by_id_returns_place(
        self,
        place_service,
        place_repository,
    ):
        place = PlaceFactory.build(id=1)
        place_repository.get_by_id.return_value = place.model_dump(exclude_unset=True)

        result = place_service.get_place_by_id(1)

        assert result == place
        place_repository.get_by_id.assert_called_once_with(1)

class TestPlaceServiceGetByIds:
    """
    Unit tests for PlaceService.get_places_by_ids().
    """

    def test_get_places_by_ids_accepts_empty_list(
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
    def test_get_places_by_ids_rejects_invalid_input_type(
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
    def test_get_places_by_ids_rejects_non_positive_ids(
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
    def test_get_places_by_ids_rejects_invalid_id_types(
        self,
        place_service,
        place_repository,
        place_ids,
    ):
        with pytest.raises(PlaceValidationError):
            place_service.get_places_by_ids(place_ids)

        place_repository.get_by_ids.assert_not_called()

    def test_get_places_by_ids_rejects_too_large_batch(
        self,
        place_service,
        place_repository,
    ):
        place_ids = list(range(1, place_service.MAX_BATCH_SIZE + 2))

        with pytest.raises(PlaceValidationError):
            place_service.get_places_by_ids(place_ids)

        place_repository.get_by_ids.assert_not_called()

    def test_get_places_by_ids_returns_places(
        self,
        place_service,
        place_repository,
    ):
        places = [
            PlaceFactory.build(id=1),
            PlaceFactory.build(id=2),
        ]
        places_dump = [
            p.model_dump(exclude_unset=True) for p in places
        ]

        place_repository.get_by_ids.return_value = places_dump

        result = place_service.get_places_by_ids([1, 2])

        assert result == {
            1: places[0],
            2: places[1],
        }

        place_repository.get_by_ids.assert_called_once_with([1, 2])

    def test_get_places_by_ids_ignores_missing_places(
        self,
        place_service,
        place_repository,
    ):
        places = [
            PlaceFactory.build(id=1),
        ]
        places_dump = [
            p.model_dump(exclude_unset=True) for p in places
        ]

        place_repository.get_by_ids.return_value = places_dump

        result = place_service.get_places_by_ids([1, 2])

        assert result == {
            1: places[0],
        }

        place_repository.get_by_ids.assert_called_once_with([1, 2])