# API Overview

`xtm-oaev-sdk` organises its implementation under `xtm_oaev_sdk/_core/` (private). The root `xtm_oaev_sdk/__init__.py` re-exports exactly 107 stable symbols and is the only surface consumers should target.

```
xtm_oaev_sdk/
  __init__.py          ← public API surface (import from here)
  _core/
    errors.py
    utils.py
    client_protocol.py
    daemon_protocol.py
    ssl_utils.py
    security_domain/
    configuration/
    contracts/
    signatures/
```

The `_core` tree is an implementation detail. Its internal structure may change between releases; the root `__init__.py` will not.

---

## errors

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

## utils

Shared infrastructure utilities: logging, JSON encoding, field-presence validation, and dict manipulation.

### Protocols

| Symbol | Description |
|---|---|
| `AppLoggerProtocol` | `@runtime_checkable` protocol for logger services. Methods: `debug`, `info`, `warning`, `error`, `setup_logger_level`. Supports `__call__(name)` for per-module instances. |

### Key classes

| Symbol | Kind | Description |
|---|---|---|
| `EnhancedJSONEncoder` | Class | `json.JSONEncoder` subclass. Serialises `@dataclass` instances via `asdict()` and `BaseModel` instances via `model_dump()`. |
| `RequiredOptional` | Pydantic model (frozen) | Field-presence validator. Declare `required`, `optional`, and `exclusive` tuples; call `validate_attrs(data=...)` to enforce them. |
| `EncodedId` | `str` subclass | URL-safe percent-encoded identifier. Idempotent; accepts `str`, `int`, or another `EncodedId`. |

### Utility functions

| Symbol | Description |
|---|---|
| `copy_dict(*, src, dest)` | Flattens nested dicts into bracket-notation keys (`{"filters": {"type": "x"}}` → `dest["filters[type]"] = "x"`). Mutates `dest` in place. |
| `remove_none_from_dict(data)` | Returns a copy of `data` with all `None`-valued keys removed. |

---

## security_domain

Domain taxonomy for categorising signatures, injections, and detection scenarios.

### Enums

| Symbol | Kind | Members |
|---|---|---|
| `SecurityDomains` | Enum | `ENDPOINT`, `NETWORK`, `WEB_APP`, `EMAIL_INFILTRATION`, `DATA_EXFILTRATION`, `URL_FILTERING`, `CLOUD`, `TABLE_TOP`, `TOCLASSIFY` |

Each member value is a dict with `domain_name` (human-readable string) and `domain_color` (hex string for UI rendering).

```python
from xtm_oaev_sdk import SecurityDomains

SecurityDomains.NETWORK.value["domain_name"]   # "Network"
SecurityDomains.NETWORK.value["domain_color"]  # "#009933"
```

---

## client_protocol

Protocol defining the OpenAEV API client interface for dependency injection and testing.

### Protocols

| Symbol | Description |
|---|---|
| `BaseClient` | `@runtime_checkable` protocol. Defines the public surface an OpenAEV client must expose. Used by extension SDKs for type-hinting without coupling to the concrete `pyoaev.OpenAEV` class. |

---

## daemon_protocol

Behavioral contract for daemon runtimes (injectors and collectors). See [Daemon Protocol](daemon-protocol.md) for full documentation.

### Protocols

| Symbol | Description |
|---|---|
| `DaemonProtocol` | `@runtime_checkable` protocol. Methods: `start()`, `set_callback(callback)`, `get_id() -> str | None`. Both `CollectorDaemon` and `InjectorDaemon` satisfy this structurally via `BaseDaemon` inheritance. |

---

## ssl_utils

TLS/SSL helper functions for certificate chain handling and verification.

### Utility functions

| Symbol | Description |
|---|---|
| `ssl_cert_chain(url)` | Fetches the full certificate chain from a remote server. Returns list of PEM-encoded certificates. |
| `ssl_verify_locations(config)` | Returns appropriate CA bundle path or verification settings from configuration. |
| `is_memory_certificate(cert_data)` | Determines whether certificate data is an in-memory PEM string vs a file path. |
| `data_to_temp_file(data, suffix)` | Writes in-memory data to a named temporary file. Useful for passing PEM strings to libraries that expect file paths. |

