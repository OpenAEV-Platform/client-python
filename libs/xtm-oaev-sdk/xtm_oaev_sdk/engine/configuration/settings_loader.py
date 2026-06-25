"""Settings loader: Pydantic-based configuration from env, YAML, and .env files.

Provides base models and settings classes for structured, validated
configuration loading with prioritized source resolution.

Source priority (highest to lowest):
    1. Environment variables
    2. YAML config file (config.yml)
    3. .env file
    4. Default values
"""

import os
from abc import ABC
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, PlainSerializer
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

__all__ = [
    "BaseConfigModel",
    "ConfigLoaderCollector",
    "ConfigLoaderOAEV",
    "HttpUrlToString",
    "LogLevelToLower",
    "SettingsLoader",
    "TimedeltaInSeconds",
]


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


class SettingsLoader(BaseSettings):
    """Base settings class with prioritized multi-source loading.

    Automatically discovers and loads configuration from environment
    variables, YAML files, and .env files with a defined priority order.

    Subclass this to define your connector's configuration schema.

    Example:
        >>> class MySettings(SettingsLoader):
        ...     model_config = SettingsConfigDict(yaml_file="config.yml")
        ...     api_url: str
        ...     timeout: int = 30
    """

    model_config = SettingsConfigDict(
        frozen=True,
        extra="allow",
        env_nested_delimiter="_",
        env_nested_max_split=1,
        enable_decoding=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Configure source resolution order.

        Resolution priority:
            1. Environment variables (always checked first)
            2. YAML file (if config.yml exists)
            3. .env file (if .env exists and no YAML found)
            4. Default values (implicit via Pydantic)

        Args:
            settings_cls: The settings class being configured.
            init_settings: Init-based settings source.
            env_settings: Environment variable source.
            dotenv_settings: .env file source.
            file_secret_settings: Secrets file source.

        Returns:
            Tuple of settings sources in priority order.
        """
        _main_path = os.curdir

        settings_cls.model_config["env_file"] = f"{_main_path}/../.env"

        if not settings_cls.model_config["yaml_file"]:
            if Path(f"{_main_path}/config.yml").is_file():
                settings_cls.model_config["yaml_file"] = f"{_main_path}/config.yml"
            if Path(f"{_main_path}/../config.yml").is_file():
                settings_cls.model_config["yaml_file"] = f"{_main_path}/../config.yml"

        if Path(settings_cls.model_config["yaml_file"] or "").is_file():  # type: ignore
            return (
                env_settings,
                YamlConfigSettingsSource(settings_cls),
            )
        if Path(settings_cls.model_config["env_file"] or "").is_file():  # type: ignore
            return (
                env_settings,
                DotEnvSettingsSource(settings_cls),
            )
        return (env_settings,)


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
        "Used in multi-tenant environments to scope API requests.",
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
    name: str = Field(description="Name of the collector.")
    log_level: LogLevelToLower | None = Field(
        default="error",
        description="Determines the verbosity of the logs.",
    )
    period: timedelta | None = Field(
        default=timedelta(minutes=1),
        description="Duration between two scheduled runs (ISO 8601 format).",
    )
    icon_filepath: str | None = Field(
        description="Path to the icon file of the collector.",
    )
