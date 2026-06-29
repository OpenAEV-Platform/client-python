# Migration Guide

Target audience: developers currently using `pyoaev` directly who need to adopt `xtm-oaev-sdk` as the shared core library. This covers import path changes, renamed symbols, and behavioral differences introduced in the split.

During the transition period, `pyoaev` provides backward-compatible shims that re-export the affected symbols with a `DeprecationWarning`. You can migrate incrementally: update one import at a time without breaking running connectors.

---

## Import Path Changes

### Errors

| Old (`pyoaev`) | New (`xtm-oaev-sdk`) |
|---|---|
| `from pyoaev.exceptions import OpenAEVError` | `from xtm_oaev_sdk import OpenAEVError` |
| `from pyoaev.exceptions import OpenAEVAuthenticationError` | `from xtm_oaev_sdk import OpenAEVAuthenticationError` |
| `from pyoaev.exceptions import OpenAEVHttpError` | `from xtm_oaev_sdk import OpenAEVHttpError` |
| `from pyoaev.exceptions import OpenAEVParsingError` | `from xtm_oaev_sdk import OpenAEVParsingError` |
| `from pyoaev.exceptions import RedirectError` | `from xtm_oaev_sdk import RedirectError` |
| `from pyoaev.exceptions import OpenAEVHeadError` | `from xtm_oaev_sdk import OpenAEVHeadError` |
| `from pyoaev.exceptions import OpenAEVGetError` | `from xtm_oaev_sdk import OpenAEVGetError` |
| `from pyoaev.exceptions import OpenAEVUpdateError` | `from xtm_oaev_sdk import OpenAEVUpdateError` |
| `from pyoaev.exceptions import OpenAEVListError` | `from xtm_oaev_sdk import OpenAEVListError` |
| `from pyoaev.exceptions import OpenAEVCreateError` | `from xtm_oaev_sdk import OpenAEVCreateError` |
| `from pyoaev.exceptions import SignatureTransmissionError` | `from xtm_oaev_sdk import SignatureTransmissionError` |
| `from pyoaev.exceptions import ConfigurationError` | `from xtm_oaev_sdk import ConfigurationError` |
| `from pyoaev.exceptions import on_http_error` | `from xtm_oaev_sdk import on_http_error` |

### Utils

| Old (`pyoaev`) | New (`xtm-oaev-sdk`) |
|---|---|
| `from pyoaev.utils import AppLoggerProtocol` | `from xtm_oaev_sdk import AppLoggerProtocol` |
| `from pyoaev.utils import EnhancedJSONEncoder` | `from xtm_oaev_sdk import EnhancedJSONEncoder` |
| `from pyoaev.utils import RequiredOptional` | `from xtm_oaev_sdk import RequiredOptional` |
| `from pyoaev.utils import EncodedId` | `from xtm_oaev_sdk import EncodedId` |
| `from pyoaev.utils import copy_dict` | `from xtm_oaev_sdk import copy_dict` |
| `from pyoaev.utils import remove_none_from_dict` | `from xtm_oaev_sdk import remove_none_from_dict` |

### Signatures

| Old (`pyoaev`) | New (`xtm-oaev-sdk`) |
|---|---|
| `from pyoaev.signatures import SignatureManager` | `from xtm_oaev_sdk import SignatureManager` |
| `from pyoaev.signatures.models import ExecutionDetails` | `from xtm_oaev_sdk import ExecutionDetails` |
| `from pyoaev.signatures.models import ExecutionSignature` | `from xtm_oaev_sdk import ExecutionSignature` |
| `from pyoaev.signatures.models import SignaturePayload` | `from xtm_oaev_sdk import SignaturePayload` |
| `from pyoaev.signatures.models import SignatureOutputStructure` | `from xtm_oaev_sdk import SignatureOutputStructure` |
| `from pyoaev.signatures.models import SignatureCallbackPayload` | `from xtm_oaev_sdk import SignatureCallbackPayload` |
| `from pyoaev.signatures.models import SignatureValue` | `from xtm_oaev_sdk import SignatureValue` |
| `from pyoaev.signatures.models import SignatureTarget` | `from xtm_oaev_sdk import SignatureTarget` |
| `from pyoaev.signatures.models import TargetSignatures` | `from xtm_oaev_sdk import TargetSignatures` |
| `from pyoaev.signatures.models import ExpectationSignatureGroup` | `from xtm_oaev_sdk import ExpectationSignatureGroup` |
| `from pyoaev.signatures.models import ExtraSignatureData` | `from xtm_oaev_sdk import ExtraSignatureData` |
| `from pyoaev.signatures.models import NetworkInjectorConfig` | `from xtm_oaev_sdk import NetworkInjectorConfig` |
| `from pyoaev.signatures.models import CloudInjectorConfig` | `from xtm_oaev_sdk import CloudInjectorConfig` |
| `from pyoaev.signatures.models import ToolOutput` | `from xtm_oaev_sdk import ToolOutput` |
| `from pyoaev.signatures.models import ToolErrorInfo` | `from xtm_oaev_sdk import ToolErrorInfo` |
| `from pyoaev.signatures.models import ToolTimeoutInfo` | `from xtm_oaev_sdk import ToolTimeoutInfo` |
| `from pyoaev.signatures.models import build_network_configs` | `from xtm_oaev_sdk import build_network_configs` |
| `from pyoaev.signatures.types import ExpectationType` | `from xtm_oaev_sdk import SignatureExpectationType` (renamed, see below) |
| `from pyoaev.signatures.types import InjectExecutionActions` | `from xtm_oaev_sdk import InjectExecutionActions` |
| `from pyoaev.signatures.types import MatchTypes` | `from xtm_oaev_sdk import MatchTypes` |
| `from pyoaev.signatures.types import SignatureTypes` | `from xtm_oaev_sdk import SignatureTypes` |