---

## configuration

Hint-based configuration resolution with multi-source lookup (environment variables, YAML files, explicit overrides). Also exposes a protocol for testing and dependency injection, plus pre-built loaders for common OpenAEV connector patterns.

### Protocols

| Symbol | Description |
|---|---|
| `ConfigurationProtocol` | `@runtime_checkable` protocol. Methods: `get(key)`, `set(key, value)`, `schema()`. Any custom configuration implementation must satisfy this. |

### Key classes

| Symbol | Kind | Description |
|---|---|---|
| `ConfigurationHint` | Pydantic model (frozen) | Describes where a single config value can be found. Fields: `data` (override), `env` (env var name), `file_path` (YAML path list), `is_number` (coerce to int), `default`. Use `model_copy(update=...)` to derive modified hints. |
| `Configuration` | Class | Accepts a `dict[str, dict | str]` of hints and resolves values with priority: set() > env > YAML > default. |
| `BaseConfigModel` | Pydantic model | Base for typed config models with schema generation support. |
| `ConfigLoaderCollector` | Class | Pre-built loader for collector configuration keys (collector_id, collector_name, etc.). |
| `ConfigLoaderOAEV` | Class | Pre-built loader for OpenAEV platform connection keys (url, token, tenant_id). |
| `SettingsLoader` | Class | Generic settings loader supporting config files and environment variables. |
| `ConnectorConfigSchemaGenerator` | Class | Generates JSON Schema from typed config models for documentation and validation. |

### Sources

| Symbol | Kind | Description |
|---|---|---|
| `DictionarySource` | Class | Configuration source that reads from an in-memory dict. |
| `EnvironmentSource` | Class | Configuration source that reads from environment variables. |

### Validators

| Symbol | Kind | Description |
|---|---|---|
| `HttpUrlToString` | Annotated type | Pydantic validator that coerces `HttpUrl` to plain `str`. |
| `LogLevelToLower` | Annotated type | Pydantic validator that normalises log level strings to lowercase. |
| `TimedeltaInSeconds` | Annotated type | Pydantic validator that coerces `timedelta` to integer seconds. |

### Logging

| Symbol | Kind | Description |
|---|---|---|
| `AppLogger` | Class | Structured logger with JSON formatting support. |
| `CustomJsonFormatter` | Class | JSON log formatter for structured logging pipelines. |
| `setup_logging_config` | Function | Configures Python logging with appropriate handlers and formatters. |
| `logger` | Function | Factory function returning an `AppLogger` instance for a given level. |

---

## contracts

Fluent builder API for declaring injector/collector contract field schemas. Contracts describe the inputs an injector accepts and the outputs it produces.

### Protocols

| Symbol | Description |
|---|---|
| `ContractBuilderProtocol` | `@runtime_checkable` protocol. Chainable methods: `add_fields`, `add_outputs`, `mandatory`, `optional`, `mandatory_group`, `build_fields`, `build_outputs`. |

### Enums

| Symbol | Kind | Members |
|---|---|---|
| `ContractExpectationType` | Enum (8 members) | `text`, `document`, `article`, `challenge`, `manual`, `prevention`, `detection`, `vulnerability` |

`ContractExpectationType` covers the full expectation taxonomy for contract field definitions. This is distinct from `SignatureExpectationType` (3-member: `DETECTION`, `PREVENTION`, `VULNERABILITY`) used in the signature pipeline.

---

## signatures

The signature lifecycle subsystem: typed injector configs, frozen Pydantic models for every wire shape, enums, the `SignatureManager` orchestrator, and transport/manager protocols.

### Protocols

| Symbol | Description |
|---|---|
| `SignatureTransportProtocol` | `@runtime_checkable`. Single method: `send_signatures(inject_id, sig_output, execution_details, *, max_payload_size, logger)`. `pyoaev` implements this. |
| `SignatureManagerProtocol` | `@runtime_checkable`. Covers the full pipeline: `build_execution_signatures`, `post_execution_updates`, `send_signatures`, `resolve_container_ip`. |

