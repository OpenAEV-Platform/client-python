"""Contract of the pyoaev signatures shims.

Legacy imports must keep working and warn. They return the *identical*
xtm_oaev_sdk object, except for the renamed ``ExpectationType`` (now
``SignatureExpectationType``) and ``SignatureManager``, which resolves to a
subclass keeping the client-based constructor.
"""

import subprocess
import sys
import warnings
from unittest.mock import MagicMock

import pytest
import xtm_oaev_sdk as sdk

_CONSUMER = "legacy_consumer.py"
_RENAMED = {"ExpectationType": "SignatureExpectationType"}

_PACKAGE = [
    "CloudInjectorConfig",
    "ExpectationSignatureGroup",
    "ExpectationType",
    "ExtraSignatureData",
    "InjectorConfig",
    "InjectExecutionActions",
    "MatchTypes",
    "NetworkInjectorConfig",
    "SignatureCallbackPayload",
    "SignaturePayload",
    "SignatureTarget",
    "SignatureTypes",
    "SignatureValue",
    "TargetSignatures",
    "build_network_configs",
]
_MODELS = [
    "SignatureValue",
    "ExpectationSignatureGroup",
    "SignatureTarget",
    "TargetSignatures",
    "SignaturePayload",
    "SignatureCallbackPayload",
    "ExecutionSignature",
    "ToolErrorInfo",
    "ToolTimeoutInfo",
    "ToolOutput",
    "NetworkInjectorConfig",
    "CloudInjectorConfig",
    "InjectorConfig",
    "build_network_configs",
    "ExecutionDetails",
    "ExtraSignatureData",
    "SignatureOutputStructure",
    "ExecutionStatus",
    "ExpectationType",
    "InjectExecutionActions",
]
_TYPES = [
    "ExpectationType",
    "ExecutionStatus",
    "InjectExecutionActions",
    "MatchTypes",
    "SignatureTypes",
]

LEGACY_NAMES = (
    [("pyoaev", name) for name in _PACKAGE]
    + [("pyoaev.signatures", name) for name in _PACKAGE]
    + [("pyoaev.signatures.models", name) for name in _MODELS]
    + [("pyoaev.signatures.types", name) for name in _TYPES]
    + [("pyoaev.signatures.signature_match", "SignatureMatch")]
    + [("pyoaev.signatures.signature_type", "SignatureType")]
    + [("pyoaev.signatures.ai_marker", "build_marker")]
    + [("pyoaev.signatures.signature_manager", "ExecutionDetails")]
    + [("pyoaev.signatures.signature_manager", "OpenAEVError")]
)
LEGACY_MANAGERS = [
    "pyoaev",
    "pyoaev.signatures",
    "pyoaev.signatures.signature_manager",
]


def _given_fresh_interpreter_script(script: str) -> list[str]:
    return [sys.executable, "-W", "error::DeprecationWarning", "-c", script]


def _when_run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True)


def _when_import_legacy_name(module: str, name: str):
    namespace: dict = {}
    source = f"from {module} import {name} as _legacy"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exec(compile(source, _CONSUMER, "exec"), namespace)
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    return namespace["_legacy"], deprecations


def _then_succeeds(result: subprocess.CompletedProcess) -> None:
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(("module", "name"), LEGACY_NAMES)
def test_legacy_import_warns_and_returns_the_sdk_object(module, name) -> None:
    """It warns towards xtm_oaev_sdk and returns the identical object."""
    sdk_name = _RENAMED.get(name, name)
    legacy, deprecations = _when_import_legacy_name(module, name)
    assert legacy is getattr(sdk, sdk_name)
    assert deprecations
    assert f"from xtm_oaev_sdk import {sdk_name}" in str(deprecations[0].message)
    # attributed to the consumer's line, so default warning filters show it
    assert any(w.filename == _CONSUMER for w in deprecations)


@pytest.mark.parametrize("module", LEGACY_MANAGERS)
def test_legacy_signature_manager_keeps_the_client_constructor(module) -> None:
    """It warns and sends through ``client.signature`` like before."""
    legacy_manager, deprecations = _when_import_legacy_name(module, "SignatureManager")
    assert deprecations
    assert issubclass(legacy_manager, sdk.SignatureManager)

    client = MagicMock()
    manager = legacy_manager(client, logger=None)

    assert manager.client is client
    assert manager.transport is client.signature


def test_importing_pyoaev_modules_is_silent() -> None:
    """It imports pyoaev and its signatures modules without any warning."""
    script = (
        "import pyoaev, pyoaev.apis, pyoaev.helpers, pyoaev.daemons\n"
        "import pyoaev.signatures, pyoaev.signatures.models\n"
        "import pyoaev.signatures.signature_manager, pyoaev.signatures.types\n"
        "import pyoaev.signatures.signature_match\n"
        "import pyoaev.signatures.signature_type, pyoaev.signatures.ai_marker\n"
    )
    result = _when_run(_given_fresh_interpreter_script(script))
    _then_succeeds(result)


def test_unknown_legacy_name_still_raises() -> None:
    """It does not swallow genuine misses."""
    with pytest.raises(ImportError):
        exec("from pyoaev.signatures import DoesNotExist", {})
