# xtm-oaev-sdk

![version](https://img.shields.io/badge/version-0.1.0-blue)
![python](https://img.shields.io/badge/python-%3E%3D3.11-informational)
![license](https://img.shields.io/badge/license-Apache--2.0-green)

Shared core SDK for OpenAEV security connectors.

## Install

```bash
pip install xtm-oaev-sdk
```

**Dependencies:** pydantic `>=2.13.3,<2.14`, pydantic-settings `>=2.14,<2.15`, PyYAML `>=6.0,<6.1`, python-json-logger `>=3.3,<3.4`.

## Quickstart

The following example shows the full signature lifecycle using `SignatureManager`.
It assumes you already have a transport implementation (e.g. from `pyoaev`).

```python
import logging
from xtm_oaev_sdk import (
    SignatureManager,
    NetworkInjectorConfig,
    ExecutionDetails,
    build_network_configs,
    SignatureTransportProtocol,
    SignatureOutputStructure,
)

# 1. Wire up a transport (pyoaev provides one; here we sketch the contract)
class MyTransport:
    def send_signatures(
        self,
        inject_id: str,
        sig_output: SignatureOutputStructure,
        execution_details: ExecutionDetails,
        *,
        max_payload_size: int,
        logger: logging.Logger,
    ) -> None:
        # POST to the platform callback endpoint
        ...

transport = MyTransport()
manager = SignatureManager(transport=transport)

# 2. Build pre-execution signatures from typed injector configs
configs = build_network_configs(["192.168.1.10", "10.0.0.5"])
exec_sigs = manager.build_execution_signatures(configs)

# 3. Record execution details (start time is set automatically)
details = ExecutionDetails()

# 4. After tool completes, merge tool output into signatures
tool_result = {"status": "success"}
manager.post_execution_updates(details, exec_sigs, tool_result)

# 5. Build the wire payload
targets_meta = [
    type("T", (), {"agent_id": "agent-uuid", "asset_id": "asset-uuid", "asset_group_id": None})(),
    type("T", (), {"agent_id": "agent-uuid", "asset_id": "asset-uuid-2", "asset_group_id": None})(),
]
payload = SignatureManager.build_payload(
    exec_sigs,
    targets_meta,
    expectation_types=["DETECTION"],
)

# 6. Ship to the platform
manager.send_signatures("inject-uuid", details, payload)
```

## Module Map

| Group | What it provides |
|---|---|
| `errors` | Full exception hierarchy rooted at `OpenAEVError`; `on_http_error` decorator for wrapping HTTP failures |
| `utils` | `AppLoggerProtocol`, `EnhancedJSONEncoder`, `RequiredOptional`, `EncodedId`, dict helpers |
| `security_domain` | `SecurityDomains` enum: 9 named domains with display name and hex color |
| `client_protocol` | `BaseClient` — `@runtime_checkable` protocol defining the OpenAEV client interface |
| `daemon_protocol` | `DaemonProtocol` — `@runtime_checkable` protocol for daemon runtimes (`start`, `set_callback`, `get_id`) |
| `ssl_utils` | `ssl_cert_chain`, `ssl_verify_locations`, `is_memory_certificate`, `data_to_temp_file` — TLS helpers |
| `configuration` | `ConfigurationHint`, `ConfigurationProtocol`, `Configuration`, loaders, sources, schema generator |
| `contracts` | `ContractBuilderProtocol`, `ContractExpectationType` (8-member enum), fluent builder for contract field sets |
| `signatures` | `SignatureManager`, protocols, 10 frozen Pydantic models, enums, `build_network_configs` helper |

## Import Convention

Always import from the package root:

```python
from xtm_oaev_sdk import SignatureManager, OpenAEVError, ConfigurationHint
```

Never import from private submodules:

```python
# Wrong — internal layout may change without notice
from xtm_oaev_sdk._core.signatures.signature_manager import SignatureManager
```

The 102 symbols listed in `__all__` are the stable public API. Everything under `_core` is an implementation detail.

## Documentation

- [API Overview](docs/api-overview.md) — full symbol reference for each domain group
- [Usage Examples](docs/usage-examples.md) — practical, runnable code snippets
- [Migration Guide](docs/migration-guide.md) — moving from `pyoaev` to `xtm-oaev-sdk`
