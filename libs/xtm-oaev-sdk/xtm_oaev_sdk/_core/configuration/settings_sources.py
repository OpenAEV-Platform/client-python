"""Settings sources: environment variables first, then the YAML or .env file."""

import os
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
)

__all__ = ["SettingsSourceSelector"]


class SettingsSourceSelector:
    """Implements ``SettingsSourcesPort``."""

    def select_sources(
        self,
        settings_cls: type[BaseSettings],
        env_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
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
