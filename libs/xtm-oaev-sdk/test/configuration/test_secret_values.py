"""Tests for the secret values of a configuration: what must never be written out.

Feature: Secret values of a configuration
  A connector running without the platform writes what it would have sent, and its
  tools' raw output, to local files. The values its configuration holds as secrets
  are listed so they can be redacted from everything written.
"""

from pathlib import Path
from typing import Any

import xtm_oaev_sdk as sdk
from pydantic import BaseModel, SecretStr


class _Splunk(BaseModel):
    password: SecretStr
    username: str


class _Settings(BaseModel):
    splunk: _Splunk


def _given_configuration(tmp_path: Path, **kwargs: Any) -> sdk.Configuration:
    """Given a connector configuration with:
    | key                       | value          |
    | openaev_token             | platform-token |
    | shodan_api_key            | shodan-key-1   |
    | crowdstrike_client_secret | cs-secret-1    |
    | crowdstrike_client_id     | client-id-1    |
    | collector_period          | 60             |
    | splunk_token              | (unset)        |
    | nuclei_api_key            | abc            |
    """
    return sdk.Configuration(
        config_hints={
            "openaev_token": {"data": "platform-token"},
            "shodan_api_key": {"data": "shodan-key-1"},
            "crowdstrike_client_secret": {"data": "cs-secret-1"},
            "crowdstrike_client_id": {"data": "client-id-1"},
            "collector_period": {"data": 60, "is_number": True},
            "splunk_token": {"data": None},
            "nuclei_api_key": {"data": "abc"},
        },
        config_file_path=str(tmp_path / "missing.yml"),
        **kwargs,
    )


def _given_settings_model() -> _Settings:
    """Given a settings model holding a nested Splunk password "spl-pass-1" and
    username "admin" """
    return _Settings(splunk=_Splunk(password="spl-pass-1", username="admin"))


def _when_listing_secret_values(configuration: sdk.Configuration) -> list[str]:
    """When the configuration lists its secret values"""
    return configuration.secret_values()


def _then_secrets_are(secrets: list[str], *expected: str) -> None:
    """Then the secret values are exactly "<expected>" """
    assert set(secrets) == set(expected)


def _then_secrets_include(secrets: list[str], value: str) -> None:
    """Then "<value>" is a secret value"""
    assert value in secrets


def _then_secrets_exclude(secrets: list[str], value: str) -> None:
    """Then "<value>" is not a secret value"""
    assert value not in secrets


def _then_longest_secrets_come_first(secrets: list[str]) -> None:
    """Then the secret values come longest first"""
    lengths = [len(secret) for secret in secrets]
    assert lengths == sorted(lengths, reverse=True)


def test_values_of_secret_keys_are_secret(tmp_path: Path) -> None:
    """It lists the values of the keys whose name says they hold a secret.

    Scenario: Values of secret keys are secret
      Given a connector configuration
      When the configuration lists its secret values
      Then the secret values are exactly "platform-token", "shodan-key-1" and "cs-secret-1"
    """
    configuration = _given_configuration(tmp_path)
    secrets = _when_listing_secret_values(configuration)
    _then_secrets_are(secrets, "platform-token", "shodan-key-1", "cs-secret-1")


def test_secret_fields_of_the_settings_model_are_secret(tmp_path: Path) -> None:
    """It lists every SecretStr of the settings model, however deep, and nothing else.

    Scenario: Secret fields of the settings model are secret
      Given a settings model holding a nested Splunk password and username
      And a connector configuration built on that settings model
      When the configuration lists its secret values
      Then "spl-pass-1" is a secret value
      And "admin" is not a secret value
    """
    settings = _given_settings_model()
    configuration = _given_configuration(tmp_path, config_base_model=settings)
    secrets = _when_listing_secret_values(configuration)
    _then_secrets_include(secrets, "spl-pass-1")
    _then_secrets_exclude(secrets, "admin")


def test_longest_secrets_come_first(tmp_path: Path) -> None:
    """It lists the longest secrets first, so one containing another is redacted whole.

    Scenario: Longest secrets come first
      Given a connector configuration
      When the configuration lists its secret values
      Then the secret values come longest first
    """
    configuration = _given_configuration(tmp_path)
    secrets = _when_listing_secret_values(configuration)
    _then_longest_secrets_come_first(secrets)


# ---- Constraints identified ----


def test_values_too_short_to_be_secret_are_left_out(tmp_path: Path) -> None:
    """It leaves out values shorter than 4 characters, which would redact plain words.

    Scenario: Values too short to be secret are left out
      Given a connector configuration
      When the configuration lists its secret values
      Then "abc" is not a secret value
    """
    configuration = _given_configuration(tmp_path)
    secrets = _when_listing_secret_values(configuration)
    _then_secrets_exclude(secrets, "abc")
