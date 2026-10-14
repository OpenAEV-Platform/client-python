"""The scenarios (contracts) capability's seam surface.

Re-presents the capability's behaviour layer — the concrete builder, the
variable helper, and the preparation entry point — together with the
capability's extension protocol, so that the public firewall never imports
``_core`` directly.

The *data models* of the scenarios capability are a business concern and
live in :mod:`xtm_oaev_sdk.contracts`; this sub-package carries the
behaviour and the protocol only.
"""

from xtm_oaev_sdk._core.contracts import (
    ContractBuilder,
    ContractBuilderProtocol,
    VariableHelper,
    build_single_referenced_credential_element,
    prepare_contracts,
)

__all__ = [
    "ContractBuilder",
    "ContractBuilderProtocol",
    "VariableHelper",
    "build_single_referenced_credential_element",
    "prepare_contracts",
]
