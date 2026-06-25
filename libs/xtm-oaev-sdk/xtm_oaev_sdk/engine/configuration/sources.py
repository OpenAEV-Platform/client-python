"""Configuration value sources: environment variables and dictionaries.

Provides abstractions for resolving configuration values from different
backing stores without coupling the Configuration class to specific I/O.
"""

import os
from typing import Any

__all__ = ["DictionarySource", "EnvironmentSource"]


class EnvironmentSource:
    """Resolves configuration values from environment variables.

    Example:
        >>> EnvironmentSource.get("HOME")
        '/home/user'
        >>> EnvironmentSource.get(None) is None
        True
    """

    @classmethod
    def get(cls, env_var: str | None) -> str | None:
        """Get the value of an environment variable.

        Args:
            env_var: Name of the environment variable to read.
                Returns None if env_var is None or empty.

        Returns:
            The environment variable value, or None if not set.
        """
        return os.getenv(env_var) if env_var else None


class DictionarySource:
    """Resolves configuration values from nested dictionary structures.

    Handles two-level key paths into a JSON-like configuration dict,
    typically loaded from a YAML or JSON config file.

    Example:
        >>> source = {"opencti": {"url": "http://localhost:8080"}}
        >>> DictionarySource.get(["opencti", "url"], source)
        'http://localhost:8080'
    """

    @classmethod
    def get(cls, config_key_path: list[str] | None, source_dict: dict[str, Any]) -> str | None:
        """Get a value from a nested dict using a two-level key path.

        Args:
            config_key_path: A list of exactly 2 non-empty strings representing
                the path ``[section, key]`` into the source dict.
            source_dict: The nested dictionary to search.

        Returns:
            The value at the specified path, or None if not found.

        Raises:
            AssertionError: If config_key_path is not a 2-element list of
                non-empty strings.
        """
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
