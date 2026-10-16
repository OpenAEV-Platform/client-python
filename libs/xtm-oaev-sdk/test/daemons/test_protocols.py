"""Tests for the BaseClient and DaemonProtocol runtime protocols."""

from typing import Any
from unittest.mock import MagicMock

import pytest
import xtm_oaev_sdk as sdk

_CLIENT_METHODS = [
    "http_delete",
    "http_get",
    "http_head",
    "http_list",
    "http_patch",
    "http_post",
    "http_put",
]
_CLIENT_PROPERTIES = [
    "backend",
    "headers",
    "order_by",
    "pagination",
    "per_page",
    "session",
    "ssl_verify",
    "tenant_id",
    "timeout",
    "url",
]
_DAEMON_METHODS = ["get_id", "set_callback", "start"]


def _given_object_with(members: list[str]) -> Any:
    instance = MagicMock(spec=members)
    for name in members:
        setattr(instance, name, MagicMock())
    return instance


def _when_reading_members(protocol: type, *, properties: bool) -> list[str]:
    return sorted(
        name
        for name, value in protocol.__dict__.items()
        if not name.startswith("_")
        and isinstance(value, property) is properties
        and (properties or callable(value))
    )


@pytest.mark.parametrize("protocol", [sdk.BaseClient, sdk.DaemonProtocol])
def test_protocols_are_runtime_checkable(protocol: type) -> None:
    """It allows isinstance checks against the protocol."""
    assert getattr(protocol, "_is_runtime_protocol", False) is True


def test_base_client_declares_the_http_surface() -> None:
    """It declares exactly the HTTP methods and client properties."""
    assert _when_reading_members(sdk.BaseClient, properties=False) == _CLIENT_METHODS
    assert _when_reading_members(sdk.BaseClient, properties=True) == _CLIENT_PROPERTIES


def test_daemon_protocol_declares_the_lifecycle_surface() -> None:
    """It declares exactly the public daemon lifecycle methods."""
    assert _when_reading_members(sdk.DaemonProtocol, properties=False) == (
        _DAEMON_METHODS
    )


@pytest.mark.parametrize(
    ("protocol", "members"),
    [
        (sdk.BaseClient, _CLIENT_METHODS + _CLIENT_PROPERTIES),
        (sdk.DaemonProtocol, _DAEMON_METHODS),
    ],
)
def test_protocols_accept_full_implementations(protocol: type, members) -> None:
    """It accepts an object exposing every member."""
    assert isinstance(_given_object_with(members), protocol)


@pytest.mark.parametrize(
    ("protocol", "members", "missing"),
    [(sdk.BaseClient, _CLIENT_METHODS + _CLIENT_PROPERTIES, m) for m in _CLIENT_METHODS]
    + [(sdk.DaemonProtocol, _DAEMON_METHODS, m) for m in _DAEMON_METHODS],
)
def test_protocols_reject_incomplete_implementations(
    protocol: type, members, missing: str
) -> None:
    """It rejects an object missing a member."""
    incomplete = [m for m in members if m != missing]
    assert not isinstance(_given_object_with(incomplete), protocol)


def test_base_daemon_satisfies_daemon_protocol() -> None:
    """It implements the daemon lifecycle protocol."""

    class _Daemon(sdk.BaseDaemon):
        def _setup(self):
            pass

        def _start_loop(self):
            pass

    daemon = _Daemon(
        configuration=sdk.Configuration(config_hints={}),
        api_client=MagicMock(),
        logger=MagicMock(),
    )
    assert isinstance(daemon, sdk.DaemonProtocol)
