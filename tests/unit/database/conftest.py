"""
Fixtures for database unit tests.
Provides factories for test data.
"""
from unittest.mock import Mock

import pytest

from backend.database.models import Place, District
from backend.database.service import PlaceService


# ====================================================================
# Test Data Factory
# ====================================================================
class PlaceFactory:
    """
    Factory for creating test Place objects with sensible defaults.
    
    Usage:
        place = PlaceFactory.build()
        place = PlaceFactory.build(id=42, name="Tula", area="Tula Oblast")
    """

    @staticmethod
    def build(**kwargs) -> Place:
        """Create a Place with defaults, overridden by kwargs."""
        defaults = {
            "id": 1,
            "name": None,
            "polygon": None,
        }
        defaults.update(kwargs)
        return Place(**defaults)


class DistrictFactory:
    """
    Factory for creating test District objects with sensible defaults.
    
    Usage:
        district = DistrictFactory.build()
        district = DistrictFactory.build(name="Tula", polygon=Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]))
    """

    @staticmethod
    def build(**kwargs) -> District:
        """Create a District with defaults, overridden by kwargs."""
        defaults = {
            "name": None,
            "polygon": None,
        }
        defaults.update(kwargs)
        return District(**defaults)

# ====================================================================
# Factories
# =====================================================================

@pytest.fixture
def place_factory():
    """Provides the PlaceFactory for creating test data."""
    return PlaceFactory.build

@pytest.fixture
def district_factory():
    """Provides the DistrictFactory for creating test data."""
    return DistrictFactory.build

# ====================================================================
# Service
# =====================================================================

@pytest.fixture
def place_repository():
    return Mock()

@pytest.fixture
def place_service(place_repository):
    return PlaceService(repository=place_repository)