# xtm-oaev-sdk

The **common SDK** of the OpenAEV connector ecosystem. Everything collectors and
injectors share lives here, and none of it cares which HTTP client you run.

`pyoaev` used to be a monolith. One package carried the OpenAEV API client *and* the
configuration system, the contract builder, the signature pipeline, the daemon
runtime, the error hierarchy and a drawer of assorted helpers. This SDK cuts the
shared, client-free half out of it. The stack now reads:

```
xtm-oaev-sdk     shared vocabulary and runtime (this package)
├── collectors-sdk   collector runtime   (OpenAEV-Platform/collectors, libs/)
├── injectors-sdk    injector runtime    (OpenAEV-Platform/injectors, libs/)
└── pyoaev           the OpenAEV HTTP client, plus deprecation shims of its former code
```

The SDK never depends on `pyoaev`. When it has to talk to the platform, the API
client gets **injected** (`BaseClient` protocol); `pyoaev.OpenAEV` is just one
implementation of it.

## What's inside

| Capability | Public API |
|---|---|
| common | `OpenAEVError` and its subclasses, `AppLogger`, `logger`, `setup_logging_config`, `CustomJsonFormatter`, `EnhancedJSONEncoder`, `copy_dict`, `remove_none_from_dict`, SSL helpers, asset and security-domain enums, `BaseClient` / `DaemonProtocol` / `AppLoggerProtocol` |
| configuration | `Configuration`, `ConfigurationHint`, `SettingsLoader`, `BaseConfigModel`, `ConfigLoaderOAEV`, `ConfigLoaderCollector`, `ConnectorConfigSchemaGenerator`, sources, serializer types |
| contracts | `Contract`, `ContractBuilder`, `VariableHelper`, `prepare_contracts`, every contract element (`ContractText`, `ContractSelect`, …) and enum, credential references (`CredentialType`, `ContractReferencedCredential`, `build_single_referenced_credential_element`) |
| signatures | `SignatureManager`, `build_network_configs`, `build_marker`, matching types, the inbound I/O models and the port I/O wire models (`PORT_IO_CONTRACT_VERSION`) |
| daemons | `BaseDaemon`, `PingAlive` |
| deprecation | `make_deprecated_getattr` (PEP 562 deprecation primitive) |

Import from the package root. Always. That is the stable API:

```python
from xtm_oaev_sdk import Configuration, ContractBuilder, SignatureManager
```

## Quickstart

```python
from xtm_oaev_sdk import (
    Configuration,
    ContractBuilder,
    ContractCheckbox,
    ContractText,
    SignatureManager,
    build_network_configs,
)

# Hint-based configuration: override, then env var, then config file, then default
config = Configuration({"log_level": {"env": "LOG_LEVEL", "default": "info"}})
config.get("log_level")  # 'info'

# Contract fields, fluent builder
fields = (
    ContractBuilder()
    .mandatory(ContractText(key="target", label="Target"))
    .optional(ContractCheckbox(key="verbose", label="Verbose"))
    .build_fields()
)

# Signatures: the manager ships them through an injected transport
# (pyoaev's `OpenAEV().signature` is one)
manager = SignatureManager(transport=api.signature)
signatures = manager.build_execution_signatures(build_network_configs(["10.0.0.1"]))
```

## Architecture

Every capability is cut into three layers, the same way across all three SDKs:

```
public/<capability>.py   adapters: what users import; speak seam types, delegate to _core
seam/<capability>/       contracts: data models, enums, errors, Protocol ports (closed, versioned)
_core/<capability>/      implementations of the seam ports
```

`public` → `seam` ← `_core`. The seam imports neither of the other two, the core
never touches `public`, and `public` never hands a core object to users. Keep the
core answering the seam and the public API keeps working. Touch the seam and you
have changed a contract: `SEAM_VERSION` bump, changelog entry. The full wiring is in
[docs/seam_strategy.md](docs/seam_strategy.md).

## Migrating from pyoaev

Every former `pyoaev` path still works, and each one fires a `DeprecationWarning`
pointing at the new import. How that holds together:
[docs/shim_strategy.md](docs/shim_strategy.md).

```python
from pyoaev.configuration import Configuration  # DeprecationWarning, still works
from xtm_oaev_sdk import Configuration          # new home
```

## Development

```bash
pip install -e libs/xtm-oaev-sdk
python -m pytest libs/xtm-oaev-sdk/test
```

Python: 3.12 or later. The code uses `typing.override`, exactly as pyoaev already did.
Runtime dependencies: pydantic, pydantic-settings, PyYAML, python-json-logger.
