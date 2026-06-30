# Configuration

The configuration subsystem resolves values from multiple sources with a declared priority order, exposes a `@runtime_checkable` protocol for testing, and ships pre-built loaders for the two common OpenAEV connector configuration shapes.

---

## Core concept: hints

Configuration is driven by `ConfigurationHint` instances. Each hint describes *where* a single value can be found and what to do when it is absent.

```python
from xtm_second_oaev_sdk import ConfigurationHint

# From environment variable, fall back to "info"
log_hint = ConfigurationHint(env="LOG_LEVEL", default="info")

# From YAML path connector.url, or environment variable, with default
url_hint = ConfigurationHint(
    env="API_URL",
    file_path=["connector", "url"],
    default="http://localhost:8080",
)

# Numeric hint — string env var is coerced to int
timeout_hint = ConfigurationHint(env="TIMEOUT_SECONDS", is_number=True, default="30")
```

`ConfigurationHint` is a **frozen Pydantic model**. Instances are immutable; derive modified copies with `model_copy(update=...)`:

```python
# Override the data field on an existing hint without mutation
debug_hint = log_hint.model_copy(update={"data": "debug"})
```

### Fields

| Field | Type | Description |
|---|---|---|
| `data` | `str \| None` | Direct override value. Takes highest priority when set. |
| `env` | `str \| None` | Environment variable name to look up. |
| `file_path` | `list[str] \| None` | Key path into a YAML config file (e.g. `["connector", "url"]`). |
| `is_number` | `bool` | When `True`, coerces the resolved string value to `int`. |
| `default` | `str \| None` | Fallback value when all other sources are absent. |

### Resolution priority

```
set() call → data override → env var → YAML file path → default
```

---

## Configuration

`Configuration` accepts a mapping of hint definitions and resolves values on demand.

```python
from xtm_second_oaev_sdk import Configuration, ConfigurationProtocol

config = Configuration(
    {
        "log_level": {"env": "LOG_LEVEL", "default": "info"},
        "api_url":   {"env": "API_URL", "default": "http://localhost:8080"},
        "timeout":   {"env": "TIMEOUT", "is_number": True, "default": "30"},
    }
)

# Configuration satisfies ConfigurationProtocol structurally
c: ConfigurationProtocol = config

print(c.get("log_level"))   # "info" (or value of LOG_LEVEL env var)
print(c.get("timeout"))     # 30 (int, because is_number=True)

# Override a value at runtime
c.set("log_level", "debug")
print(c.get("log_level"))   # "debug"

# Produce a JSON-serialisable schema dict (for documentation/validation)
print(c.schema())
```

---

## ConfigurationProtocol

`@runtime_checkable` protocol satisfied by `Configuration` and any custom implementation.

```python
@runtime_checkable
class ConfigurationProtocol(Protocol):
    def get(self, key: str) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...
    def schema(self) -> dict[str, Any]: ...
```

Implement this for testing without loading real environment variables or YAML files:

```python
from typing import Any
from xtm_second_oaev_sdk import ConfigurationProtocol

class StubConfig:
    def __init__(self, values: dict[str, Any]) -> None:
        self._values = values

    def get(self, key: str) -> Any:
        return self._values.get(key)

    def set(self, key: str, value: Any) -> None:
        self._values[key] = value

    def schema(self) -> dict[str, Any]:
        return {}

assert isinstance(StubConfig({}), ConfigurationProtocol)  # True
```

---

## SettingsLoader

`SettingsLoader` is a generic pydantic-settings–based loader that supports config files and environment variables. It is the underlying engine behind `ConfigLoaderCollector` and `ConfigLoaderOAEV`.

```python
from xtm_second_oaev_sdk import SettingsLoader

class MySettings(SettingsLoader):
    api_url: str = "http://localhost:8080"
    log_level: str = "info"
    timeout: int = 30

    model_config = {
        "env_prefix": "MY_CONNECTOR_",
    }

settings = MySettings()
print(settings.api_url)   # reads MY_CONNECTOR_API_URL or falls back to default
```

---

## Pre-built loaders

Two ready-made loaders cover the two configuration shapes found in every OpenAEV connector.

### ConfigLoaderOAEV

Loads the platform connection settings:

```python
from xtm_second_oaev_sdk import ConfigLoaderOAEV

oaev_config = ConfigLoaderOAEV()
# Reads: OAEV_URL, OAEV_TOKEN, OAEV_TENANT_ID (or YAML equivalents)
print(oaev_config.url)
print(oaev_config.token)
```

### ConfigLoaderCollector

Loads the collector registration settings:

```python
from xtm_second_oaev_sdk import ConfigLoaderCollector

collector_config = ConfigLoaderCollector()
# Reads: COLLECTOR_ID, COLLECTOR_NAME, LOG_LEVEL, etc.
print(collector_config.collector_id)
print(collector_config.collector_name)
```

---

## Sources

`Configuration` resolves values from declarative hint objects. Two source classes back specific lookup strategies and can also be used directly when building custom loaders:

| Symbol | Description |
|---|---|
| `DictionarySource` | Reads from an in-memory `dict`. Useful in tests or when config is built programmatically at runtime. |
| `EnvironmentSource` | Reads from `os.environ`. Used internally by `Configuration` when a hint's `env` field is set. |

---

## BaseConfigModel

`BaseConfigModel` is the base for typed configuration models with schema generation support. Extend it to declare your connector's configuration shape as a Pydantic model:

```python
from xtm_second_oaev_sdk import BaseConfigModel, HttpUrlToString, LogLevelToLower, TimedeltaInSeconds
from datetime import timedelta
from typing import Annotated

class MyConnectorConfig(BaseConfigModel):
    api_url: Annotated[str, HttpUrlToString]
    log_level: Annotated[str, LogLevelToLower] = "info"
    poll_interval: Annotated[int, TimedeltaInSeconds] = 60
```

---

## Type coercions

Three annotated type aliases normalise incoming values before they reach your model fields:

| Symbol | Input type | Output type | Behaviour |
|---|---|---|---|
| `HttpUrlToString` | `HttpUrl` (Pydantic) | `str` | Converts a validated Pydantic `HttpUrl` object to a plain string, so HTTP clients can consume it without extra conversion |
| `LogLevelToLower` | `str` | `str` | Normalises log level strings to lowercase (`"INFO"` → `"info"`) |
| `TimedeltaInSeconds` | `timedelta` | `int` | Converts a `timedelta` to its total integer seconds (`timedelta(minutes=5)` → `300`) |

---

## ConnectorConfigSchemaGenerator

`ConnectorConfigSchemaGenerator` generates a JSON Schema document from a `BaseConfigModel` subclass. Use this to produce documentation or validation artefacts for your connector's configuration:

```python
from xtm_second_oaev_sdk import ConnectorConfigSchemaGenerator, BaseConfigModel

class MyConfig(BaseConfigModel):
    api_url: str
    log_level: str = "info"

generator = ConnectorConfigSchemaGenerator(MyConfig)
schema = generator.generate()
# Returns a dict conforming to JSON Schema Draft 7 / OpenAPI 3.1
```

---

## CONFIGURATION_TYPES

`CONFIGURATION_TYPES` is a dict registry mapping type-string keys to Python types. It is used internally by `ConnectorConfigSchemaGenerator` and `BaseConfigModel` to resolve type annotations during schema generation.

---

*Back to [README](../README.md) | [API Overview](api-overview.md)*