### Configuration

| Old (`pyoaev`) | New (`xtm-oaev-sdk`) |
|---|---|
| `from pyoaev.configuration import ConfigurationHint` | `from xtm_oaev_sdk import ConfigurationHint` |
| `from pyoaev.configuration import ConfigurationProtocol` | `from xtm_oaev_sdk import ConfigurationProtocol` |

### Contracts

| Old (`pyoaev`) | New (`xtm-oaev-sdk`) |
|---|---|
| `from pyoaev.contracts import ContractBuilderProtocol` | `from xtm_oaev_sdk import ContractBuilderProtocol` |
| `from pyoaev.contracts import ExpectationType` | `from xtm_oaev_sdk import ContractExpectationType` (renamed, see below) |

---

## Behavioral Changes

### `SignatureManager` constructor

The `client` parameter (a concrete `OpenAEV` instance) has been replaced by `transport` (a `SignatureTransportProtocol`).

**Before:**

```python
from pyoaev import OpenAEV
from pyoaev.signatures import SignatureManager

client = OpenAEV(...)
manager = SignatureManager(client=client)
```

**After:**

```python
from xtm_oaev_sdk import SignatureManager, SignatureTransportProtocol

# pyoaev provides a transport adapter; pass it here
transport: SignatureTransportProtocol = pyoaev_client.signature_transport()
manager = SignatureManager(transport=transport)
```

This decouples the signature pipeline from the HTTP client, making `SignatureManager` independently testable against any transport implementation.

### `ExpectationType` renamed and split into two enums

The old `ExpectationType` served two distinct purposes. It has been split into two separate, non-overlapping enums:

| Old | New | Members | Used in |
|---|---|---|---|
| `ExpectationType` (pyoaev signatures) | `SignatureExpectationType` | `DETECTION`, `PREVENTION`, `VULNERABILITY` (3) | Signature pipeline, wire payload |
| `ExpectationType` (pyoaev contracts) | `ContractExpectationType` | `text`, `document`, `article`, `challenge`, `manual`, `prevention`, `detection`, `vulnerability` (8) | Contract field definitions |

**Before:**

```python
from pyoaev.signatures.types import ExpectationType
# or
from pyoaev.contracts import ExpectationType
```

**After:**

```python
# For signatures (3-member):
from xtm_oaev_sdk import SignatureExpectationType
types = ["DETECTION", "PREVENTION"]

# For contracts (8-member):
from xtm_oaev_sdk import ContractExpectationType
contract_type = ContractExpectationType.detection
```

### `ConfigurationHint` is now frozen

`ConfigurationHint` is now a frozen Pydantic model. Direct attribute mutation no longer works.

**Before:**

```python
hint = ConfigurationHint(env="LOG_LEVEL", default="info")
hint.data = "debug"  # mutated in place
```

**After:**

```python
from xtm_oaev_sdk import ConfigurationHint

hint = ConfigurationHint(env="LOG_LEVEL", default="info")
# Derive a new instance with the override applied
debug_hint = hint.model_copy(update={"data": "debug"})
```

The `Configuration.set()` method handles this internally, so calling `config.set("log_level", "debug")` still works unchanged.

