import os
from abc import ABC
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, PlainSerializer
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class BaseConfigModel(BaseModel, ABC):
    """Base class for global config models
    To prevent attributes from being modified after initialization.
    """

    model_config = ConfigDict(extra="allow", frozen=True, validate_default=True)


class SettingsLoader(BaseSettings):
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
        """Customise the sources of settings for the connector.

        This method is called by the Pydantic BaseSettings class to determine the order of sources.
        The configuration come in this order either from:
            1. Environment variables
            2. YAML file
            3. .env file
            4. Default values

        The variables loading order will remain the same as in `pycti.get_config_variable()`:
            1. If a config.yml file is found, the order will be: `ENV VAR` → config.yml → default value
            2. If a .env file is found, the order will be: `ENV VAR` → .env → default value
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


LogLevelToLower = Annotated[
    Literal["debug", "info", "warn", "error"],
    PlainSerializer(lambda v: "".join(v), return_type=str),
]

HttpUrlToString = Annotated[HttpUrl, PlainSerializer(str, return_type=str)]
TimedeltaInSeconds = Annotated[
    timedelta, PlainSerializer(lambda v: int(v.total_seconds()), return_type=int)
]


class ConfigLoaderOAEV(BaseConfigModel):
    """OpenAEV/OpenAEV platform configuration settings.

    Contains URL and authentication token for connecting to the OpenAEV platform.
    """

    url: HttpUrlToString = Field(
        description="The OpenAEV platform URL.",
    )
    token: str = Field(
        description="The token for the OpenAEV platform.",
    )


class ConfigLoaderCollector(BaseConfigModel):
    """Base collector configuration settings.

    Contains common collector settings including identification, logging,
    scheduling, and platform information.
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
