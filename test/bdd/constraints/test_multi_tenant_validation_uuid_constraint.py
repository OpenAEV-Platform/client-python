"""Tenant ID handling in OpenAEV configuration feature tests."""

from uuid import UUID

import pytest
from pydantic import ValidationError
from pytest_bdd import given, parsers, scenario, then, when

from pyoaev.configuration.settings_loader import ConfigLoaderOAEV

# --------------------------------------------------
# SCENARIOS
# --------------------------------------------------


@scenario(
    "multi_tenant_validation_uuid_constraint.feature",
    "tenant_id is a valid UUID",
)
def test_tenant_id_is_a_valid_uuid():
    pass


@scenario(
    "multi_tenant_validation_uuid_constraint.feature",
    "tenant_id is explicitly set to None",
)
def test_tenant_id_is_explicitly_set_to_none():
    pass


@scenario(
    "multi_tenant_validation_uuid_constraint.feature",
    "tenant_id is invalid and should raise a validation error",
)
def test_tenant_id_is_invalid_and_should_raise_a_validation_error():
    pass


@scenario(
    "multi_tenant_validation_uuid_constraint.feature",
    "tenant_id is not provided",
)
def test_tenant_id_is_not_provided():
    pass


# --------------------------------------------------
# GIVEN
# --------------------------------------------------


@given(
    "a configuration without tenant_id",
    target_fixture="config",
)
def config_without():
    return {
        "url": "https://example.com",
        "token": "token",
    }


@given(
    "a configuration with tenant_id set to None",
    target_fixture="config",
)
def config_none():
    return {
        "url": "https://example.com",
        "token": "token",
        "tenant_id": None,
    }


@given(
    parsers.parse('a configuration with tenant_id "{tenant_id}" invalid'),
    target_fixture="config",
)
def config_with_tenant_invalid(tenant_id):
    return {
        "url": "https://example.com",
        "token": "token",
        "tenant_id": tenant_id,
    }


@given(
    'a configuration with tenant_id "2cffad3a-0001-4078-b0e2-ef74274022c3"',
    target_fixture="config",
)
def config_with_tenant_valid():
    return {
        "url": "https://example.com",
        "token": "token",
        "tenant_id": "2cffad3a-0001-4078-b0e2-ef74274022c3",
    }


# --------------------------------------------------
# WHEN
# --------------------------------------------------


@when(
    "the configuration is loaded",
    target_fixture="result",
)
def load_config(config):
    try:
        return ConfigLoaderOAEV(**config)
    except ValidationError as err:
        return err


# --------------------------------------------------
# THEN
# --------------------------------------------------


@then("tenant_id should be None")
def assert_none(result):
    assert result.tenant_id is None


@then("tenant_id should be a valid UUID")
def assert_uuid(result):
    assert isinstance(result.tenant_id, UUID)


@then("a validation error should be raised")
def assert_validation_error(result):
    assert isinstance(result, ValidationError)
