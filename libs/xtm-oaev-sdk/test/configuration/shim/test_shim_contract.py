"""Contract of the pyoaev configuration shims.

Legacy imports must keep working, return the *identical* xtm_oaev_sdk object,
and warn; importing pyoaev itself and using the SDK directly must stay silent.
"""

import subprocess
import sys
import warnings

import pytest
import xtm_oaev_sdk as sdk

LEGACY_NAMES = [
    ("pyoaev", "BaseConfigModel"),
    ("pyoaev", "ConfigLoaderCollector"),
    ("pyoaev", "ConfigLoaderOAEV"),
    ("pyoaev", "Configuration"),
    ("pyoaev", "SettingsLoader"),
    ("pyoaev.configuration", "BaseConfigModel"),
    ("pyoaev.configuration", "ConfigLoaderCollector"),
    ("pyoaev.configuration", "ConfigLoaderOAEV"),
    ("pyoaev.configuration", "Configuration"),
    ("pyoaev.configuration", "SettingsLoader"),
    ("pyoaev.configuration.configuration", "CONFIGURATION_TYPES"),
    ("pyoaev.configuration.configuration", "Configuration"),
    ("pyoaev.configuration.configuration", "ConfigurationHint"),
    ("pyoaev.configuration.configuration", "ConnectorConfigSchemaGenerator"),
    ("pyoaev.configuration.configuration", "DictionarySource"),
    ("pyoaev.configuration.configuration", "EnvironmentSource"),
    ("pyoaev.configuration.configuration", "is_falsy"),
    ("pyoaev.configuration.configuration", "is_truthy"),
    ("pyoaev.configuration.settings_loader", "BaseConfigModel"),
    ("pyoaev.configuration.settings_loader", "ConfigLoaderCollector"),
    ("pyoaev.configuration.settings_loader", "ConfigLoaderOAEV"),
    ("pyoaev.configuration.settings_loader", "HttpUrlToString"),
    ("pyoaev.configuration.settings_loader", "LogLevelToLower"),
    ("pyoaev.configuration.settings_loader", "SettingsLoader"),
    ("pyoaev.configuration.settings_loader", "TimedeltaInSeconds"),
    ("pyoaev.configuration.sources", "DictionarySource"),
    ("pyoaev.configuration.sources", "EnvironmentSource"),
    (
        "pyoaev.configuration.connector_config_schema_generator",
        "ConnectorConfigSchemaGenerator",
    ),
]


def _given_fresh_interpreter_script(script: str) -> list[str]:
    return [sys.executable, "-W", "error::DeprecationWarning", "-c", script]


def _when_run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True)


def _when_import_legacy_name(module: str, name: str):
    namespace: dict = {}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exec(f"from {module} import {name} as _legacy", namespace)
    return namespace["_legacy"], caught


def _then_succeeds(result: subprocess.CompletedProcess) -> None:
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(("module", "name"), LEGACY_NAMES)
def test_legacy_import_warns_and_returns_the_sdk_object(module, name) -> None:
    """It warns towards xtm_oaev_sdk and returns the identical object."""
    legacy, caught = _when_import_legacy_name(module, name)
    assert legacy is getattr(sdk, name)
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert deprecations
    assert f"from xtm_oaev_sdk import {name}" in str(deprecations[0].message)


def test_importing_pyoaev_is_silent() -> None:
    """It imports pyoaev without any DeprecationWarning."""
    result = _when_run(_given_fresh_interpreter_script("import pyoaev"))
    _then_succeeds(result)


def test_sdk_classes_stay_silent_once_pyoaev_is_loaded() -> None:
    """It never alters SDK objects: native use stays silent next to pyoaev."""
    script = (
        "import pyoaev, pyoaev.configuration.configuration\n"
        "import xtm_oaev_sdk as sdk\n"
        "sdk.Configuration(config_hints={})\n"
        "sdk.EnvironmentSource()\n"
        "class _C(sdk.BaseConfigModel):\n"
        "    pass\n"
        "_C()\n"
    )
    result = _when_run(_given_fresh_interpreter_script(script))
    _then_succeeds(result)


def test_unknown_legacy_name_still_raises() -> None:
    """It does not swallow genuine misses."""
    import pyoaev.configuration

    with pytest.raises(AttributeError):
        pyoaev.configuration.DoesNotExist
