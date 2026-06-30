# API Overview

`xtm-oaev-sdk` organises its implementation across three explicit layers. The root `xtm_oaev_sdk/__init__.py` re-exports exactly 107 stable symbols via `public/` and is the only surface consumers should target.

## Three-Layer Architecture

```
xtm_oaev_sdk/
  __init__.py              ← public API surface (import from here)
  public/
    __init__.py            ← 107 re-exports; the canonical __all__
  contracts/               ← stable ports: protocols, data models, enums
    common/                  shared: error hierarchy, protocols, enums, type aliases (35 symbols)
    configuration/           ConfigurationProtocol, BaseConfigModel, type coercions (7 symbols)
    contracts/               28 OpenAEV scenario data models + builder protocol (28 symbols)
    signatures/              22 signature data models + protocols + enums (22 symbols)
  _core/                   ← private implementations (adapters)
    common/                  errors, utils, SSL, logging (12 symbols)
    configuration/           Configuration, SettingsLoader, sources, schema gen (7 symbols)
    contracts/               ContractBuilder, VariableHelper, prepare_contracts (3 symbols)
    signatures/              SignatureManager, SignatureMatch, SignatureType, build_network_configs (4 symbols)
```

The dependency direction is strict:

```
public/ → contracts/ ← _core/
```

`contracts/` defines stable interfaces that both `public/` (re-exports) and `_core/` (implementations) depend on. `_core/` depends on `contracts/` for its type definitions; `contracts/` never imports from `_core/`. This is the Light Hexagonal Architecture pattern: `contracts/` is the hexagonal ports layer; `_core/` is the adapters layer.

The `_core/` tree is an implementation detail. Its internal structure may change between releases; the root `__init__.py` will not.

---

## Domain Breakdown

| Domain | `contracts/` | `_core/` | Public total |
|---|---:|---:|---:|
| common (shared) | 23 | 12 | 35 |
| configuration | 7 | 7 | 14 |
| contracts (scenarios) | 28 | 3 | 31 |
| signatures | 22 | 4 | 26 |
| `__version__` | — | — | 1 |
| **Total** | **80** | **26** | **107** |

---

## common / errors

Exception hierarchy for all SDK operations. Every error derives from `OpenAEVError` so callers can choose between granular and catch-all handling.

**Exception tree:**

```
OpenAEVError (base)
├── OpenAEVAuthenticationError   — bad credentials / expired token / forbidden
├── OpenAEVHttpError             — generic HTTP transport errors
├── OpenAEVParsingError          — response deserialisation failures
├── RedirectError                — unexpected HTTP redirects
├── OpenAEVHeadError             — HEAD request failures
├── OpenAEVGetError              — GET request failures
├── OpenAEVUpdateError           — PUT/PATCH failures
├── OpenAEVListError             — list/pagination failures
├── OpenAEVCreateError           — POST creation failures
├── OpenAEVDeleteError           — DELETE request failures
├── SignatureTransmissionError   — signature delivery failures
└── ConfigurationError           — configuration loading/validation failures
```

`OpenAEVError` carries structured context: `error_message`, `response_code` (HTTP status), and `response_body` (raw bytes). Its `__str__` implementation extracts human-readable messages from JSON payloads automatically.

### Key symbols

| Symbol | Kind | Description |
|---|---|---|
| `OpenAEVError` | Exception | Base class. `error_message`, `response_code`, `response_body`. |
| `OpenAEVAuthenticationError` | Exception | Credential / token failure. |
| `OpenAEVHttpError` | Exception | Generic HTTP transport error. |
| `OpenAEVParsingError` | Exception | Response deserialisation failure. |
| `RedirectError` | Exception | Unexpected HTTP redirect. |
| `OpenAEVHeadError` | Exception | HEAD request failure. |
| `OpenAEVGetError` | Exception | GET request failure. |
| `OpenAEVUpdateError` | Exception | PUT/PATCH failure. |
| `OpenAEVListError` | Exception | List/pagination failure. |
| `OpenAEVCreateError` | Exception | POST creation failure. |
| `OpenAEVDeleteError` | Exception | DELETE request failure. |
| `SignatureTransmissionError` | Exception | Signature delivery failure. |
| `ConfigurationError` | Exception | Config loading/validation failure. |
| `on_http_error(error)` | Decorator | Wraps `OpenAEVHttpError` into a caller-specified type. |

---

## common / utils

Shared infrastructure utilities: logging, JSON encoding, field-presence validation, and dict manipulation.

### Protocols

| Symbol | Description |
|---|---|
| `AppLoggerProtocol` | `@runtime_checkable` protocol for logger services. Methods: `debug`, `info`, `warning`, `error`, `setup_logger_level`. Supports `__call__(name)` for per-module instances. |

