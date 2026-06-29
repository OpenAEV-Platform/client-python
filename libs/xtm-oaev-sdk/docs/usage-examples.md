# Usage Examples

Practical, self-contained code snippets for each major use case. Replace placeholder values (UUIDs, URLs, credentials) with real data before running.

---

## Error Handling

### Catching the OpenAEVError hierarchy

```python
from xtm_oaev_sdk import (
    OpenAEVError,
    OpenAEVAuthenticationError,
    OpenAEVHttpError,
    OpenAEVGetError,
    SignatureTransmissionError,
    ConfigurationError,
)

def call_platform_api() -> None:
    raise OpenAEVGetError("Not Found", response_code=404)

try:
    call_platform_api()
except OpenAEVAuthenticationError as e:
    # Token expired or missing permissions — re-authenticate or abort
    print(f"Auth failure: {e}")
except OpenAEVGetError as e:
    # GET-specific failure; e.response_code is the HTTP status
    print(f"GET failed ({e.response_code}): {e.error_message}")
except SignatureTransmissionError as e:
    # Platform rejected signatures — check payload and retry logic
    print(f"Signature delivery failed: {e}")
except ConfigurationError as e:
    # Missing or invalid configuration values at startup
    print(f"Bad config: {e}")
except OpenAEVError as e:
    # Catch-all for any SDK error
    print(f"SDK error: {e}")
```

### Using the `on_http_error` decorator

```python
from xtm_oaev_sdk import OpenAEVCreateError, OpenAEVHttpError, on_http_error

class InjectorClient:
    @on_http_error(OpenAEVCreateError)
    def create_inject(self, payload: dict) -> dict:
        # Any OpenAEVHttpError raised here is automatically converted
        # into OpenAEVCreateError with the original context preserved.
        raise OpenAEVHttpError("Bad Request", response_code=400)
```

### Extracting structured error context

`OpenAEVError.__str__` automatically extracts human-readable messages from JSON response bodies:

```python
import json
from xtm_oaev_sdk import OpenAEVError

raw_body = json.dumps({"error": {"message": "Token expired"}}).encode()
err = OpenAEVError("Unauthorized", response_code=401, response_body=raw_body)
print(str(err))  # "401: Token expired"
```

---

## Configuration

### Creating a `ConfigurationHint`

`ConfigurationHint` is a frozen Pydantic model. Build one per configuration key and pass the collection to `Configuration`.

```python
from xtm_oaev_sdk import ConfigurationHint

# Read from environment variable, fall back to "info"
log_hint = ConfigurationHint(env="LOG_LEVEL", default="info")

# Read from YAML file path connector.url, fall back to localhost
url_hint = ConfigurationHint(
    env="API_URL",
    file_path=["connector", "url"],
    default="http://localhost:8080",
)

# Numeric hint (coerces string env var to int)
timeout_hint = ConfigurationHint(env="TIMEOUT_SECONDS", is_number=True, default="30")

# ConfigurationHint is frozen — derive modified copies with model_copy
debug_hint = log_hint.model_copy(update={"data": "debug"})
```

### Resolving configuration values

```python
from xtm_oaev_sdk import Configuration, ConfigurationProtocol

config = Configuration(
    {
        "log_level": {"env": "LOG_LEVEL", "default": "info"},
        "api_url":   {"env": "API_URL", "default": "http://localhost:8080"},
        "timeout":   {"env": "TIMEOUT", "is_number": True, "default": "30"},
    }
)

# Type: ConfigurationProtocol — works anywhere the protocol is expected
c: ConfigurationProtocol = config

print(c.get("log_level"))   # "info" (or value of LOG_LEVEL env var)
print(c.get("timeout"))     # 30 (int, because is_number=True)

# Override a value at runtime
c.set("log_level", "debug")
print(c.get("log_level"))   # "debug"
```

### Implementing `ConfigurationProtocol` for testing

```python
from typing import Any
from xtm_oaev_sdk import ConfigurationProtocol

class StubConfig:
    """Minimal in-memory config for unit tests."""

    def __init__(self, values: dict[str, Any]) -> None:
        self._values = values

    def get(self, key: str) -> Any:
        return self._values.get(key)

    def set(self, key: str, value: Any) -> None:
        self._values[key] = value

    def schema(self) -> dict[str, Any]:
        return {}

# Verify structural compatibility at runtime
assert isinstance(StubConfig({}), ConfigurationProtocol)
```

