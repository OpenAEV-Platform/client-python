"""DEPRECATED: moved to :mod:`xtm_oaev_sdk`.

Backward-compatibility shim: every name below resolves to the *identical*
xtm_oaev_sdk object and emits a :class:`DeprecationWarning` on access, with
two exceptions: ``ExpectationType`` was renamed ``SignatureExpectationType``,
and ``SignatureManager`` resolves to the client-based adapter described in
:mod:`pyoaev.signatures.signature_manager`.
"""

import xtm_oaev_sdk as _sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

from pyoaev.signatures.signature_manager import _ClientSignatureManager

__all__ = [
    "CloudInjectorConfig",
    "ExpectationSignatureGroup",
    "ExpectationType",
    "ExtraSignatureData",
    "InjectorConfig",
    "InjectExecutionActions",
    "MatchTypes",
    "NetworkInjectorConfig",
    "SignatureCallbackPayload",
    "SignatureManager",
    "SignaturePayload",
    "SignatureTarget",
    "SignatureTypes",
    "SignatureValue",
    "TargetSignatures",
    "build_network_configs",
]

_RENAMED = {"ExpectationType": "SignatureExpectationType"}

# Also served from the pyoaev package root, which used to star-import it.
_DEPRECATED = {
    "SignatureManager": (
        "Use 'from xtm_oaev_sdk import SignatureManager' with a "
        "SignatureTransportProtocol transport (e.g. client.signature) instead.",
        _ClientSignatureManager,
    ),
    **{
        name: (
            f"Use 'from xtm_oaev_sdk import {_RENAMED.get(name, name)}' instead.",
            getattr(_sdk, _RENAMED.get(name, name)),
        )
        for name in __all__
        if name != "SignatureManager"
    },
}

__getattr__ = _make_deprecated_getattr(_DEPRECATED, module_name=__name__)