### Key classes

| Symbol | Kind | Description |
|---|---|---|
| `AppLogger` | Class | Structured logger with JSON formatting support. |
| `CustomJsonFormatter` | Class | JSON log formatter for structured logging pipelines. |
| `EnhancedJSONEncoder` | Class | `json.JSONEncoder` subclass. Serialises `@dataclass` instances via `asdict()` and `BaseModel` instances via `model_dump()`. |
| `RequiredOptional` | Pydantic model (frozen) | Field-presence validator. Declare `required`, `optional`, and `exclusive` tuples; call `validate_attrs(data=...)` to enforce them. |
| `EncodedId` | `str` subclass | URL-safe percent-encoded identifier. Idempotent; accepts `str`, `int`, or another `EncodedId`. |

### Utility functions

| Symbol | Description |
|---|---|
| `logger` | Factory function returning an `AppLogger` instance for a given level. |
| `setup_logging_config` | Configures Python logging with appropriate handlers and formatters. |
| `copy_dict(*, src, dest)` | Flattens nested dicts into bracket-notation keys (`{"filters": {"type": "x"}}` → `dest["filters[type]"] = "x"`). Mutates `dest` in place. |
| `remove_none_from_dict(data)` | Returns a copy of `data` with all `None`-valued keys removed. |

---

## common / protocols

Protocol definitions for cross-package dependency injection and testing.

### Protocols

| Symbol | Description |
|---|---|
| `BaseClient` | `@runtime_checkable` protocol. Defines the public surface an OpenAEV client must expose. Used by extension SDKs for type-hinting without coupling to the concrete `pyoaev.OpenAEV` class. |
| `DaemonProtocol` | `@runtime_checkable` protocol. Methods: `start()`, `set_callback(callback)`, `get_id() -> str \| None`. See [Daemon Protocol](daemon-protocol.md). |

---

## common / ssl_utils

TLS/SSL helper functions for certificate chain handling and verification.

### Utility functions

| Symbol | Description |
|---|---|
| `ssl_cert_chain(url)` | Fetches the full certificate chain from a remote server. Returns list of PEM-encoded certificates. |
| `ssl_verify_locations(config)` | Returns appropriate CA bundle path or verification settings from configuration. |
| `is_memory_certificate(cert_data)` | Determines whether certificate data is an in-memory PEM string vs a file path. |
| `data_to_temp_file(data, suffix)` | Writes in-memory data to a named temporary file. Useful for passing PEM strings to libraries that expect file paths. |

---

## common / enums

Domain taxonomy enums shared across features.

| Symbol | Kind | Members |
|---|---|---|
| `SecurityDomains` | Enum | `ENDPOINT`, `NETWORK`, `WEB_APP`, `EMAIL_INFILTRATION`, `DATA_EXFILTRATION`, `URL_FILTERING`, `CLOUD`, `TABLE_TOP`, `TOCLASSIFY` |
| `AssetCategory` | Enum (12 members) | `HOST`, `CONTAINER_WORKLOAD`, `CLOUD_RESOURCE`, `WEB_APPLICATION`, `NETWORK_DEVICE`, `MOBILE_DEVICE`, `IOT_OT_DEVICE`, `IDENTITY`, `SAAS_APPLICATION`, `AI_TARGET`, `SECURITY_PLATFORM`, `GENERIC_ASSET` |
| `AssetSubCategory` | Enum (55 members) | Per-category subtypes: `SERVER`, `CONTAINER`, `COMPUTE`, `WEBSITE`, `ROUTER`, `LLM_MODEL`, `AI_AGENT`, etc. |
| `CloudProvider` | Enum (7 members) | `AWS`, `AZURE`, `GCP`, `OCI`, `ALIBABA`, `KUBERNETES`, `OTHER` |
| `AssetCriticality` | Enum (5 members) | `VERY_HIGH`, `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN` |

Each `SecurityDomains` member value is a dict with `domain_name` (human-readable string) and `domain_color` (hex string for UI rendering).

```python
from xtm_oaev_sdk import SecurityDomains

SecurityDomains.NETWORK.value["domain_name"]   # "Network"
SecurityDomains.NETWORK.value["domain_color"]  # "#009933"
```

---

## configuration

Hint-based configuration resolution with multi-source lookup (environment variables, YAML files, explicit overrides). Exposes a protocol for testing and dependency injection plus pre-built loaders for common OpenAEV connector patterns. Full documentation: [Configuration](configuration.md).

### Key classes

