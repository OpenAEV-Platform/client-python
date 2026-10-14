"""DEPRECATED: moved to :mod:`xtm_oaev_sdk`.

Backward-compatibility shim: every name below resolves to the *identical*
xtm_oaev_sdk object and emits a :class:`DeprecationWarning` on access.
``ExpectationType`` was renamed ``ContractExpectationType``.
"""

import xtm_oaev_sdk as _sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

__all__ = [  # noqa: F822 (names are served by the PEP 562 __getattr__ below)
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

_RENAMED = {"ExpectationType": "ContractExpectationType"}

__getattr__ = _make_deprecated_getattr(
    {
        **{
            name: (
                f"Use 'from xtm_oaev_sdk import {_RENAMED.get(name, name)}' instead.",
                getattr(_sdk, _RENAMED.get(name, name)),
            )
            for name in __all__
        },
    },
    module_name=__name__,
)