---

## Contracts

### Building a contract with `ContractBuilder`

```python
from xtm_oaev_sdk import ContractBuilder, ContractBuilderProtocol, ContractExpectationType
from xtm_oaev_sdk import (
    ContractText,
    ContractCheckbox,
    ContractSelect,
    ContractAsset,
    ContractExpectations,
    Expectation,
    SupportedLanguage,
    ContractConfig,
    Contract,
)

builder = ContractBuilder()

(
    builder
    .mandatory(ContractText(key="target_url", label="Target URL"))
    .optional(ContractCheckbox(key="verify_ssl", label="Verify SSL", defaultValue=True))
    .mandatory(
        ContractSelect(
            key="protocol",
            label="Protocol",
            choices={"http": "HTTP", "https": "HTTPS"},
        )
    )
)

fields = builder.build_fields()
print(len(fields))   # 3

# mandatory_group: all fields in the group are required together
group_builder = ContractBuilder()
group_builder.mandatory_group([
    ContractText(key="username", label="Username"),
    ContractText(key="password", label="Password"),
])
grouped_fields = group_builder.build_fields()
# Both fields carry mandatoryGroups=["username", "password"]
```

### Coding against `ContractBuilderProtocol`

```python
from xtm_oaev_sdk import ContractBuilderProtocol

def register_contract(builder: ContractBuilderProtocol) -> list:
    """Accepts any builder satisfying the protocol."""
    return builder.build_fields()
```

---

## Signatures

### Full lifecycle: build, update, ship

```python
import logging
from xtm_oaev_sdk import (
    SignatureManager,
    ExecutionDetails,
    ExtraSignatureData,
    build_network_configs,
    SignatureTransportProtocol,
    SignatureOutputStructure,
)

# --- Transport (see next section for a full implementation sketch) ---
transport: SignatureTransportProtocol = ...  # provided by pyoaev

manager = SignatureManager(
    transport=transport,
    logger=logging.getLogger("my_injector"),
    max_payload_size=5_242_880,  # 5 MiB (default)
)

# --- Step 1: build pre-execution signatures ---
configs = build_network_configs(["192.168.1.10", "10.0.0.5", "target.example.com"])
exec_sigs = manager.build_execution_signatures(configs)
# Returns list[ExecutionSignature] because multiple configs were passed

# --- Step 2: record start, let the tool run ---
details = ExecutionDetails()
# ... run your tool here ...

# --- Step 3: merge tool output into signatures ---
tool_result = {
    "status": "success",
    # For failures: "error_info": {"exit_code": 1, "crash_timestamp": "2026-01-01T00:00:00Z"}
    # For timeouts: "timeout_info": {"partial_results": ["10.0.0.5"]}
}
manager.post_execution_updates(details, exec_sigs, tool_result)

# --- Step 4: build the wire payload ---
# targets_meta items must expose .agent_id, .asset_id, .asset_group_id
class TargetMeta:
    def __init__(self, agent_id, asset_id, asset_group_id=None):
        self.agent_id = agent_id
        self.asset_id = asset_id
        self.asset_group_id = asset_group_id

targets = [
    TargetMeta("agent-uuid-1", "asset-uuid-a"),
    TargetMeta("agent-uuid-1", "asset-uuid-b"),
    TargetMeta("agent-uuid-1", "asset-uuid-c"),
]

payload = SignatureManager.build_payload(
    exec_sigs,
    targets,
    expectation_types=["DETECTION", "PREVENTION"],
    extra_signatures=ExtraSignatureData(
        detection={"custom_field": "extra_value"},
    ),
)

# --- Step 5: transmit ---
manager.send_signatures("inject-uuid-xyz", details, payload)
```

### Cloud inject lifecycle