| Symbol | Kind | Description |
|---|---|---|
| `ConfigurationHint` | Pydantic model (frozen) | Describes where a single config value can be found. Fields: `data` (override), `env` (env var name), `file_path` (YAML path list), `is_number` (coerce to int), `default`. Use `model_copy(update=...)` to derive modified hints. |
| `ConfigurationProtocol` | `@runtime_checkable` protocol | Methods: `get(key)`, `set(key, value)`, `schema()`. Any custom configuration implementation must satisfy this. |
| `Configuration` | Class | Accepts a `dict[str, dict \| str]` of hints and resolves values with priority: `set()` > env > YAML > default. |
| `BaseConfigModel` | Pydantic model | Base for typed config models with schema generation support. |
| `CONFIGURATION_TYPES` | Dict | Registry mapping type-string keys to Python types for schema generation. |
| `ConfigLoaderCollector` | Class | Pre-built loader for collector configuration keys (`collector_id`, `collector_name`, etc.). |
| `ConfigLoaderOAEV` | Class | Pre-built loader for OpenAEV platform connection keys (`url`, `token`, `tenant_id`). |
| `SettingsLoader` | Class | Generic settings loader supporting config files and environment variables. |
| `ConnectorConfigSchemaGenerator` | Class | Generates JSON Schema from typed config models for documentation and validation. |
| `DictionarySource` | Class | Configuration source that reads from an in-memory dict. |
| `EnvironmentSource` | Class | Configuration source that reads from environment variables. |
| `HttpUrlToString` | Annotated type | Pydantic validator that coerces `HttpUrl` to plain `str`. |
| `LogLevelToLower` | Annotated type | Pydantic validator that normalises log level strings to lowercase. |
| `TimedeltaInSeconds` | Annotated type | Pydantic validator that coerces `timedelta` to integer seconds. |

---

## contracts (scenarios)

Fluent builder API for declaring injector/collector contract field schemas. Full documentation: [Contracts & Signatures](contracts-and-signatures.md).

### Builder

| Symbol | Kind | Description |
|---|---|---|
| `ContractBuilder` | Class | Fluent builder. Chainable methods: `mandatory()`, `optional()`, `mandatory_group()`, `add_fields()`, `add_outputs()`, `build_fields()`, `build_outputs()`. |
| `ContractBuilderProtocol` | `@runtime_checkable` protocol | Protocol surface of `ContractBuilder`; use for type hints and testing. |
| `VariableHelper` | Class | Helper for resolving and formatting contract variable references. |
| `prepare_contracts` | Function | Utility that assembles a final contract payload from builder output. |

### Enums

| Symbol | Kind | Members |
|---|---|---|
| `ContractExpectationType` | Enum (8 members) | `text`, `document`, `article`, `challenge`, `manual`, `prevention`, `detection`, `vulnerability` |
| `ContractFieldKey` | Enum | Field key identifiers for standard contract fields |
| `ContractFieldType` | Enum | Field type identifiers |
| `ContractOutputType` | Enum | Output type identifiers |
| `VariableType` | Enum | Variable type identifiers |
| `SupportedLanguage` | Enum | Supported language codes for contract localisation |

### Data models (28)

| Symbol | Kind | Description |
|---|---|---|
| `Contract` | Pydantic model | Top-level contract descriptor |
| `ContractConfig` | Pydantic model | Contract configuration metadata |
| `ContractPayload` | Pydantic model | Wire payload wrapping contract fields and outputs |
| `ContractElement` | Pydantic model | Base for all contract field elements |
| `ContractText` | Pydantic model | Single-line text input field |
| `ContractTextArea` | Pydantic model | Multi-line text input field |
| `ContractCheckbox` | Pydantic model | Boolean checkbox field |
| `ContractSelect` | Pydantic model | Single-choice select field with `choices` dict |
| `ContractAsset` | Pydantic model | Asset picker field |
| `ContractAssetGroup` | Pydantic model | Asset group picker field |
| `ContractAttachment` | Pydantic model | File attachment field |
| `ContractTeam` | Pydantic model | Team picker field |
| `ContractTuple` | Pydantic model | Ordered multi-value field |
| `ContractVariable` | Pydantic model | Variable reference field |
| `ContractCardinality` | Pydantic model | Cardinality constraint descriptor |
| `ContractCardinalityElement` | Pydantic model | Single cardinality element |
| `ContractOutputElement` | Pydantic model | One output field descriptor |
| `ContractExpectations` | Pydantic model | Expectation set for a contract |
| `Expectation` | Pydantic model | Single expectation with type and label |
| `Domain` | Pydantic model | Domain reference within a contract |
| `LinkedFieldModel` | Pydantic model | Field with a dependency link to another field |

---

## signatures

The signature lifecycle subsystem: typed injector configs, frozen Pydantic models for every wire shape, enums, the `SignatureManager` orchestrator, and transport/manager protocols. Full documentation: [Contracts & Signatures](contracts-and-signatures.md).

