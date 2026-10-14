"""Regenerate the golden schema hashes for the port I/O wire contract.

Run ``python libs/xtm-oaev-sdk/test/seam/generate_port_io_golden.py``. The
golden file pins the JSON schema of every wire model; it is only regenerated
on an intentional, version-bumped contract change.
"""

import hashlib
import json
from pathlib import Path

from xtm_oaev_sdk.seam.port_io import (
    ExecutionDetails,
    ExpectationSignatureGroup,
    SignatureOutputStructure,
    SignaturePayload,
    SignatureTarget,
    SignatureValue,
    TargetSignatures,
)

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


def main() -> None:
    out: dict[str, str] = {}
    for name, cls in CONTRACT_MODELS.items():
        canonical = json.dumps(cls.model_json_schema(), sort_keys=True)
        out[name] = hashlib.sha256(canonical.encode()).hexdigest()
    with GOLDEN_PATH.open("w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    print(f"wrote {GOLDEN_PATH}")


if __name__ == "__main__":
    main()