```python
from xtm_oaev_sdk import (
    SignatureManager,
    CloudInjectorConfig,
    ExecutionDetails,
)

transport: SignatureTransportProtocol = ...

manager = SignatureManager(transport=transport)

cloud_configs = [
    CloudInjectorConfig(
        cloud_provider="aws",
        cloud_account_id="123456789012",
        cloud_region="eu-west-1",
        target_service="s3",
    ),
    CloudInjectorConfig(
        cloud_provider="aws",
        cloud_account_id="123456789012",
        cloud_region="us-east-1",
        target_service="ec2",
    ),
]

exec_sigs = manager.build_execution_signatures(cloud_configs)
details = ExecutionDetails()
# ... execute cloud tool ...
manager.post_execution_updates(details, exec_sigs, {"status": "success"})
```

### Single-target shorthand

When a single `InjectorConfig` is passed, `build_execution_signatures` returns a single `ExecutionSignature` (not a list):

```python
from xtm_oaev_sdk import SignatureManager, NetworkInjectorConfig

manager = SignatureManager(transport=transport)
single_config = NetworkInjectorConfig(target_ipv4="10.0.0.1")
sig = manager.build_execution_signatures(single_config)
# sig is ExecutionSignature, not list[ExecutionSignature]
```

---

## Implementing `SignatureTransportProtocol`

`pyoaev` ships a production implementation. The sketch below shows how to wire one in from scratch (useful for testing or alternate backends):

```python
import logging
from xtm_oaev_sdk import (
    SignatureTransportProtocol,
    SignatureOutputStructure,
    ExecutionDetails,
    SignatureTransmissionError,
)

class HttpSignatureTransport:
    """Minimal transport: POST signatures to a platform callback endpoint."""

    def __init__(self, base_url: str, token: str) -> None:
        self._base_url = base_url
        self._token = token

    def send_signatures(
        self,
        inject_id: str,
        sig_output: SignatureOutputStructure,
        execution_details: ExecutionDetails,
        *,
        max_payload_size: int,
        logger: logging.Logger,
    ) -> None:
        import json
        import urllib.request

        url = f"{self._base_url}/api/injects/{inject_id}/execution"
        body = json.dumps({
            "execution_output_structured": sig_output.model_dump_json(exclude_none=True),
            "execution_status": execution_details.execution_status,
            "execution_duration": int(execution_details.execution_duration),
        }).encode()

        req = urllib.request.Request(
            url,
            data=body,
            headers={"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status >= 400:
                    raise SignatureTransmissionError(
                        f"Platform rejected signatures: {resp.status}",
                        response_code=resp.status,
                    )
        except OSError as e:
            raise SignatureTransmissionError(str(e)) from e

# Verify protocol conformance at runtime
assert isinstance(HttpSignatureTransport("http://localhost", "tok"), SignatureTransportProtocol)
```

---

## RequiredOptional

`RequiredOptional` validates field presence in API payloads. Useful when building dynamic request dicts where certain keys are mandatory, others optional, and some mutually exclusive.

```python
from xtm_oaev_sdk import RequiredOptional

# Scenario: a payload must have "name" and "type", and exactly one of "id" or "key"
validator = RequiredOptional(
    required=("name", "type"),
    exclusive=("id", "key"),
)

# Valid
validator.validate_attrs(data={"name": "scanner", "type": "network", "id": "abc123"})

# Missing required field → AttributeError: Missing attributes: type
try:
    validator.validate_attrs(data={"name": "scanner", "id": "abc123"})
except AttributeError as e:
    print(e)

# Both exclusive fields provided → AttributeError
try:
    validator.validate_attrs(data={"name": "x", "type": "y", "id": "1", "key": "2"})
except AttributeError as e:
    print(e)

# Skip a required field during partial updates
validator.validate_attrs(
    data={"type": "network", "id": "abc123"},
    excludes=["name"],  # name is excluded from the required check
)
```

`RequiredOptional` is a frozen Pydantic model. Instances are immutable after creation.

---

## EncodedId

URL-safe identifiers for path segments:

```python
from xtm_oaev_sdk import EncodedId

safe = EncodedId("inject type/special chars")
print(safe)        # "inject%20type%2Fspecial%20chars"
print(EncodedId(42))  # "42"

# Encoding is idempotent
print(EncodedId(safe) is safe)  # True
```

---

*Back to [README](../README.md) | [API Overview](api-overview.md) | [Migration Guide](migration-guide.md)*
