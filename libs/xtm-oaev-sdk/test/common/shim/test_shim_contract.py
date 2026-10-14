"""Contract of the pyoaev shims for the shared (common) capability.

Legacy imports must keep working, return the *identical* xtm_oaev_sdk object,
and warn; importing pyoaev's own modules and using the SDK directly must stay
silent.
"""

import subprocess
import sys
import warnings

import pytest
import xtm_oaev_sdk as sdk

_ERRORS = [
    "ConfigurationError",
    "OpenAEVAuthenticationError",
    "OpenAEVCreateError",
    "OpenAEVDeleteError",
    "OpenAEVError",
    "OpenAEVGetError",
    "OpenAEVHeadError",
    "OpenAEVHttpError",
    "OpenAEVListError",
    "OpenAEVParsingError",
    "OpenAEVUpdateError",
    "RedirectError",
    "SignatureTransmissionError",
    "on_http_error",
]
_UTILS = [
    "AppLogger",
    "CustomJsonFormatter",
    "EncodedId",
    "EnhancedJSONEncoder",
    "RequiredOptional",
    "copy_dict",
    "logger",
    "remove_none_from_dict",
    "setup_logging_config",
]
_SSL = [
    "data_to_temp_file",
    "is_memory_certificate",
    "ssl_cert_chain",
    "ssl_verify_locations",
]
_ASSET_TYPES = [
    "AssetCategory",
    "AssetCriticality",
    "AssetSubCategory",
    "CloudProvider",
]

LEGACY_NAMES = (
    [("pyoaev.exceptions", name) for name in _ERRORS]
    + [("pyoaev.utils", name) for name in _UTILS]
    + [("pyoaev.helpers", name) for name in _SSL]
    + [("pyoaev.asset_types", name) for name in _ASSET_TYPES]
    + [("pyoaev.security_domain.types", "SecurityDomains")]
    + [("pyoaev", name) for name in _ASSET_TYPES]
    + [
        ("pyoaev", name)
        for name in _ERRORS
        if name not in ("OpenAEVError", "on_http_error")
    ]
)


_CONSUMER = "legacy_consumer.py"


def _given_fresh_interpreter_script(script: str) -> list[str]:
    return [sys.executable, "-W", "error::DeprecationWarning", "-c", script]


def _when_run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True)


def _when_import_legacy_name(module: str, name: str):
    namespace: dict = {}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exec(
            compile(f"from {module} import {name} as _legacy", _CONSUMER, "exec"),
            namespace,
        )
    return namespace["_legacy"], caught


def _then_succeeds(result: subprocess.CompletedProcess) -> None:
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(("module", "name"), LEGACY_NAMES)
def test_legacy_import_warns_and_returns_the_sdk_object(module, name) -> None:
    """It warns towards xtm_oaev_sdk and returns the identical object."""
    legacy, caught = _when_import_legacy_name(module, name)
    assert legacy is getattr(sdk, name)
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert deprecations
    assert f"from xtm_oaev_sdk import {name}" in str(deprecations[0].message)
    # attributed to the consumer's line, so default warning filters show it
    assert any(w.filename == _CONSUMER for w in deprecations)


def test_pyoaev_all_still_lists_legacy_exceptions() -> None:
    """It keeps the legacy star-export surface of pyoaev."""
    import pyoaev

    for name in _ERRORS:
        if name not in ("OpenAEVError", "on_http_error"):
            assert name in pyoaev.__all__
    for name in _ASSET_TYPES:
        assert name in pyoaev.__all__


def test_importing_pyoaev_modules_is_silent() -> None:
    """It imports pyoaev and its own modules without any DeprecationWarning."""
    script = (
        "import pyoaev, pyoaev.apis, pyoaev.base, pyoaev.client, pyoaev.mixins\n"
        "import pyoaev.helpers, pyoaev.daemons, pyoaev.contracts, pyoaev.signatures\n"
        "import pyoaev.utils, pyoaev.exceptions, pyoaev.asset_types\n"
        "import pyoaev.security_domain.types\n"
    )
    result = _when_run(_given_fresh_interpreter_script(script))
    _then_succeeds(result)


def test_sdk_objects_stay_silent_once_pyoaev_is_loaded() -> None:
    """It never alters SDK objects: native use stays silent next to pyoaev."""
    script = (
        "import pyoaev, pyoaev.exceptions, pyoaev.utils, pyoaev.helpers\n"
        "import xtm_oaev_sdk as sdk\n"
        "sdk.EncodedId('a b')\n"
        "sdk.RequiredOptional(required=('a',)).validate_attrs(data={'a': 1})\n"
        "sdk.AssetCategory('WEB_APPLICATION')\n"
        "try:\n"
        "    raise sdk.OpenAEVHttpError('boom', 500)\n"
        "except sdk.OpenAEVError:\n"
        "    pass\n"
    )
    result = _when_run(_given_fresh_interpreter_script(script))
    _then_succeeds(result)


@pytest.mark.parametrize(
    "module", ["pyoaev.exceptions", "pyoaev.utils", "pyoaev.helpers"]
)
def test_unknown_legacy_name_still_raises(module: str) -> None:
    """It does not swallow genuine misses."""
    with pytest.raises(ImportError):
        exec(f"from {module} import DoesNotExist", {})
