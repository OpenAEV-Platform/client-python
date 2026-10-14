"""Contract of the pyoaev contracts shims.

Legacy imports must keep working, return the *identical* xtm_oaev_sdk object
(``ExpectationType`` was renamed ``ContractExpectationType``), warn, and be
attributed to the consumer's line.
"""

import subprocess
import sys
import warnings

import pytest
import xtm_oaev_sdk as sdk

_CONSUMER = "legacy_consumer.py"
_RENAMED = {"ExpectationType": "ContractExpectationType"}

_CONTRACT_CONFIG = [
    "SupportedLanguage",
    "ContractFieldType",
    "ContractFieldKey",
    "ContractOutputType",
    "PrimitiveType",
    "ExpectationType",
    "SecurityPlatformType",
    "Expectation",
    "LinkedFieldModel",
    "ContractElement",
    "ContractCardinalityElement",
    "ContractOutputElement",
    "ContractConfig",
    "Domain",
    "Contract",
    "ContractTeam",
    "ContractText",
    "prepare_contracts",
    "ContractTuple",
    "ContractTextArea",
    "ContractCheckbox",
    "ContractAttachment",
    "ContractExpectations",
    "ContractSelect",
    "ContractAsset",
    "ContractAssetGroup",
    "ContractAiTarget",
    "ContractPayload",
    "ContractReferencedCredential",
    "CredentialType",
    "EnhancedJSONEncoder",
    "ContractCardinality",
    "ContractVariable",
    "VariableHelper",
]

LEGACY_NAMES = (
    [("pyoaev", "ContractBuilder"), ("pyoaev.contracts", "ContractBuilder")]
    + [
        ("pyoaev.contracts.contract_builder", name)
        for name in ("ContractBuilder", "ContractElement", "ContractOutputElement")
    ]
    + [("pyoaev.contracts.contract_config", name) for name in _CONTRACT_CONFIG]
    + [
        ("pyoaev.contracts.contract_utils", name)
        for name in ("ContractCardinality", "VariableType", "ContractVariable")
    ]
    + [
        ("pyoaev.contracts.variable_helper", name)
        for name in (
            "VariableHelper",
            "ContractCardinality",
            "ContractVariable",
            "VariableType",
        )
    ]
    + [
        ("pyoaev.credential", name)
        for name in ("CredentialType", "build_single_referenced_credential_element")
    ]
    + [("pyoaev.credential.types", "CredentialType")]
    + [
        ("pyoaev.credential.utils", name)
        for name in (
            "ContractReferencedCredential",
            "CredentialType",
            "build_single_referenced_credential_element",
        )
    ]
)

LEGACY_CONSTANTS = {
    "USER": "user",
    "EXERCISE": "exercise",
    "TEAMS": "teams",
    "COMCHECK": "comcheck",
    "PLAYER_URI": "player_uri",
    "CHALLENGES_URI": "challenges_uri",
    "SCOREBOARD_URI": "scoreboard_uri",
    "LESSONS_URI": "lessons_uri",
}


def _when_import_legacy_name(module: str, name: str):
    namespace: dict = {}
    source = f"from {module} import {name} as _legacy"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exec(compile(source, _CONSUMER, "exec"), namespace)
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    return namespace["_legacy"], deprecations


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


@pytest.mark.parametrize(("name", "value"), LEGACY_CONSTANTS.items())
def test_legacy_variable_constants_keep_their_value_and_warn(name, value) -> None:
    """It keeps the unexported module constants working, with a warning."""
    legacy, deprecations = _when_import_legacy_name(
        "pyoaev.contracts.variable_helper", name
    )
    assert legacy == value
    assert deprecations


def test_importing_pyoaev_contracts_is_silent() -> None:
    """It imports pyoaev and its contracts modules without any warning."""
    script = (
        "import pyoaev, pyoaev.contracts, pyoaev.contracts.contract_builder\n"
        "import pyoaev.contracts.contract_config, pyoaev.contracts.contract_utils\n"
        "import pyoaev.contracts.variable_helper\n"
        "import pyoaev.credential, pyoaev.credential.types, pyoaev.credential.utils\n"
    )
    result = subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_unknown_legacy_name_still_raises() -> None:
    """It does not swallow genuine misses."""
    with pytest.raises(ImportError):
        exec("from pyoaev.contracts.contract_config import DoesNotExist", {})
