"""xtm-second-oaev-sdk — OpenAEV SDK core (DDD + Light Hex Architecture).

Architecture:
    _core/common/         Shared implementations (errors, utils, ssl)
    _core/configuration/  Configuration feature implementations
    _core/contracts/      OpenAEV scenarios feature implementations
    _core/signatures/     Signature feature implementations
    contracts/common/     Shared protocols, enums, types
    contracts/configuration/  Configuration contracts
    contracts/contracts/  Scenario data models
    contracts/signatures/ Signature data models
    public/              User-facing re-exports (107 symbols)
"""

__version__ = "0.1.0"

from xtm_second_oaev_sdk.public import *  # noqa: F401, F403
from xtm_second_oaev_sdk.public import __all__ as _public_all

__all__ = list(_public_all)
