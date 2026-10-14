"""Port I/O data contract: the versioned wire schema crossing the SDK↔platform seam.

These models — and the three wire-vocabulary enums they serialise — define
the exact JSON shapes transmitted between the SDK's transport port
(``SignatureTransportProtocol``) and the platform's callback endpoint.  This package is the re-export surface; the seam **owns** the
models (``xtm_oaev_sdk.seam.port_io.models``), and the capability's port
(``_core/signatures``) re-exports them back for its historical surface.

They form a pinnable, anti-breaking boundary:

- contract unchanged + port (internal) changes  →  no breaking change
- contract unchanged + adapter (public) changes  →  retrocompat holds
- contract changes                               →  **breaking change**

Any modification to the JSON schema of a model in this module is a breaking
change for consumers and must bump :data:`PORT_IO_CONTRACT_VERSION`.

The schema-pinning guard (``tests/test_port_io_schema_pin.py``) hashes each
model's ``model_json_schema()`` against a golden file and fails on drift.
"""

from xtm_oaev_sdk.seam.port_io.models import (
    PORT_IO_CONTRACT_VERSION,
    ExecutionDetails,
    ExecutionStatus,
    ExpectationSignatureGroup,
    InjectExecutionActions,
    SignatureCallbackPayload,
    SignatureExpectationType,
    SignatureOutputStructure,
    SignaturePayload,
    SignatureTarget,
    SignatureValue,
    TargetSignatures,
)

__all__ = [
    "PORT_IO_CONTRACT_VERSION",
    "ExecutionDetails",
    "ExpectationSignatureGroup",
    "ExecutionStatus",
    "InjectExecutionActions",
    "SignatureCallbackPayload",
    "SignatureOutputStructure",
    "SignaturePayload",
    "SignatureTarget",
    "SignatureValue",
    "SignatureExpectationType",
    "TargetSignatures",
]
