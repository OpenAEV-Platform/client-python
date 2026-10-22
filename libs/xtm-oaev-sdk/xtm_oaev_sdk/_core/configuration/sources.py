"""Configuration sources: environment variables and nested dictionaries."""

import os
from typing import Any

__all__ = ["ConfigurationSources"]


class ConfigurationSources:
    """Implements ``ConfigurationSourcesPort``."""

    def from_environment(self, env_var: str | None) -> str | None:
        return os.getenv(env_var) if env_var else None

    # this is quite hacky
    # it only strictly handles two levels of keys in a dict
    def from_dictionary(
        self, config_key_path: list[str] | None, source_dict: dict[str, Any]
    ) -> str | None:
        if config_key_path is None:
            return None

        assert (
            isinstance(config_key_path, list)
            and len(config_key_path) == 2
            and all([len(path_part) > 0 for path_part in config_key_path])
        )

        return source_dict.get(config_key_path[0], {config_key_path[1]: None}).get(
            config_key_path[1]
        )
