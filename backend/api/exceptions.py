"""
Custom exceptions for Yandex Geocoder module.
"""


class YandexGeocoderError(Exception):
    """Base exception for all geocoder errors."""
    pass


class YandexGeocoderAuthError(YandexGeocoderError):
    """Raised when API key is invalid or rate limit exceeded."""
    pass


class YandexGeocoderAPIError(YandexGeocoderError):
    """Raised when API returns an unexpected error."""
    pass


class YandexGeocoderParseError(YandexGeocoderError):
    """Raised when API response cannot be parsed/validated."""
    pass


class GeocodingNotFoundError(YandexGeocoderError):
    """Raised when no results found for the query."""
    pass


class GeocodingValidationError(YandexGeocoderError):
    """Raised when input data fails business validation."""
    pass    