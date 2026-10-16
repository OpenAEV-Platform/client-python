"""Configuration data contracts: hints, base models and serialization types.

Settings models are frozen, allow extra fields for forward compatibility and
validate their defaults. Source priority when loading settings (highest to
lowest): environment variables, YAML config file, .env file, defaults.
"""

from abc import ABC
from datetime import timedelta
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, PlainSerializer

__all__ = [
    "BaseConfigModel",
    "CONFIGURATION_TYPES",
    "ConfigLoaderCollector",
    "ConfigLoaderOAEV",
    "ConfigurationHint",
    "HttpUrlToString",
    "LogLevelToLower",
    "TimedeltaInSeconds",
]

CONFIGURATION_TYPES = str | int | bool | Any | None
"""Union type for configuration values."""


class ConfigurationHint(BaseModel):
    """An individual configuration hint defining where a value can be found.

    Hints specify the resolution strategy for a configuration key:
    which environment variable to check, which file path to follow,
    and what default to use if no source provides a value.

    The model is mutable: ``Configuration.set()`` assigns ``data`` in place.

    Args:
        data: Override value. When set, this value is returned directly.
        env: Environment variable name to read.
        file_path: JSON path (nested keys) in the config file.
        is_number: Whether to interpret the resolved value as an integer.
        default: Fallback value when no source provides one.

    Example:
        >>> hint = ConfigurationHint(env="LOG_LEVEL", default="info")
        >>> hint.data = "debug"  # override
    """

    data: CONFIGURATION_TYPES = Field(default=None)
    env: str | None = Field(default=None)
    file_path: list[str] | None = Field(default=None)
    is_number: bool | None = Field(default=False)
    default: CONFIGURATION_TYPES = Field(default=None)


class BaseConfigModel(BaseModel, ABC):
    """Abstract base for frozen configuration models.

    All configuration models inherit from this class to ensure
    immutability after initialization and allow extra fields
    for forward compatibility.

    Example:
        >>> class MyConfig(BaseConfigModel):
        ...     url: str
        ...     timeout: int = 30
        >>> cfg = MyConfig(url="http://localhost")
        >>> cfg.url = "other"  # raises ValidationError (frozen)
    """

    model_config = ConfigDict(extra="allow", frozen=True, validate_default=True)


# Annotated type aliases for common configuration field patterns

LogLevelToLower = Annotated[
    Literal["debug", "info", "warn", "error"],
    PlainSerializer(lambda v: "".join(v), return_type=str),
]
"""Log level literal type that serializes to lowercase string."""

HttpUrlToString = Annotated[HttpUrl, PlainSerializer(str, return_type=str)]
"""HTTP URL type that serializes to plain string."""

TimedeltaInSeconds = Annotated[
    timedelta, PlainSerializer(lambda v: int(v.total_seconds()), return_type=int)
]
"""Timedelta type that serializes to integer seconds."""


class ConfigLoaderOAEV(BaseConfigModel):
    """OpenAEV platform connection configuration.

    Args:
        url: The OpenAEV platform URL.
        token: Authentication token for the platform API.
        tenant_id: Optional tenant identifier for multi-tenant deployments.
    """

    url: HttpUrlToString = Field(
        description="The OpenAEV platform URL.",
    )
    token: str = Field(
        description="The token for the OpenAEV platform.",
    )
    tenant_id: UUID | None = Field(
        default=None,
        description="Identifier of the tenant within the OpenAEV platform. "
        "Used in multi-tenant environments to scope API requests and ensure data isolation between different tenants.",
    )


class ConfigLoaderCollector(BaseConfigModel):
    """Base collector configuration settings.

    Common settings shared by all collectors including identification,
    logging level, scheduling period, and UI customization.

    Args:
        id: Unique identifier of the collector instance.
        name: Human-readable collector name.
        log_level: Logging verbosity (debug/info/warn/error).
        period: Duration between scheduled runs (ISO 8601).
        icon_filepath: Path to the collector's icon file.
    """

    id: str = Field(description="ID of the collector.")
    name: str = Field(description="Name of the collector")
    log_level: LogLevelToLower | None = Field(
        default="error",
        description="Determines the verbosity of the logs.",
    )
    period: timedelta | None = Field(
        default=timedelta(minutes=1),
        description="Duration between two scheduled runs of the collector (ISO 8601 format).",
    )
    icon_filepath: str | None = Field(
        description="Path to the icon file of the collector.",
    )
    author: str | None = Field(
        default=None,
        description="Optional author override for the connector's payloads and contracts. "
        "When absent, the platform attributes them to the connector's name.",
    )
    platform_description: str | None = Field(
        default=None,
        description="Description applied to the security platform auto-created by the "
        "collector, so its read-only card is not empty in the platform UI.",
    )
    platform_tags: list[str] | str | None = Field(
        default=None,
        description="Tag names applied to the security platform auto-created by the "
        "collector. Accepts a list of names or a single comma-separated string "
        "(the usual shape when configured through an environment variable).",
    )
