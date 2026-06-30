# xtm-second-oaev-sdk

![version](https://img.shields.io/badge/version-0.1.0-blue)
![python](https://img.shields.io/badge/python-%3E%3D3.12-informational)
![license](https://img.shields.io/badge/license-Apache--2.0-green)

Shared core SDK for OpenAEV security connectors — restructured with DDD + Light Hexagonal Architecture.

`xtm-second-oaev-sdk` exposes the same 107 public symbols as `xtm-oaev-sdk` but organises its internals into three explicit layers: stable data-model contracts (`contracts/`), feature implementations (`_core/`), and a flat re-export surface (`public/`). The public API is identical; only the internal layout changes.

## Install

```bash
pip install xtm-second-oaev-sdk
```

**Dependencies:** pydantic `>=2.13.3,<2.14`, pydantic-settings `>=2.14,<2.15`, PyYAML `>=6.0,<6.1`, python-json-logger `>=3.3,<3.4`.

## Quickstart

The following example shows the full signature lifecycle using `SignatureManager`.
It assumes you already have a transport implementation (e.g. from `pyoaev`).

```python
import logging
from xtm_second_oaev_sdk import (
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

## Features

- **Full OpenAEV error hierarchy** rooted at `OpenAEVError`, with an `on_http_error` decorator for automatic wrapping
- **Configuration system** with hint-based multi-source resolution (env, YAML, override), pre-built loaders, and JSON schema generation
- **Contract builder** — fluent API for defining injector/collector field schemas and output contracts
- **Signature pipeline** — typed models for every wire shape, `SignatureManager` orchestrator, and `build_network_configs` helper
- **Asset taxonomy** — enums for `AssetCategory`, `AssetSubCategory`, `CloudProvider`, `AssetCriticality`
- **Security domain taxonomy** — `SecurityDomains` enum with display names and hex colors
- **Daemon + client protocols** — `@runtime_checkable` protocols for dependency injection and testing without coupling to pyoaev
- **TLS helpers** — cert chain fetching, in-memory certificate detection, temp-file bridging
- **Structured logging** — `AppLogger`, `CustomJsonFormatter`, `setup_logging_config`
- **Three-layer internal architecture** — stable contracts layer, private implementation layer, flat public surface

## Module Map

| Group | Symbols | Description |
|---|---|---|
| `errors` (14) | `OpenAEVError`, `OpenAEVAuthenticationError`, `OpenAEVHttpError`, `OpenAEVParsingError`, `RedirectError`, `OpenAEVHeadError`, `OpenAEVGetError`, `OpenAEVUpdateError`, `OpenAEVListError`, `OpenAEVCreateError`, `OpenAEVDeleteError`, `SignatureTransmissionError`, `ConfigurationError`, `on_http_error` | Full exception hierarchy rooted at `OpenAEVError`; `on_http_error` decorator for wrapping HTTP failures |
| `utils` (10) | `AppLogger`, `AppLoggerProtocol`, `CustomJsonFormatter`, `EnhancedJSONEncoder`, `RequiredOptional`, `EncodedId`, `copy_dict`, `remove_none_from_dict`, `logger`, `setup_logging_config` | Structured logging, JSON encoding, field-presence validation, dict helpers |
| `protocols` (2) | `BaseClient`, `DaemonProtocol` | `@runtime_checkable` protocols for the OpenAEV client and daemon runtime interfaces |
| `ssl_utils` (4) | `ssl_cert_chain`, `ssl_verify_locations`, `is_memory_certificate`, `data_to_temp_file` | TLS certificate chain fetching, CA bundle resolution, in-memory cert detection, temp-file bridging |
| `enums` (5) | `SecurityDomains`, `AssetCategory`, `AssetSubCategory`, `CloudProvider`, `AssetCriticality` | Domain taxonomy: 9 security domains, 12 asset categories, 55 subcategories, 7 cloud providers, 5 criticalities |
| `configuration` (14) | `Configuration`, `ConfigurationHint`, `ConfigurationProtocol`, `BaseConfigModel`, `CONFIGURATION_TYPES`, `SettingsLoader`, `ConfigLoaderCollector`, `ConfigLoaderOAEV`, `ConnectorConfigSchemaGenerator`, `DictionarySource`, `EnvironmentSource`, `HttpUrlToString`, `LogLevelToLower`, `TimedeltaInSeconds` | Hint-based config resolution (env, YAML, override), pre-built loaders, schema generator, type coercions |
| `contracts` (31) | `ContractBuilder`, `ContractBuilderProtocol`, `VariableHelper`, `prepare_contracts`, `ContractExpectationType`, `Contract`, `ContractConfig`, `ContractPayload`, `ContractElement`, `ContractText`, `ContractTextArea`, `ContractCheckbox`, `ContractSelect`, `ContractAsset`, `ContractAssetGroup`, `ContractAttachment`, `ContractTeam`, `ContractTuple`, `ContractVariable`, `ContractCardinality`, `ContractCardinalityElement`, `ContractFieldKey`, `ContractFieldType`, `ContractOutputElement`, `ContractOutputType`, `ContractExpectations`, `Expectation`, `Domain`, `SupportedLanguage`, `LinkedFieldModel`, `VariableType` | Fluent builder for contract field schemas; 28 OpenAEV scenario data models |
| `signatures` (26) | `SignatureManager`, `SignatureManagerProtocol`, `SignatureTransportProtocol`, `SignatureMatch`, `SignatureType`, `build_network_configs`, `SignatureExpectationType`, `InjectExecutionActions`, `MatchTypes`, `SignatureTypes`, `ExecutionDetails`, `ExecutionSignature`, `NetworkInjectorConfig`, `CloudInjectorConfig`, `InjectorConfig`, `SignaturePayload`, `SignatureOutputStructure`, `SignatureCallbackPayload`, `ExpectationSignatureGroup`, `SignatureValue`, `SignatureTarget`, `TargetSignatures`, `ExtraSignatureData`, `ToolOutput`, `ToolErrorInfo`, `ToolTimeoutInfo` | End-to-end signature orchestrator, protocols, 22 frozen data models, enums, config helper |

## Import Convention

Always import from the package root:

```python
from xtm_second_oaev_sdk import SignatureManager, OpenAEVError, ConfigurationHint
```

Never import from private submodules (`_core/`); their layout may change without notice:

```python
# Wrong — internal layout may change between releases
from xtm_second_oaev_sdk._core.signatures import SignatureManager
```

The 107 symbols listed in `__all__` are the stable public API. Everything under `_core/` is an implementation detail.

## Feature-Aware Imports (DDD consumers)

DDD consumers that import by domain boundary may use the stable `contracts/` layer directly. These paths are stable:

```python
# Errors and shared types from the common contracts port
from xtm_second_oaev_sdk.contracts.common import (
    OpenAEVError,
    OpenAEVAuthenticationError,
    DaemonProtocol,
    BaseClient,
    SecurityDomains,
)

# Configuration contracts (protocols, base models, type coercions)
from xtm_second_oaev_sdk.contracts.configuration import (
    ConfigurationProtocol,
    ConfigurationHint,
    BaseConfigModel,
    HttpUrlToString,
    LogLevelToLower,
    TimedeltaInSeconds,
)

# Scenario data models (28 models + builder protocol + enums)
from xtm_second_oaev_sdk.contracts.contracts import (
    ContractBuilderProtocol,
    ContractExpectationType,
    Contract,
    ContractText,
    ContractSelect,
    Expectation,
    ContractConfig,
)

# Signature data models (22 models + protocols + enums)
from xtm_second_oaev_sdk.contracts.signatures import (
    SignatureTransportProtocol,
    SignatureManagerProtocol,
    SignatureExpectationType,
    NetworkInjectorConfig,
    ExecutionDetails,
    SignatureOutputStructure,
)
```

Implementations (the feature classes) remain under `_core/` and are accessible via the flat root import.

## Documentation

- [API Overview](docs/api-overview.md) — full symbol reference for each domain group
- [Configuration](docs/configuration.md) — `Configuration`, `SettingsLoader`, sources, schema generation
- [Contracts & Signatures](docs/contracts-and-signatures.md) — builder API, scenario models, signature pipeline
- [Daemon Protocol](docs/daemon-protocol.md) — `DaemonProtocol` behavioral contract
- [Migration Guide](docs/migration-guide.md) — moving from `xtm-oaev-sdk` to `xtm-second-oaev-sdk`

## Deprecation Shim Strategy

This SDK is the canonical home for symbols previously in `pyoaev`. During migration, `pyoaev` keeps backward-compatible shims:

```python
# Old path (triggers DeprecationWarning, still works)
from pyoaev.helpers import ssl_cert_chain
from pyoaev.exceptions import OpenAEVError

# New path (clean, no warning)
from xtm_second_oaev_sdk import ssl_cert_chain
from xtm_second_oaev_sdk import OpenAEVError
```

The shim in `pyoaev` uses `__getattr__` to proxy the call to this SDK and emit a `DeprecationWarning`. Once all connectors are migrated, the shim is removed from `pyoaev` and this SDK becomes the sole source.

Shimmed symbol groups: SSL helpers (4), exceptions (13), utils (6), signatures (22), daemon protocol, configuration.

See [SECOND_README.md § Deprecation Shim Strategy](../../SECOND_README.md#deprecation-shim-strategy) for the full lifecycle and testing approach.

## Development

```bash
# Install in editable mode with test dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Check public surface (must remain 107 symbols)
python -c "from xtm_second_oaev_sdk import __all__; print(len(__all__))"
```