### `RequiredOptional` is now a frozen Pydantic model

`RequiredOptional` previously accepted ad-hoc mutation of its `required`, `optional`, and `exclusive` tuples. It is now a frozen `BaseModel`.

**Before:**

```python
from pyoaev.utils import RequiredOptional

ro = RequiredOptional()
ro.required = ("name", "type")
```

**After:**

```python
from xtm_oaev_sdk import RequiredOptional

ro = RequiredOptional(required=("name", "type"), exclusive=("id", "key"))
# All fields must be set at construction time; model is immutable after that
```

### Signature models are now frozen (immutable DTOs)

The following 10 models are now frozen (`model_config = ConfigDict(frozen=True)`):

- `ToolErrorInfo`
- `ToolTimeoutInfo`
- `ToolOutput`
- `SignatureValue`
- `ExpectationSignatureGroup`
- `ExtraSignatureData`
- `SignatureTarget`
- `SignatureCallbackPayload`
- `NetworkInjectorConfig`
- `CloudInjectorConfig`

If your code mutated fields on these models after construction, switch to `model_copy(update=...)`:

**Before:**

```python
config = NetworkInjectorConfig(target_ipv4="10.0.0.1")
config.target_ipv4 = "10.0.0.2"  # mutated in place — no longer allowed
```

**After:**

```python
from xtm_oaev_sdk import NetworkInjectorConfig

config = NetworkInjectorConfig(target_ipv4="10.0.0.1")
updated = config.model_copy(update={"target_ipv4": "10.0.0.2"})
```

Note: `ExecutionDetails` and `ExecutionSignature` are **not** frozen because `SignatureManager` updates them after tool execution via `post_execution_updates`.

---

## Deprecation Shims in `pyoaev`

During the transition period `pyoaev` re-exports renamed symbols with `DeprecationWarning` to avoid hard breaks. The shims will be removed in a future `pyoaev` major release. To identify affected imports in your codebase, run with warnings enabled:

```bash
python -W error::DeprecationWarning -m your_connector
```

Any `DeprecationWarning` pointing at `pyoaev.exceptions`, `pyoaev.signatures`, `pyoaev.utils`, or `pyoaev.contracts` indicates an import that needs updating.

---

## New Protocols (no shim needed)

These are new abstractions added during the SDK split. They have no legacy import path — no shim is required.

### DaemonProtocol

`DaemonProtocol` captures the behavioral contract shared by `CollectorDaemon` and injector daemon runtimes. It exposes 3 public methods: `start()`, `set_callback()`, `get_id()`.

```python
from xtm_oaev_sdk import DaemonProtocol
# or from either extension SDK:
from injectors_sdk import DaemonProtocol
from collectors_sdk import DaemonProtocol
```

pyoaev's `BaseDaemon` satisfies this Protocol structurally with zero changes. See [daemon-protocol.md](daemon-protocol.md) for details.

### BaseClient

`BaseClient` captures the HTTP client behavioral contract. See [api-overview.md](api-overview.md).

---

## Extension SDKs (no shim needed)

The following symbols were never in `pyoaev` — they are new extractions from other sources. No legacy import path exists, no deprecation shim is needed.

| Symbol | Package | Source |
|---|---|---|
| `BaseInjector` | `injectors-sdk` | New Protocol (injector lifecycle contract) |
| `BaseCollector` | `collectors-sdk` | Extracted from `collectors_template/template/` |
| `BasicCollectorEngine` | `collectors-sdk` | Extracted from `collectors_template/template/` |
| All collector Protocols, models, errors | `collectors-sdk` | Extracted from `collectors_template/template/` |
| CLI Engine (`CliEngine`, `CommandSpec`, etc.) | `injectors-sdk` | New (from PoC) |

### What stays in pyoaev (not extracted)

| Symbol | Why |
|---|---|
| `CollectorDaemon` | Platform runtime — constructs OpenAEV API client, spawns PingAlive thread, manages scheduler loop |
| `BaseDaemon` | Abstract base for all daemon types — tightly coupled to `OpenAEV` client constructor |
| `OpenAEVCollectorHelper` | Legacy helper wrapping `CollectorDaemon` directly |
| `OpenAEVInjectorHelper` | Legacy helper wrapping injector daemon lifecycle |

These remain at `from pyoaev.daemons import CollectorDaemon` / `BaseDaemon`. All 17+ concrete collectors still import from this path unchanged.

---

*Back to [README](../README.md) | [API Overview](api-overview.md) | [Usage Examples](usage-examples.md)*