### Key classes

| Symbol | Kind | Description |
|---|---|---|
| `SignatureManager` | Class | End-to-end orchestrator. Constructor: `(transport, logger=None, max_payload_size=5_242_880)`. See [Usage Examples](usage-examples.md#signatures). |
| `ExecutionDetails` | Pydantic model | Execution metadata: `start_time`, `end_time`, `execution_status`, `execution_action`. Computed: `execution_message`, `execution_duration`. |
| `ExecutionSignature` | Pydantic model | Flat per-target signature record. Network fields: `source_ipv4/ipv6`, `target_ipv4/ipv6/hostname`. Cloud fields: `cloud_provider`, `cloud_account_id`, `cloud_region`, `target_service`. |
| `NetworkInjectorConfig` | Pydantic model (frozen) | Exactly one of `target_ipv4`, `target_ipv6`, or `target_hostname`. Validated by `model_validator`. |
| `CloudInjectorConfig` | Pydantic model (frozen) | `cloud_provider`, `cloud_account_id`, `cloud_region`, optional `target_service`. |
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
| `SignatureType` | Class | Couples a `SignatureTypes` label with a `MatchTypes` policy. `make_struct_for_matching(data)` produces helper dicts. |
| `SignatureMatch` | Class | Stores match type and optional score threshold. |

### Enums

| Symbol | Kind | Members |
|---|---|---|
| `SignatureExpectationType` | Enum (3 members) | `DETECTION`, `PREVENTION`, `VULNERABILITY` |
| `InjectExecutionActions` | Enum (8 members) | `PREREQUISITE_CHECK`, `PREREQUISITE_EXECUTION`, `CLEANUP_EXECUTION`, `COMMAND_EXECUTION`, `DNS_RESOLUTION`, `FILE_EXECUTION`, `FILE_DROP`, `COMPLETE` |
| `MatchTypes` | Enum (2 members) | `MATCH_TYPE_FUZZY`, `MATCH_TYPE_SIMPLE` |
| `SignatureTypes` | Enum (15 members) | Field identifiers: `SIG_TYPE_SOURCE_IPV4_ADDRESS`, `SIG_TYPE_TARGET_HOSTNAME_ADDRESS`, `SIG_TYPE_CLOUD_PROVIDER`, `SIG_TYPE_AI_REQUEST_MARKER`, `SIG_TYPE_AI_TARGET_ENDPOINT`, etc. |

### Utility functions

| Symbol | Description |
|---|---|
| `build_network_configs(targets)` | Converts a heterogeneous list of `str`, `dict`, or `NetworkInjectorConfig` items into a typed `list[NetworkInjectorConfig]`. Strings are auto-classified as IPv4, IPv6, or hostname. |

---

## asset_types

Canonical asset taxonomy enums mirroring the OpenAEV backend. Typed `str` enums that drop straight into API dict payloads.

### Enums

| Symbol | Kind | Members |
|---|---|---|
| `AssetCategory` | Enum (12 members) | `HOST`, `CONTAINER_WORKLOAD`, `CLOUD_RESOURCE`, `WEB_APPLICATION`, `NETWORK_DEVICE`, `MOBILE_DEVICE`, `IOT_OT_DEVICE`, `IDENTITY`, `SAAS_APPLICATION`, `AI_TARGET`, `SECURITY_PLATFORM`, `GENERIC_ASSET` |
| `AssetSubCategory` | Enum (55 members) | Per-category subtypes: `SERVER`, `CONTAINER`, `COMPUTE`, `WEBSITE`, `ROUTER`, `LLM_MODEL`, `AI_AGENT`, etc. |
| `CloudProvider` | Enum (7 members) | `AWS`, `AZURE`, `GCP`, `OCI`, `ALIBABA`, `KUBERNETES`, `OTHER` |
| `AssetCriticality` | Enum (5 members) | `VERY_HIGH`, `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN` |

---

*Back to [README](../README.md)*
