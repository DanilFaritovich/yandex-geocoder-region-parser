# ====================================================================== #
# Business Result Model
# ====================================================================== #

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.api.models import GeoObject, GeocoderApiResponse


class GeocodeResult(BaseModel):
    """Geocoding result with convenient access to address parts."""
    model_config = ConfigDict()

    geocode: Optional[str] = Field(default=None, description="Geocoding query")
    district: Optional[str] = Field(default=None, description="City district (kind=district)")
    area: Optional[str] = Field(default=None, description="Regional/municipal district (kind=area)")
    locality: Optional[str] = Field(default=None, description="Settlement (kind=locality)")
    province: Optional[str] = Field(default=None, description="Region/province (kind=province)")
    country: Optional[str] = Field(default=None, description="Country (kind=country)")
    country_code: Optional[str] = Field(default=None, description="ISO 3166-1 country code")
    formatted: Optional[str] = Field(default=None, description="Full address as one line")
    kind: Optional[str] = Field(default=None, description="Type of found object")
    text: Optional[str] = Field(default=None, description="Text description of the object")
    latitude: Optional[float] = Field(default=None, description="Latitude in degrees")
    longitude: Optional[float] = Field(default=None, description="Longitude in degrees")
    precision: Optional[str] = Field(default=None, description="Match precision")

    @property
    def coordinates(self) -> Optional[tuple[float, float]]:
        """Return coordinates as (lat, lon) tuple."""
        if self.latitude is not None and self.longitude is not None:
            return (self.latitude, self.longitude)
        return None
        