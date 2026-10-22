"""DEPRECATED: moved to :mod:`xtm_oaev_sdk`.

Backward-compatibility shim: every name below resolves to the *identical*
xtm_oaev_sdk object and emits a :class:`DeprecationWarning` on access.
The module constants (``USER``, ``EXERCISE``, ...) are not part of the SDK
public surface; they keep their values here and warn.
"""

import xtm_oaev_sdk as _sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

__all__ = [  # noqa: F822 (names are served by the PEP 562 __getattr__ below)
    "VariableHelper",
    "ContractCardinality",
    "ContractVariable",
    "VariableType",
]

_CONSTANTS = {
    "USER": "user",
    "EXERCISE": "exercise",
    "TEAMS": "teams",
    "COMCHECK": "comcheck",
    "PLAYER_URI": "player_uri",
    "CHALLENGES_URI": "challenges_uri",
    "SCOREBOARD_URI": "scoreboard_uri",
    "LESSONS_URI": "lessons_uri",
}

__getattr__ = _make_deprecated_getattr(
    {
        **{
            name: (
                f"Use 'from xtm_oaev_sdk import {name}' instead.",
                getattr(_sdk, name),
            )
            for name in __all__
        },
        **{
            name: (
                f"'{name}' is deprecated and has no public replacement in "
                "xtm_oaev_sdk; use the VariableHelper built-in variables instead.",
                value,
            )
            for name, value in _CONSTANTS.items()
        },
    },
    module_name=__name__,
)
