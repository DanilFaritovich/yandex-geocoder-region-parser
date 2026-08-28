# ====================================================================== #
# Business Result Model
# ====================================================================== #


from pydantic import BaseModel, ConfigDict, Field


class GeocodeResult(BaseModel):
    """Geocoding result with convenient access to address parts."""

    model_config = ConfigDict()

    geocode: str | None = Field(default=None, description="Geocoding query")
    district: str | None = Field(
        default=None, description="City district (kind=district)"
    )
    area: str | None = Field(
        default=None, description="Regional/municipal district (kind=area)"
    )
    locality: str | None = Field(default=None, description="Settlement (kind=locality)")
    province: str | None = Field(
        default=None, description="Region/province (kind=province)"
    )
    country: str | None = Field(default=None, description="Country (kind=country)")
    country_code: str | None = Field(
        default=None, description="ISO 3166-1 country code"
    )
    formatted: str | None = Field(default=None, description="Full address as one line")
    kind: str | None = Field(default=None, description="Type of found object")
    text: str | None = Field(default=None, description="Text description of the object")
    latitude: float | None = Field(default=None, description="Latitude in degrees")
    longitude: float | None = Field(default=None, description="Longitude in degrees")
    precision: str | None = Field(default=None, description="Match precision")

    @property
    def coordinates(self) -> tuple[float, float] | None:
        """Return coordinates as (lat, lon) tuple."""
        if self.latitude is not None and self.longitude is not None:
            return (self.latitude, self.longitude)
        return None
