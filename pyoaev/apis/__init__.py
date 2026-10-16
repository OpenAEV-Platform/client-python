import collectors_sdk as _collectors_sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

from .ai_target import *  # noqa: F401,F403
from .attack_pattern import *  # noqa: F401,F403
from .collector import *  # noqa: F401,F403
from .cve import *  # noqa: F401,F403
from .document import *  # noqa: F401,F403
from .endpoint import *  # noqa: F401,F403
from .inject import *  # noqa: F401,F403
from .inject_expectation import *  # noqa: F401,F403
from .inject_expectation_trace import *  # noqa: F401,F403
from .injector import *  # noqa: F401,F403
from .injector_contract import *  # noqa: F401,F403
from .kill_chain_phase import *  # noqa: F401,F403
from .me import *  # noqa: F401,F403
from .organization import *  # noqa: F401,F403
from .payload import *  # noqa: F401,F403
from .security_platform import *  # noqa: F401,F403
from .signature import *  # noqa: F401,F403
from .tag import *  # noqa: F401,F403
from .team import *  # noqa: F401,F403
from .user import *  # noqa: F401,F403
from .vulnerability import *  # noqa: F401,F403

# The expectation models moved to collectors_sdk; their legacy names stay in
# ``__all__`` and are served by the PEP 562 __getattr__ below, with a warning.
_MOVED_MODELS = ["DetectionExpectation", "ExpectationTypeEnum", "PreventionExpectation"]

__all__ = [  # noqa: F822 (moved names are served by the PEP 562 __getattr__ below)
    *[name for name in dir() if not name.startswith("_")],
    *_MOVED_MODELS,
]

__getattr__ = _make_deprecated_getattr(
    {
        name: (
            f"Use 'from collectors_sdk import {name}' instead.",
            getattr(_collectors_sdk, name),
        )
        for name in _MOVED_MODELS
    },
    module_name=__name__,
)
