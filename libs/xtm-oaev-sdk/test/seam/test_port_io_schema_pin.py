"""Schema-pinning guard for the port I/O data contract.

Hashes each contract model's ``model_json_schema()`` and compares against
the committed golden file. Any drift in the wire schema fails this test.

To intentionally update the contract:
    1. Bump ``PORT_IO_CONTRACT_VERSION`` in ``seam/port_io/models.py``.
    2. Regenerate the golden file:
       ``python libs/xtm-oaev-sdk/test/seam/generate_port_io_golden.py``
    3. Commit both changes together.
"""

import ast
import hashlib
import json
from pathlib import Path

from xtm_oaev_sdk.seam.port_io import (
    PORT_IO_CONTRACT_VERSION,
    ExecutionDetails,
    ExpectationSignatureGroup,
    SignatureOutputStructure,
    SignaturePayload,
    SignatureTarget,
    SignatureValue,
    TargetSignatures,
)
from xtm_oaev_sdk.seam.port_io import models as port_io_models

GOLDEN_PATH = Path(__file__).parent / "fixtures" / "port_io_schemas.json"

CONTRACT_MODELS = {
    "ExecutionDetails": ExecutionDetails,
    "ExpectationSignatureGroup": ExpectationSignatureGroup,
    "SignatureOutputStructure": SignatureOutputStructure,
    "SignaturePayload": SignaturePayload,
    "SignatureTarget": SignatureTarget,
    "SignatureValue": SignatureValue,
    "TargetSignatures": TargetSignatures,
}


def _schema_hash(model_cls) -> str:
    """SHA-256 of the canonical JSON Schema for a pydantic model class."""
    schema = model_cls.model_json_schema()
    canonical = json.dumps(schema, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _load_golden() -> dict[str, str]:
    with GOLDEN_PATH.open() as f:
        return json.load(f)


def test_port_io_contract_version_is_pinned():
    """The version constant must be a semver string, not a placeholder."""
    assert PORT_IO_CONTRACT_VERSION == "1.0.0"


def test_port_io_wire_schema_matches_golden():
    """Every contract model's JSON Schema must match the golden file.

    This is the anti-breaking guard: if a field is added, removed, renamed,
    or retyped in any of the 7 wire models, this test fails.
    """
    golden = _load_golden()

    # Guard against accidental golden file truncation.
    assert len(golden) == len(CONTRACT_MODELS), (
        f"Golden file has {len(golden)} entries; expected {len(CONTRACT_MODELS)}. "
        f"Missing: {set(CONTRACT_MODELS) - set(golden)}"
    )

    for name, cls in sorted(CONTRACT_MODELS.items()):
        current = _schema_hash(cls)
        expected = golden[name]
        assert current == expected, (
            f"Schema drift detected in {name} (port I/O contract "
            f"v{PORT_IO_CONTRACT_VERSION}).\n"
            f"  expected: {expected}\n"
            f"  actual:   {current}\n"
            f"If intentional, bump PORT_IO_CONTRACT_VERSION and regenerate "
            f"the golden file."
        )


def test_port_io_models_import_only_the_signatures_seam():
    """The wire contract is closed: no import of the capability internals."""
    source = Path(port_io_models.__file__).read_text()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "xtm_oaev_sdk"
        ):
            assert node.module == "xtm_oaev_sdk.seam.signatures.seam", node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("xtm_oaev_sdk"), alias.name
