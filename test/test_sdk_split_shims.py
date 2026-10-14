"""Contract of the pyoaev shims toward collectors-sdk and injectors-sdk.

Legacy imports and patch targets of collectors and injectors must keep working:
names resolve to the *identical* SDK object, or to a thin subclass that keeps
building the OpenAEV client, and warn at the consumer's line.
"""

import subprocess
import sys
import warnings
from unittest.mock import MagicMock, mock_open, patch

import collectors_sdk
import injectors_sdk
import pytest
import xtm_oaev_sdk

_CONSUMER = "legacy_consumer.py"

IDENTICAL = [
    ("pyoaev.helpers", "OpenAEVDetectionHelper", collectors_sdk),
    ("pyoaev.helpers", "ListenQueue", injectors_sdk),
    ("pyoaev.helpers", "OpenAEVConfigHelper", injectors_sdk),
    ("pyoaev.helpers", "create_mq_ssl_context", injectors_sdk),
    ("pyoaev.helpers", "PingAlive", xtm_oaev_sdk),
    ("pyoaev.helpers", "Configuration", xtm_oaev_sdk),
    ("pyoaev.helpers", "ConfigurationError", xtm_oaev_sdk),
    ("pyoaev.helpers", "logger", xtm_oaev_sdk),
    ("pyoaev.daemons.collector_daemon", "DEFAULT_PERIOD_SECONDS", collectors_sdk),
    ("pyoaev.daemons.collector_daemon", "DEFAULT_PLATFORM_TAG_COLOR", collectors_sdk),
    ("pyoaev.apis.inject_expectation.model", "DetectionExpectation", collectors_sdk),
    ("pyoaev.apis.inject_expectation.model", "PreventionExpectation", collectors_sdk),
    ("pyoaev.apis.inject_expectation.model", "ExpectationTypeEnum", collectors_sdk),
    ("pyoaev.apis.inject_expectation.model", "Expectation", collectors_sdk),
    ("pyoaev.apis.inject_expectation.model.expectation", "Expectation", collectors_sdk),
    (
        "pyoaev.apis.inject_expectation.model.expectation",
        "ExpectationSignature",
        collectors_sdk,
    ),
    *[
        (module, name, collectors_sdk)
        for module in (
            "pyoaev.apis.inject_expectation",
            "pyoaev.apis.inject_expectation.inject_expectation",
        )
        for name in (
            "DetectionExpectation",
            "ExpectationTypeEnum",
            "PreventionExpectation",
        )
    ],
]


def _when_import_legacy_name(module: str, name: str):
    namespace: dict = {}
    source = f"from {module} import {name} as _legacy"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exec(compile(source, _CONSUMER, "exec"), namespace)
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    return namespace["_legacy"], deprecations


def _then_warns_at_consumer(deprecations) -> None:
    assert deprecations
    assert any(w.filename == _CONSUMER for w in deprecations)


@pytest.mark.parametrize(("module", "name", "sdk"), IDENTICAL)
def test_legacy_name_is_the_sdk_object(module, name, sdk) -> None:
    """It warns and returns the identical SDK object."""
    legacy, deprecations = _when_import_legacy_name(module, name)
    assert legacy is getattr(sdk, name)
    _then_warns_at_consumer(deprecations)
    assert sdk.__name__ in str(deprecations[0].message)


@pytest.mark.parametrize(
    "module", ["pyoaev.daemons", "pyoaev.daemons.collector_daemon", "pyoaev.helpers"]
)
def test_legacy_collector_daemon_is_one_client_building_subclass(module) -> None:
    """It resolves every path to the same class, so class patches still apply."""
    from pyoaev.daemons.collector_daemon import _ClientCollectorDaemon

    legacy, deprecations = _when_import_legacy_name(module, "CollectorDaemon")
    _then_warns_at_consumer(deprecations)
    assert legacy is _ClientCollectorDaemon
    assert issubclass(legacy, collectors_sdk.CollectorDaemon)


@patch("pyoaev.apis.DocumentManager.upsert", return_value={})
@patch("pyoaev.apis.CollectorManager.create", return_value={})
@patch("builtins.open", new_callable=mock_open, read_data="data")
@patch("pyoaev.utils.PingAlive.start")
def test_legacy_collector_daemon_builds_the_openaev_client(*_) -> None:
    """It still works with only a configuration, as legacy collectors use it."""
    from pyoaev.client import OpenAEV
    from pyoaev.configuration import Configuration
    from pyoaev.daemons import CollectorDaemon

    config = Configuration(
        config_hints={
            "openaev_url": {"data": "http://example.com"},
            "openaev_token": {"data": "token"},
            "collector_id": {"data": "collector-id"},
        }
    )
    collector = CollectorDaemon(configuration=config, collector_type="test")

    assert isinstance(collector.api, OpenAEV)
    collector._setup()


