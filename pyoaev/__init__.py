# -*- coding: utf-8 -*-
__version__ = "2.2.0"

from pyoaev._version import (  # noqa: F401
    __author__,
    __copyright__,
    __email__,
    __license__,
    __title__,
)
from pyoaev.client import OpenAEV  # noqa: F401
from pyoaev.configuration import *  # noqa: F401,F403,F405
from pyoaev.contracts import *  # noqa: F401,F403,F405
from pyoaev.exceptions import *  # noqa: F401,F403,F405
from pyoaev.signatures import *  # noqa: F401,F403,F405

__all__ = [
    "__author__",
    "__copyright__",
    "__email__",
    "__license__",
    "__title__",
    "__version__",
    "OpenAEV",
]
__all__.extend(exceptions.__all__)  # noqa: F405
