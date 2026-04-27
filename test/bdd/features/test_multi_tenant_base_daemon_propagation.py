from unittest.mock import MagicMock
from uuid import UUID

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from pyoaev.daemons.base_daemon import BaseDaemon

# --------------------------------------------------
# SCENARIO
# --------------------------------------------------


@scenario(
    "multi_tenant_base_daemon_propagation.feature",
    "BaseDaemon propagates tenant_id correctly from configuration",
)
def test_base_daemon_propagates_tenant_id():
    pass


# --------------------------------------------------
# FIXTURE CONTEXT
# --------------------------------------------------


@pytest.fixture
def context():
    return {}


# --------------------------------------------------
# HELPERS
# --------------------------------------------------


def build_config(tenant_case):
    base = {
        "openaev_url": "url",
        "openaev_token": "token",
    }

    if tenant_case == "missing_key":
        return base

    if tenant_case == "explicit_none":
        base["openaev_tenant_id"] = None
        return base

    if tenant_case == "valid_uuid":
        base["openaev_tenant_id"] = UUID("2cffad3a-0001-4078-b0e2-ef74274022c3")
        return base
    return base


# --------------------------------------------------
# GIVEN
# --------------------------------------------------


@given(parsers.parse('a daemon configuration with "{tenant_case}"'))
def daemon_config(context, monkeypatch, tenant_case):
    captured = build_config(tenant_case)

    def fake_client(url, token, tenant_id=None):
        captured["url"] = url
        captured["token"] = token
        captured["tenant_id"] = tenant_id
        return MagicMock()

    monkeypatch.setattr("pyoaev.daemons.base_daemon.OpenAEV", fake_client)

    config = MagicMock()
    config_map = build_config(tenant_case)
    config.get.side_effect = lambda key: config_map.get(key)

    context["config"] = config
    context["captured"] = captured


# --------------------------------------------------
# WHEN
# --------------------------------------------------


@when("the BaseDaemon is initialized")
def init_daemon(context):
    class DummyDaemon(BaseDaemon):
        def _setup(self):
            pass

        def _start_loop(self):
            pass

    context["daemon"] = DummyDaemon(configuration=context["config"])


# --------------------------------------------------
# THEN
# --------------------------------------------------


@then(
    parsers.parse(
        'the API client should be created with tenant_id "{expected_tenant_id}"'
    )
)
def check_tenant(context, expected_tenant_id):
    captured = context["captured"]

    daemon = context["daemon"]
    assert daemon.api is not None

    expected = None if expected_tenant_id == "None" else UUID(expected_tenant_id)
    assert captured["url"] == "url"
    assert captured["token"] == "token"
    assert captured["tenant_id"] == expected
