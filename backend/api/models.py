"""
Pydantic models for Yandex Geocoder API.
Contains: API response models, settings, and business result models.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


# ====================================================================== #
# API Response Models (mirror Yandex Geocoder JSON schema)
# ====================================================================== #

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Component(BaseModel):
    """Single address component from Yandex Geocoder response."""

    kind: str = Field(
        description=(
            "Component type: country, province, area, locality, "
            "district, street, house"
        )
    )
    name: str = Field(
        description="Component name"
    )


class Address(BaseModel):
    """Structured address of a geographic object."""

    country_code: str = Field(
        description="ISO 3166-1 country code"
    )
    formatted: str = Field(
        description="Full formatted address"
    )
    components: list[Component] = Field(
        default_factory=list,
        alias="Components",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class GeocoderMetaData(BaseModel):
    """Metadata describing a geocoded object."""

    kind: str = Field(
        description="Type of geographic object"
    )
    text: str = Field(
        default="",
        description="Full address as text"
    )
    precision: str = Field(
        default="",
        description="Geocoding precision"
    )
    address: Address = Field(
        alias="Address",
        description="Structured address"
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class Point(BaseModel):
    """Geographic coordinates."""

    pos: str = Field(
        description="Coordinates in 'longitude latitude' format"
    )


class GeoObjectMetaData(BaseModel):
    """Metadata wrapper inside a GeoObject."""

    geocoder_metadata: GeocoderMetaData = Field(
        alias="GeocoderMetaData",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class GeoObject(BaseModel):
    """Single geographic object returned by Yandex Geocoder."""

    meta_data_property: GeoObjectMetaData = Field(
        alias="metaDataProperty",
    )
    point: Point = Field(
        alias="Point",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class FeatureMember(BaseModel):
    """Wrapper around a geographic object."""

    geo_object: GeoObject = Field(
        alias="GeoObject",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class GeocoderResponseMetaData(BaseModel):
    """Metadata describing the geocoder response."""

    request: str
    found: str
    results: str


class MetaDataProperty(BaseModel):
    """Metadata wrapper of the GeoObject collection."""

    geocoder_response: GeocoderResponseMetaData = Field(
        alias="GeocoderResponseMetaData",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class GeoObjectCollection(BaseModel):
    """Collection of geographic objects returned by the API."""

    meta_data_property: MetaDataProperty = Field(
        alias="metaDataProperty",
    )
    feature_member: list[FeatureMember] = Field(
        default_factory=list,
        alias="featureMember",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class Response(BaseModel):
    """Top-level Yandex Geocoder response."""

    geo_object_collection: GeoObjectCollection = Field(
        alias="GeoObjectCollection",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class GeocoderApiResponse(BaseModel):
    """Complete Yandex Geocoder API response."""

    response: Response


# ====================================================================== #
# Configuration
# ====================================================================== #

class GeocoderSettings(BaseSettings):
    """
    Geocoder configuration.
    Loads from env vars with prefix YANDEX_GEOCODER_ or from .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="YANDEX_GEOCODER_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(min_length=1, description="Yandex Maps API key")
    base_url: str = Field(min_length=1, description="API endpoint")
    timeout: int = Field(default=10, description="HTTP request timeout in seconds")
    lang: str = Field(default="ru_RU", description="Response language")
    retries: int = Field(default=1, description="Number of retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries (seconds)")

# ====================================================================== #
# Requests
# ====================================================================== #

class GeocodeRequest(BaseModel):
    """Base request for Yandex Geocoder API."""

    geocode: str = Field(
        min_length=1,
        description="Address or locality to geocode",
    )
    lang: str = Field(
        default="ru_RU",
        description="Response language",
    )
    kind: Optional[str] = Field(
        default=None,
        description="Type of found object",
    )
    format: str = Field(
        default="json",
        description="Response format",
    )
    results: int = Field(
        default=1,
        ge=1,
        description="Maximum number of results",
    )
    skip: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip",
    )

    def params(self, api_key: str) -> dict[str, str | int]:
        """Build Yandex Geocoder API query parameters."""
        par = {
            "apikey": api_key,
            "geocode": self.geocode,
            "lang": self.lang,
            "format": self.format,
            "results": self.results,
            "skip": self.skip,
        }
        if self.kind is not None:
            par["kind"] = self.kind

        return par


class GeocodeDistrictRequest(GeocodeRequest):
    """Request for geocoding district information."""

    def params(self, api_key: str) -> Dict[str, str | int]:
        self.kind = "district"
        par = super().params(api_key)
        return par