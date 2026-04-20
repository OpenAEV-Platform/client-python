from unittest.mock import MagicMock
from uuid import UUID

import pytest

from pyoaev.daemons.base_daemon import BaseDaemon


class DummyDaemon(BaseDaemon):
    def _setup(self):
        pass

    def _start_loop(self):
        pass


@pytest.mark.parametrize(
    "config_map, expected_tenant",
    [
        (
            {
                "openaev_url": "url",
                "openaev_token": "token",
            },
            None,
        ),
        (
            {
                "openaev_url": "url",
                "openaev_token": "token",
                "openaev_tenant_id": None,
            },
            None,
        ),
        (
            {
                "openaev_url": "url",
                "openaev_token": "token",
                "openaev_tenant_id": UUID("2cffad3a-0001-4078-b0e2-ef74274022c3"),
            },
            UUID("2cffad3a-0001-4078-b0e2-ef74274022c3"),
        ),
    ],
    ids=[
        "missing_tenant_key",
        "explicit_none_tenant",
        "valid_uuid_tenant",
    ],
)
def test_default_api_client_propagates_tenant_id(
    monkeypatch, config_map, expected_tenant
):
    captured = {}

    def fake_client(url, token, tenant_id=None):
        captured["url"] = url
        captured["token"] = token
        captured["tenant_id"] = tenant_id
        return MagicMock()

    monkeypatch.setattr("pyoaev.daemons.base_daemon.OpenAEV", fake_client)

    config = MagicMock()
    config.get.side_effect = lambda key: config_map.get(key)

    daemon = DummyDaemon(configuration=config)
    assert daemon.api is not None

    assert "openaev_tenant_id" in config_map or expected_tenant is None
    assert captured["url"] == "url"
    assert captured["token"] == "token"
    assert captured["tenant_id"] == expected_tenant