### Protocols

| Symbol | Description |
|---|---|
| `SignatureTransportProtocol` | `@runtime_checkable`. Single method: `send_signatures(inject_id, sig_output, execution_details, *, max_payload_size, logger)`. `pyoaev` implements this. |
| `SignatureManagerProtocol` | `@runtime_checkable`. Covers the full pipeline: `build_execution_signatures`, `post_execution_updates`, `send_signatures`, `resolve_container_ip`. |

### Key classes

| Symbol | Kind | Description |
|---|---|---|
| `SignatureManager` | Class | End-to-end orchestrator. Constructor: `(transport, logger=None, max_payload_size=5_242_880)`. |
| `SignatureMatch` | Class | Stores match type and optional score threshold. |
| `SignatureType` | Class | Couples a `SignatureTypes` label with a `MatchTypes` policy. `make_struct_for_matching(data)` produces helper dicts. |
| `build_network_configs(targets)` | Function | Converts a heterogeneous list of `str`, `dict`, or `NetworkInjectorConfig` items into a typed `list[NetworkInjectorConfig]`. Strings are auto-classified as IPv4, IPv6, or hostname. |

### Enums

| Symbol | Kind | Members |
|---|---|---|
| `SignatureExpectationType` | Enum (3 members) | `DETECTION`, `PREVENTION`, `VULNERABILITY` |
| `InjectExecutionActions` | Enum (8 members) | `PREREQUISITE_CHECK`, `PREREQUISITE_EXECUTION`, `CLEANUP_EXECUTION`, `COMMAND_EXECUTION`, `DNS_RESOLUTION`, `FILE_EXECUTION`, `FILE_DROP`, `COMPLETE` |
| `MatchTypes` | Enum (2 members) | `MATCH_TYPE_FUZZY`, `MATCH_TYPE_SIMPLE` |
| `SignatureTypes` | Enum (15 members) | Field identifiers: `SIG_TYPE_SOURCE_IPV4_ADDRESS`, `SIG_TYPE_TARGET_HOSTNAME_ADDRESS`, `SIG_TYPE_CLOUD_PROVIDER`, `SIG_TYPE_AI_REQUEST_MARKER`, `SIG_TYPE_AI_TARGET_ENDPOINT`, etc. |

### Data models (22)

| Symbol | Kind | Description |
|---|---|---|
| `ExecutionDetails` | Pydantic model | Execution metadata: `start_time`, `end_time`, `execution_status`, `execution_action`. Computed: `execution_message`, `execution_duration`. |
| `ExecutionSignature` | Pydantic model | Flat per-target signature record. Network fields: `source_ipv4/ipv6`, `target_ipv4/ipv6/hostname`. Cloud fields: `cloud_provider`, `cloud_account_id`, `cloud_region`, `target_service`. |
| `NetworkInjectorConfig` | Pydantic model (frozen) | Exactly one of `target_ipv4`, `target_ipv6`, or `target_hostname`. Validated by `model_validator`. |
| `CloudInjectorConfig` | Pydantic model (frozen) | `cloud_provider`, `cloud_account_id`, `cloud_region`, optional `target_service`. |
| `InjectorConfig` | Type alias | Union of `NetworkInjectorConfig` and `CloudInjectorConfig`. |
| `SignaturePayload` | Pydantic model | Wire body: list of `TargetSignatures`. |
| `SignatureOutputStructure` | Pydantic model | Outer callback envelope wrapping `SignaturePayload`. |
| `SignatureCallbackPayload` | Pydantic model (frozen) | POST envelope validated before transmission. Contains `execution_message`, `execution_status`, `execution_duration`, `execution_action`. |
| `ExpectationSignatureGroup` | Pydantic model (frozen) | Values bound to one expectation type (DETECTION/PREVENTION/VULNERABILITY). |
| `SignatureValue` | Pydantic model (frozen) | One observation: `signature_type` + `signature_value`. |
| `SignatureTarget` | Pydantic model (frozen) | Target identity on the wire: `agent`, `asset`, `asset_group`. |
| `TargetSignatures` | Pydantic model | A target plus its grouped signature values. |
| `ExtraSignatureData` | Pydantic model (frozen) | Optional extra fields keyed by expectation type (`detection`, `prevention`, `vulnerability`). |
| `ToolOutput` | Pydantic model (frozen) | Tool result envelope: `status`, `error_info`, `timeout_info`. |
| `ToolErrorInfo` | Pydantic model (frozen) | Crash report: `exit_code`, `crash_timestamp`. |
| `ToolTimeoutInfo` | Pydantic model (frozen) | Timeout report: `partial_results` list. |

---

*Back to [README](../README.md)*
