"""Schema-pinning guard for the signatures inbound seam.

Hashes each seam model's ``model_json_schema()`` and compares against
the committed golden file. Any drift in the seam schema fails this test.

The seam is the frozen boundary both sides of the capability share, so
this guard also enforces the dependency rule (the seam imports nothing
from the capability) and the identity contract (every re-export layer
shares the exact same objects as the seam).

To intentionally update the seam:
    1. Bump ``SEAM_VERSION`` in ``seam/signatures/seam.py``.
    2. Regenerate the golden file:
       ``python libs/xtm-oaev-sdk/test/seam/generate_signatures_seam_golden.py``
    3. Commit both changes together.
"""

import ast
import hashlib
import json
from pathlib import Path

from xtm_oaev_sdk.seam.signatures import (
    SEAM_VERSION,
    CloudInjectorConfig,
    ExecutionSignature,
    NetworkInjectorConfig,
    ToolErrorInfo,
    ToolOutput,
    ToolTimeoutInfo,
)
from xtm_oaev_sdk.seam.signatures import seam as seam_module

GOLDEN_PATH = Path(__file__).parent / "fixtures" / "signatures_seam_schemas.json"

SEAM_MODELS = {
    "ToolErrorInfo": ToolErrorInfo,
    "ToolTimeoutInfo": ToolTimeoutInfo,
    "ToolOutput": ToolOutput,
    "ExecutionSignature": ExecutionSignature,
    "NetworkInjectorConfig": NetworkInjectorConfig,
    "CloudInjectorConfig": CloudInjectorConfig,
}


def _schema_hash(model_cls) -> str:
    """SHA-256 of the canonical JSON Schema for a pydantic model class."""
    schema = model_cls.model_json_schema()
    canonical = json.dumps(schema, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def test_seam_version_is_pinned():
    """The version constant must be the pinned semver string."""
    assert SEAM_VERSION == "1.0.0"


def test_seam_schema_is_pinned():
    """Every seam model's JSON schema must match the committed golden file."""
    with GOLDEN_PATH.open() as f:
        golden = json.load(f)
    for name, cls in SEAM_MODELS.items():
        assert name in golden, f"{name} missing from golden file"
        actual = _schema_hash(cls)
        assert actual == golden[name], (
            f"{name}: seam schema drift detected\n"
            f"  golden {golden[name]}\n"
            f"  actual {actual}\n"
            "If this was intentional, bump SEAM_VERSION and regenerate the golden file."
        )


def test_seam_imports_nothing_from_capability():
    """The seam is pure data: no imports from xtm_oaev_sdk itself."""
    source = Path(seam_module.__file__).read_text()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(
                    "xtm_oaev_sdk"
                ), f"seam imports capability module {alias.name!r} — pure-data violation"
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert not module.startswith(
                "xtm_oaev_sdk"
            ), f"seam imports from capability module {module!r} — pure-data violation"


def test_reexports_preserve_identity():
    """The seam module, the seam package, and the public surface share one object."""
    import xtm_oaev_sdk as sdk
    import xtm_oaev_sdk.seam.signatures as seam_package

    for name, cls in SEAM_MODELS.items():
        assert (
            getattr(seam_package, name) is cls
        ), f"{name}: seam package re-export broke identity"
        assert (
            getattr(sdk, name) is cls
        ), f"{name}: public surface re-export broke identity"
    assert sdk.InjectorConfig is seam_package.InjectorConfig
