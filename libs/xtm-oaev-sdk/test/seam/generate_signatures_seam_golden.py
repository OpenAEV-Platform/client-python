"""Regenerate the golden schema hashes for the signatures inbound seam.

Run ``python libs/xtm-oaev-sdk/test/seam/generate_signatures_seam_golden.py``. The golden file pins the
JSON schema of every seam model; it is only regenerated on an
intentional, version-bumped contract change.
"""

import hashlib
import json
from pathlib import Path

from xtm_oaev_sdk.seam.signatures.seam import (
    CloudInjectorConfig,
    ExecutionSignature,
    NetworkInjectorConfig,
    ToolErrorInfo,
    ToolOutput,
    ToolTimeoutInfo,
)

GOLDEN_PATH = Path(__file__).parent / "fixtures" / "signatures_seam_schemas.json"

SEAM_MODELS = {
    "ToolErrorInfo": ToolErrorInfo,
    "ToolTimeoutInfo": ToolTimeoutInfo,
    "ToolOutput": ToolOutput,
    "ExecutionSignature": ExecutionSignature,
    "NetworkInjectorConfig": NetworkInjectorConfig,
    "CloudInjectorConfig": CloudInjectorConfig,
}


def main() -> None:
    out: dict[str, str] = {}
    for name, cls in SEAM_MODELS.items():
        canonical = json.dumps(cls.model_json_schema(), sort_keys=True)
        out[name] = hashlib.sha256(canonical.encode()).hexdigest()
    with GOLDEN_PATH.open("w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    print(f"wrote {GOLDEN_PATH}")


if __name__ == "__main__":
    main()