def test_legacy_collector_daemon_setup_patch_target_still_applies() -> None:
    """It honours patches on pyoaev.daemons.collector_daemon.CollectorDaemon._setup."""
    from pyoaev.daemons import CollectorDaemon

    with patch("pyoaev.daemons.collector_daemon.CollectorDaemon._setup") as setup:
        collector = CollectorDaemon(
            configuration=xtm_oaev_sdk.Configuration(config_hints={}),
            api_client=MagicMock(),
            collector_type="test",
        )
        collector._setup()

    setup.assert_called_once()


@patch("xtm_oaev_sdk.PingAlive.start")
def test_legacy_injector_helper_builds_the_openaev_client(_) -> None:
    """It still builds the client from the config helper when none is injected."""
    from pyoaev.helpers import OpenAEVConfigHelper, OpenAEVInjectorHelper

    config = OpenAEVConfigHelper.from_configuration_object(
        xtm_oaev_sdk.Configuration(
            config_hints={
                "openaev_url": {"data": "http://example.com"},
                "openaev_token": {"data": "token"},
                "openaev_tenant_id": {"data": "tenant"},
                "injector_type": {"data": "openaev_test"},
                "injector_log_level": {"data": "info"},
            }
        )
    )
    with patch("pyoaev.helpers.OpenAEV") as client_class:
        helper = OpenAEVInjectorHelper(config, MagicMock())

    client_class.assert_called_once_with(
        url="http://example.com", token="token", tenant_id="tenant"
    )
    assert helper.api is client_class.return_value
    assert isinstance(helper, injectors_sdk.OpenAEVInjectorHelper)


@pytest.mark.parametrize(
    ("name", "value"),
    [("TRUTHY", ["yes", "true", "True"]), ("FALSY", ["no", "false", "False"])],
)
def test_legacy_truthiness_constants_keep_their_value(name, value) -> None:
    """It keeps the unused legacy constants available, with a warning."""
    legacy, deprecations = _when_import_legacy_name("pyoaev.helpers", name)
    assert legacy == value
    _then_warns_at_consumer(deprecations)


def test_legacy_collector_helper_still_resolves() -> None:
    """It keeps the already deprecated OpenAEVCollectorHelper available."""
    legacy, deprecations = _when_import_legacy_name(
        "pyoaev.helpers", "OpenAEVCollectorHelper"
    )
    _then_warns_at_consumer(deprecations)
    assert callable(legacy)


def _given_expectation_manager():
    from pyoaev.apis import InjectExpectationManager

    manager = InjectExpectationManager(MagicMock())
    manager.expectations_assets_for_source = MagicMock(
        return_value=[
            {
                "inject_expectation_id": "4a1bb2c4-6a59-4b4b-a3c0-0d36a4f8e1c1",
                "inject_expectation_type": "DETECTION",
                "inject_expectation_signatures": [],
            }
        ]
    )
    return manager


def _when_call_legacy_models_for_source(manager, **kwargs):
    namespace: dict = {"manager": manager, "kwargs": kwargs}
    source = "_result = manager.expectations_models_for_source(**kwargs)"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exec(compile(source, _CONSUMER, "exec"), namespace)
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    return namespace["_result"], deprecations


def test_expectation_manager_builds_sdk_models() -> None:
    """It still hands out collectors-sdk expectation models, with a warning."""
    manager = _given_expectation_manager()

    (model,), deprecations = _when_call_legacy_models_for_source(
        manager, source_id="collector"
    )

    assert isinstance(model, collectors_sdk.DetectionExpectation)
    _then_warns_at_consumer(deprecations)
    assert "from collectors_sdk import expectations_models_for_source" in str(
        deprecations[0].message
    )


def test_expectation_manager_delegates_to_collectors_sdk() -> None:
    """It builds nothing itself: collectors-sdk builds the models from the manager."""
    manager = _given_expectation_manager()
    sentinel = [object()]

    with patch.object(
        collectors_sdk, "expectations_models_for_source", return_value=sentinel
    ) as builder:
        result, _ = _when_call_legacy_models_for_source(
            manager, source_id="collector", expiration_time=5
        )

    builder.assert_called_once_with(manager, "collector", expiration_time=5)
    assert result is sentinel


def test_importing_pyoaev_modules_is_silent() -> None:
    """It imports pyoaev and its shim modules without any warning."""
    script = (
        "import pyoaev, pyoaev.helpers, pyoaev.daemons, pyoaev.daemons.collector_daemon\n"
        "import pyoaev.apis, pyoaev.apis.inject_expectation.model\n"
        "import pyoaev.apis.inject_expectation.model.expectation\n"
    )
    result = subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
