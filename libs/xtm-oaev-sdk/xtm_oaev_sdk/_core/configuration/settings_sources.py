"""Settings sources: environment variables first, then the YAML or .env file.

In dev mode, a last source fills the platform URL and token the others leave out: a
daemon started with ``--dev`` never reaches the platform, so it must not need them.
"""

import inspect
import os
from pathlib import Path
from typing import Any, Callable

from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
)
from xtm_oaev_sdk.seam.configuration import ConfigLoaderOAEV

__all__ = ["SettingsSourceSelector"]

#: The platform a daemon in dev mode is configured with when nothing names one: an
#: ``.invalid`` host (RFC 2606) can never be reached.
DEV_PLATFORM = {"url": "http://platform.openaev.invalid", "token": "dev-mode"}


def _is_platform(annotation: Any) -> bool:
    return inspect.isclass(annotation) and issubclass(annotation, ConfigLoaderOAEV)


class _DevPlatformSource(PydanticBaseSettingsSource):
    """Lowest priority source: the dev platform, for every platform section."""

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        return {
            name: dict(DEV_PLATFORM)
            for name, field in self.settings_cls.model_fields.items()
            if _is_platform(field.annotation)
        }


class SettingsSourceSelector:
    """Implements ``SettingsSourcesPort``.

    :param dev_enabled: tells whether the daemon runs in dev mode; when it does, the
        platform URL and token are no longer required.
    """

    def __init__(self, dev_enabled: Callable[[], bool] = lambda: False) -> None:
        self._dev_enabled = dev_enabled

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

        sources: tuple[PydanticBaseSettingsSource, ...] = (env_settings,)
        if Path(settings_cls.model_config["yaml_file"] or "").is_file():  # type: ignore
            sources += (YamlConfigSettingsSource(settings_cls),)
        elif Path(settings_cls.model_config["env_file"] or "").is_file():  # type: ignore
            sources += (DotEnvSettingsSource(settings_cls),)
        if self._dev_enabled():
            sources += (_DevPlatformSource(settings_cls),)
        return sources
