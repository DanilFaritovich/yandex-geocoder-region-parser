"""
Pydantic models for PostgreSQL Place module.
Contains: DB settings and Place, District entity models.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from shapely import wkt
from shapely.geometry import Polygon


# ====================================================================== #
# Env Settings
# ====================================================================== #
class EnvSettings(BaseSettings):
    """Environment settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="ENV_", env_file_encoding="utf-8", extra="ignore"
    )

    path: str = Field(default=".env", description="Path to .env file")

    @property
    def env_files(self) -> tuple[str, ...]:
        if self.path == ".env":
            return (".env",)
        else:
            return (".env", self.path)


# ====================================================================== #
# Database Settings
# ====================================================================== #


class PlaceDBSettings(BaseSettings):
    """
    PostgreSQL connection settings.
    Loads from env vars with prefix PLACE_DB_ or from .env file.

    Example .env:
        PLACE_DB_HOST=localhost
        PLACE_DB_PORT=5432
        PLACE_DB_NAME=mydb
        PLACE_DB_USER=myuser
        PLACE_DB_PASSWORD=secret
    """

    model_config = SettingsConfigDict(
        env_file=EnvSettings().env_files,
        env_prefix="DB_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    dbname: str = Field(default="dbname", description="Database name")
    user: str = Field(default="user", description="Database user")
    password: str = Field(default="password", description="Database password")

    # Connection pool settings
    pool_min_size: int = Field(default=2, description="Minimum pool size")
    pool_max_size: int = Field(default=10, description="Maximum pool size")
    connect_timeout: int = Field(default=10, description="Connection timeout (seconds)")

    sslmode: str = Field(
        default="require",
        description="PostgreSQL SSL mode",
    )

    sql_file_path: str = Field(default="sql/work", description="SQL file for work")

    @property
    def conninfo(self) -> str:
        """Build psycopg connection string."""
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.dbname} "
            f"user={self.user} "
            f"password={self.password} "
            f"connect_timeout={self.connect_timeout} "
            f"sslmode={self.sslmode}"
        )

    @property
    def conn_kwargs(self) -> dict[str, Any]:
        """Build psycopg connection kwargs."""
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
            "connect_timeout": self.connect_timeout,
        }


# ====================================================================== #
# District Entity Model
# ====================================================================== #


class District(BaseModel):
    """District entity — administrative division received from API."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    name: str | None = Field(default=None, description="District name")
    polygon: Polygon | None = Field(default=None, description="District polygon")

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> District:
        """
        Build District from API response.
        """

        column_map = {
            "name": "name",
            "polygon": "polygon",
        }

        # Map DB row keys to model fields
        mapped_row: dict[str, Any] = {}
        for db_col, model_field in column_map.items():
            if db_col in row:
                mapped_row[model_field] = row[db_col]

        return cls.model_validate(mapped_row)


# ====================================================================== #
# Place Entity Model
# ====================================================================== #


class Place(BaseModel):
    """
    Place entity from t_place table.

    NOTE: Adjust fields to match your actual t_place schema.
    """

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: int = Field(description="Place ID (primary key)")
    c_description: str | None = Field(default=None, description="Place name")
    c_language_code: str | None = Field(default=None, description="Language code")
    c_polygon: Polygon | None = Field(default=None, description="Place polygon")
    districts: list[District] = Field(
        default_factory=list, description="List of districts"
    )

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> Place:
        """Build Place from database row."""

        polygon = None

        polygon_text = row.get("c_polygon_text")

        if polygon_text:
            geometry = wkt.loads(polygon_text)

            if not isinstance(geometry, Polygon):
                raise ValueError(f"Expected Polygon geometry, got {geometry.geom_type}")

            polygon = geometry

        mapped_row = {
            "id": row["id"],
            "c_description": row.get("c_description"),
            "c_language_code": row.get("c_language_code"),
            "c_polygon": polygon,
        }

        return cls.model_validate(mapped_row)

    def add_district(self, district: District) -> None:
        """
        Add a single district to this place.

        Args:
            district: District object to add

        Raises:
            ValueError: if district with same name already exists
        """
        if not isinstance(district, District):
            raise TypeError("district must be of type District")

        if district.name and any(d.name == district.name for d in self.districts):
            raise ValueError(f"District with name {district.name} already exists")

        self.districts.append(district)
