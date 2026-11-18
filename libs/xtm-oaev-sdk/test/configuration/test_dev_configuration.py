"""Tests for loading a daemon configuration in dev mode.

Feature: Configuration in dev mode
  A daemon started with --dev never reaches the platform, so its configuration must
  load without the platform URL and token. Whatever the configuration gives still wins;
  without --dev, the platform URL and token stay required.
"""

import sys
from pathlib import Path
from typing import Any, NamedTuple

import pytest
import xtm_oaev_sdk as sdk
from pydantic import Field, ValidationError
from pydantic_settings import SettingsConfigDict

PROGRAM = "openaev-shodan"
PLATFORM_ENV = ("OPENAEV_URL", "OPENAEV_TOKEN", "OPENAEV_TENANT_ID")


class Loading(NamedTuple):
    settings: Any
    error: ValidationError | None


class _ShodanSettings(sdk.SettingsLoader):
    model_config = SettingsConfigDict(env_nested_delimiter="_", env_nested_max_split=1)

    openaev: sdk.ConfigLoaderOAEV = Field(default_factory=sdk.ConfigLoaderOAEV)
    shodan_api_key: str = "dev-key"


def _given_no_platform_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Given no configuration file nor environment variable names the platform"""
    work = tmp_path / "injector"
    work.mkdir()
    monkeypatch.chdir(work)
    for name in PLATFORM_ENV:
        monkeypatch.delenv(name, raising=False)


def _given_platform_url_in_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Given the environment names the platform "https://openaev.example" """
    monkeypatch.setenv("OPENAEV_URL", "https://openaev.example")
    monkeypatch.setenv("OPENAEV_TOKEN", "real-token")


def _given_process_command_line(monkeypatch: pytest.MonkeyPatch, *args: str) -> None:
    """Given the process command line contains "<args>" """
    monkeypatch.setattr(sys, "argv", [PROGRAM, *args])


def _when_loading_settings() -> Loading:
    """When the daemon loads its settings"""
    try:
        return Loading(_ShodanSettings(), None)
    except ValidationError as error:
        return Loading(None, error)


def _then_settings_load(loading: Loading) -> None:
    """Then the settings load"""
    assert loading.error is None, f"Expected the settings to load: {loading.error}"


def _then_settings_are_refused_for(loading: Loading, *fields: str) -> None:
    """Then the settings are refused for missing <fields>"""
    assert loading.error is not None, "Expected the settings to be refused"
    failing = {str(error["loc"][-1]) for error in loading.error.errors()}
    assert set(fields) <= failing, f"Expected {fields} to fail, got {failing}"


def _then_platform_is(loading: Loading, url: str, token: str) -> None:
    """Then the platform is <url> with the token <token>"""
    assert (str(loading.settings.openaev.url), loading.settings.openaev.token) == (
        url,
        token,
    )


def _then_platform_is_a_placeholder_never_reached(loading: Loading) -> None:
    """Then the platform URL is a placeholder that can never be reached"""
    host = loading.settings.openaev.url.host
    assert host.endswith(".invalid"), f"Expected an .invalid host, got {host}"
    assert loading.settings.openaev.token


def test_configuration_loads_without_platform_keys_under_dev(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """It loads the settings without the platform URL and token under --dev.

    Scenario: The configuration loads without platform keys under --dev
      Given no configuration file nor environment variable names the platform
      And the process command line contains "--dev"
      When the daemon loads its settings
      Then the settings load
      And the platform URL is a placeholder that can never be reached
    """
    _given_no_platform_configuration(monkeypatch, tmp_path)
    _given_process_command_line(monkeypatch, "--dev")
    loading = _when_loading_settings()
    _then_settings_load(loading)
    _then_platform_is_a_placeholder_never_reached(loading)


def test_configured_platform_keys_still_win_under_dev(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """It keeps the platform URL and token the configuration gives, dev or not.

    Scenario: Configured platform keys still win under --dev
      Given no configuration file nor environment variable names the platform
      And the environment names the platform "https://openaev.example"
      And the process command line contains "--dev"
      When the daemon loads its settings
      Then the platform is "https://openaev.example/" with the token "real-token"
    """
    _given_no_platform_configuration(monkeypatch, tmp_path)
    _given_platform_url_in_environment(monkeypatch)
    _given_process_command_line(monkeypatch, "--dev")
    loading = _when_loading_settings()
    _then_platform_is(loading, "https://openaev.example/", "real-token")


# ---- Constraints identified ----


def test_platform_keys_stay_required_without_dev(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """It still requires the platform URL and token without --dev.

    Scenario: Platform keys stay required without --dev
      Given no configuration file nor environment variable names the platform
      And the process command line contains "--once"
      When the daemon loads its settings
      Then the settings are refused for missing "url" and "token"
    """
    _given_no_platform_configuration(monkeypatch, tmp_path)
    _given_process_command_line(monkeypatch, "--once")
    loading = _when_loading_settings()
    _then_settings_are_refused_for(loading, "url", "token")
