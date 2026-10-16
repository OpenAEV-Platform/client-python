"""Contract of the pyoaev daemon runtime shims.

``PingAlive`` resolves to the *identical* xtm_oaev_sdk object. ``BaseDaemon``
resolves to a subclass that keeps building the OpenAEV client when none is
injected. Both warn, attributed to the consumer's line.
"""

import subprocess
import sys
import warnings
from unittest.mock import MagicMock, patch

import pytest
import xtm_oaev_sdk as sdk

_CONSUMER = "legacy_consumer.py"


def _when_import_legacy_name(module: str, name: str):
    namespace: dict = {}
    source = f"from {module} import {name} as _legacy"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exec(compile(source, _CONSUMER, "exec"), namespace)
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    return namespace["_legacy"], deprecations


def _then_warns_at_consumer(deprecations, sdk_name: str) -> None:
    assert deprecations
    assert f"from xtm_oaev_sdk import {sdk_name}" in str(deprecations[0].message)
    assert any(w.filename == _CONSUMER for w in deprecations)


@pytest.mark.parametrize("module", ["pyoaev.utils"])
def test_legacy_ping_alive_is_the_sdk_object(module: str) -> None:
    """It warns and returns the identical PingAlive."""
    legacy, deprecations = _when_import_legacy_name(module, "PingAlive")
    assert legacy is sdk.PingAlive
    _then_warns_at_consumer(deprecations, "PingAlive")


@pytest.mark.parametrize("module", ["pyoaev.daemons", "pyoaev.daemons.base_daemon"])
def test_legacy_base_daemon_builds_the_openaev_client(module: str) -> None:
    """It warns and still builds the OpenAEV client from configuration."""
    legacy, deprecations = _when_import_legacy_name(module, "BaseDaemon")
    _then_warns_at_consumer(deprecations, "BaseDaemon")
    assert issubclass(legacy, sdk.BaseDaemon)

    class _Daemon(legacy):
        def _setup(self):
            pass

        def _start_loop(self):
            pass

    configuration = sdk.Configuration(
        config_hints={
            "openaev_url": {"data": "http://example.com"},
            "openaev_token": {"data": "token"},
            "openaev_tenant_id": {"data": "tenant"},
        }
    )
    with patch("pyoaev.daemons.base_daemon.OpenAEV") as client_class:
        daemon = _Daemon(configuration=configuration, logger=MagicMock())

    client_class.assert_called_once_with(
        url="http://example.com", token="token", tenant_id="tenant"
    )
    assert daemon.api is client_class.return_value


def test_legacy_collector_daemon_is_still_a_legacy_base_daemon() -> None:
    """It keeps the legacy class hierarchy."""
    from pyoaev.daemons import CollectorDaemon

    legacy_base, _ = _when_import_legacy_name("pyoaev.daemons", "BaseDaemon")
    assert issubclass(CollectorDaemon, legacy_base)


def test_openaev_client_satisfies_base_client() -> None:
    """It accepts the real pyoaev client as an injected API client."""
    from pyoaev import OpenAEV

    assert isinstance(OpenAEV(url="http://example.com", token="t"), sdk.BaseClient)


def test_importing_pyoaev_daemon_modules_is_silent() -> None:
    """It imports the daemon runtime modules without any warning."""
    script = (
        "import pyoaev, pyoaev.daemons, pyoaev.daemons.base_daemon\n"
        "import pyoaev.daemons.collector_daemon, pyoaev.helpers, pyoaev.utils\n"
    )
    result = subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
