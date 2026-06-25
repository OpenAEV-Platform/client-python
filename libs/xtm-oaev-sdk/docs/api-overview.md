# API Overview

`xtm-oaev-sdk` organises its implementation under `xtm_oaev_sdk/_core/` (private). The root `xtm_oaev_sdk/__init__.py` re-exports exactly 51 stable symbols and is the only surface consumers should target.

```
xtm_oaev_sdk/
  __init__.py          ← public API surface (import from here)
  _core/
    errors.py
    utils.py
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

## configuration

Hint-based configuration resolution with multi-source lookup (environment variables, YAML files, explicit overrides). Also exposes a protocol for testing and dependency injection.

### Protocols

| Symbol | Description |
|---|---|
| `ConfigurationProtocol` | `@runtime_checkable` protocol. Methods: `get(key)`, `set(key, value)`, `schema()`. Any custom configuration implementation must satisfy this. |

### Key classes

| Symbol | Kind | Description |
|---|---|---|
| `ConfigurationHint` | Pydantic model (frozen) | Describes where a single config value can be found. Fields: `data` (override), `env` (env var name), `file_path` (YAML path list), `is_number` (coerce to int), `default`. Use `model_copy(update=...)` to derive modified hints. |

The concrete `Configuration` class (not re-exported from the root) accepts a `dict[str, dict | str]` of hints and resolves values in this priority order:

1. Explicit `set()` override
2. Environment variable (`env` hint)
3. YAML file value (`file_path` hint)
4. Default value (`default` hint)

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
| `SignatureTypes` | Enum (13 members) | Field identifiers: `SIG_TYPE_SOURCE_IPV4_ADDRESS`, `SIG_TYPE_TARGET_HOSTNAME_ADDRESS`, `SIG_TYPE_CLOUD_PROVIDER`, etc. |

### Utility functions

| Symbol | Description |
|---|---|
| `build_network_configs(targets)` | Converts a heterogeneous list of `str`, `dict`, or `NetworkInjectorConfig` items into a typed `list[NetworkInjectorConfig]`. Strings are auto-classified as IPv4, IPv6, or hostname. |

---

*Back to [README](../README.md)*
