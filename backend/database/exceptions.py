"""
Custom exceptions for PostgreSQL Place module.
"""


class PlaceDBError(Exception):
    """Base exception for all place DB errors."""

    pass


class PlaceConnectionError(PlaceDBError):
    """Raised when cannot connect to database."""

    pass


class PlaceQueryError(PlaceDBError):
    """Raised when SQL query fails."""

    pass


class PlaceNotFoundError(PlaceDBError):
    """Raised when place not found by ID."""

    pass


class PlaceValidationError(PlaceDBError):
    """Raised when input data fails business validation."""

    pass
