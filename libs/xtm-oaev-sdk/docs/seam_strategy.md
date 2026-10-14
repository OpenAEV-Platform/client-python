# Seam strategy: port/adapter layering of the SDKs

`xtm-oaev-sdk`, `collectors-sdk` and `injectors-sdk` share one build. Every
capability is cut into a **public** adapter layer, a **seam** of contracts, and a
**core** implementation. This document covers the intent, the rules, the patterns
that applied them without touching behaviour, and how to add a capability.

## Intent

| Layer | Role |
|---|---|
| `public/<capability>.py` | What users import: ready-to-use adapters (classes, functions) plus the seam contracts users need. Adapters speak seam types and hand the work to the core. |
| `seam/<capability>/` | The **contract** between public and core: data models, enums, errors, value objects, and `Protocol` ports, plus `SEAM_VERSION`. |
| `_core/<capability>/` | The code behind the public API: one implementation per seam port. |

As long as the core keeps answering the seam, the public layer keeps working, and
so does every consumer downstream of it. The core can be rewritten at will. A change
*to the seam* is another matter: that is a contract change. It bumps `SEAM_VERSION`,
earns a changelog entry, and needs a deprecation once it reaches the public surface.

## Rules

```
public  ──►  seam  ◄──  _core
   └───────────────────────► (wiring only: default implementations)
```

1. **The seam is closed.** It imports only the standard library, third-party
   libraries (pydantic…), other packages' *public* API (e.g. `collectors_sdk` seams
   import `xtm_oaev_sdk`) and sibling seam modules. Never `_core`. Never `public`.
2. **The core implements the seam.** It imports seams, other core modules and
   third-party libraries. Never `public`, not even lazily; type-only imports go under
   `TYPE_CHECKING`.
3. **Public never hands out a core object.** Every exported name is either an adapter
   defined in `public/` or a contract defined in `seam/`. Public touches `_core` for
   one reason only, picking the default implementation of each port:

   ```python
   _truthiness: TruthinessPort = Truthiness()
   _sources: ConfigurationSourcesPort = ConfigurationSources()
   _resolver: ConfigurationResolverPort = ConfigurationResolver(_sources, _truthiness)
   ```

4. **Users import from the package root** (`from xtm_oaev_sdk import X`). The layers
   are internal wiring.

## What goes where

### In the seam: data contracts

Pydantic models, dataclasses, enums, exceptions, type aliases and constants. In
short, whatever crosses the boundary. They may carry **their own invariants**, logic
that only reads or derives from their own data, because that logic is part of what
the data *is*:

- validators and derived fields (`ConfigurationHint`, `ExpectationData`'s null
  signatures coerced to `[]`);
- `__post_init__` invariants of the contract elements (derived `type`, forced
  cardinality, predefined expectations);
- value objects: `EncodedId` (URL encoding), `RequiredOptional.validate_attrs`,
  `SignatureMatch` (score invariant), `SignatureType.make_struct_for_matching`;
- exceptions, including `OpenAEVError`'s extraction of a readable message from its
  own response body: the core raises them and users catch them, so they have to live
  where both sides can reach them.

Anything that does I/O, orchestrates, or leans on another capability is
**behaviour**, and it goes behind a port.

### Behind a port: everything else, however small

Every piece of behaviour gets a `Protocol` port in the seam, an implementation in
the core and an adapter in public, **even a one-liner**. `is_truthy` gets its
`TruthinessPort`, `Truthiness` and public `is_truthy`, same treatment as
`SignatureManager`. Uniformity is the whole point: no "too small to need a seam"
exception left to argue about.

A seam holds two kinds of protocols:

- **Consumer protocols**: what users type against or implement: `BaseClient`,
  `DaemonProtocol`, `AppLoggerProtocol`, `ConfigurationProtocol`,
  `ContractBuilderProtocol`, `SignatureManagerProtocol`, and the driven port
  `SignatureTransportProtocol` (implemented by `pyoaev`'s signature API).
- **Internal ports**: what a public adapter needs from the core:
  `ConfigurationResolverPort`, `SignatureEnginePort`, `CollectorRegistrationPort`…

## Patterns used to adapt without changing behaviour

The layering went onto existing code with behaviour held identical: public surface,
wire payloads and connector test suites, compared before and after. Pulling that off
took a handful of recurring patterns.

### Data + behaviour classes: split, the public class extends the seam data

When a user-facing class mixes data and behaviour (`Contract`, `Expectation`), the
seam keeps the data (`ContractData`, `ExpectationData`) and the public class extends
it, bolting the behaviour on through ports. Users keep constructing the public class;
the core only ever sees the seam type.

```python
@dataclass
class Contract(ContractData):
    variables: list[ContractVariable] = field(
        default_factory=lambda: _variables.default_variables()
    )

    def to_contract_add_input(self, source_id: str) -> dict[str, Any]:
        return _serializer.to_add_input(self, source_id)
```

### Framework subclasses stay framework subclasses

Adapters that users hand to a framework keep their base class, override only the
hook, and delegate the logic: `EnhancedJSONEncoder` (`json.JSONEncoder.default`),
`CustomJsonFormatter` (pythonjsonlogger `add_fields`), `ConnectorConfigSchemaGenerator`
(pydantic `GenerateJsonSchema`), `SettingsLoader` (pydantic-settings
`settings_customise_sources`), `PingAlive` / `ListenQueue` (`threading.Thread`).

### Stateful adapters keep their attributes and hooks

`BaseDaemon`, `CollectorDaemon`, `SignatureManager`, `AppLogger`,
`OpenAEVInjectorHelper` keep their attributes (`_configuration`, `api`, `logger`,
`local_logger`, IP caches…) and their overridable hooks (`_setup`, `_start_loop`,
`_try_callback`, `_create_default_api_client`, `_utcnow`…). Subclasses and tests
lean on them. The adapter holds the state; the core holds the logic.

### Pass callables to keep dispatch and patch points

Where the original code called back into its own object, the adapter passes that
callback down to the core, so overrides and patches still land:

```python
def _source_context(self, config):
    return _engine.source_context(
        config, self.resolve_container_ip, lambda: self._cached_ipv6
    )
```

`SignatureManager.post_execution_updates` passes `self._utcnow` (read only after the
tool output validates, as before); `Expectation.match_alert` passes
`self.match_fuzzy` / `self.match_simple`; `OpenAEVDetectionHelper` passes
`self.match_alert_element_fuzzy` / `self._decode_value`; `CollectorDaemon` passes
`self._try_callback` to the scheduler. A dependency the core cannot import travels
the same way: `Configuration.schema()` hands the public
`ConnectorConfigSchemaGenerator` to the core resolver.

### A state protocol when the core drives a stateful loop

`ListenQueue`'s RabbitMQ loop rewrites public attributes (`pika_connection`,
`channel`, `thread`…). The seam declares a `QueueListenerProtocol` describing that
state; the core runs the loop (connect, consume, recover, process, stop) against it,
and the adapter's methods shrink to one-line delegations:

```python
def run(self) -> None:
    _consumer.run(self)
```

## Versioning

- Every capability seam exposes `SEAM_VERSION`. `port_io`, a pure
  wire schema, carries `PORT_IO_CONTRACT_VERSION` instead.
- The seams that cross a process boundary pin their JSON schemas with golden hashes:
  `seam/signatures/seam.py` (inbound I/O: injector configs, execution
  signatures, tool output) and `seam/port_io` (`PORT_IO_CONTRACT_VERSION`: the wire
  payloads sent to the platform). See `test/seam/`.
- Policy: a change to a seam (field, type, enum member, error, port signature) bumps
  its version and lands in the changelog. If it reaches the public surface, the old
  name goes through a deprecation shim first (see [shim_strategy.md](shim_strategy.md)).

## Walkthrough: the configuration capability

```python
# seam/configuration/ports.py — the contract (closed)
@runtime_checkable
class TruthinessPort(Protocol):
    def is_truthy(self, value: str) -> bool: ...
    def is_falsy(self, value: str) -> bool: ...

# _core/configuration/truthiness.py — the implementation (imports the seam only)
class Truthiness:
    def is_truthy(self, value: str) -> bool:
        return value.lower() in ["yes", "true"]

# public/configuration.py — the adapter (what users import)
_truthiness: TruthinessPort = Truthiness()

def is_truthy(value: str) -> bool:
    return _truthiness.is_truthy(value)
```

The same capability carries the heavier cases too. `Configuration` keeps its
constructor, `get`, `set` and `schema`, and delegates resolution to
`ConfigurationResolverPort`. `SettingsLoader` stays a `BaseSettings` and delegates
source selection to `SettingsSourcesPort`. The settings models (`BaseConfigModel`,
`ConfigLoaderOAEV`…) are data contracts in the seam.

## Capability map

### xtm-oaev-sdk

| Capability | Seam: contracts | Seam: ports | Core | Public adapters |
|---|---|---|---|---|
| common | the error hierarchy, the asset and security-domain enums, `EncodedId`, `RequiredOptional`, `BaseClient`, `DaemonProtocol`, `AppLoggerProtocol` | `HttpErrorPort`, `JsonEncodingPort`, `LoggingPort`, `DictToolsPort`, `CertificatesPort` | `HttpErrorTranslator`, `JsonEncoding`, `LoggingSetup`, `DictTools`, `Certificates` | `on_http_error`, `AppLogger`, `logger`, `setup_logging_config`, `CustomJsonFormatter`, `EnhancedJSONEncoder`, `copy_dict`, `remove_none_from_dict`, the SSL helpers |
| configuration | `ConfigurationHint`, settings models, serializer types, `CONFIGURATION_TYPES`, `ConfigurationProtocol` | `ConfigurationResolverPort`, `ConfigurationSourcesPort`, `ConnectorSchemaPort`, `SettingsSourcesPort`, `TruthinessPort` | `ConfigurationResolver`, `ConfigurationSources`, `ConnectorSchemaTransformer`, `SettingsSourceSelector`, `Truthiness` | `Configuration`, `EnvironmentSource`, `DictionarySource`, `ConnectorConfigSchemaGenerator`, `SettingsLoader`, `is_truthy`, `is_falsy` |
| contracts | `ContractData`, contract elements and enums, `ContractVariable`, `Expectation`, `ContractBuilderProtocol` | `ContractAssemblyPort`, `ContractVariablesPort`, `ContractSerializerPort` | `ContractAssembly`, `BuiltinContractVariables`, `ContractSerializer` | `Contract`, `ContractBuilder`, `VariableHelper`, `prepare_contracts` |
| signatures | inbound I/O models, matching types and policies, `ExtraSignatureData`, `SignatureTransportProtocol`, `SignatureManagerProtocol` | `SignatureEnginePort`, `ContainerAddressPort`, `NetworkTargetsPort`, `MarkerPort` | `SignatureEngine`, `ContainerAddressResolver`, `NetworkTargets`, `MarkerBuilder` | `SignatureManager`, `build_network_configs`, `build_marker` |
| port_io | wire models and enums, `PORT_IO_CONTRACT_VERSION` | (none: pure wire schema) | | re-exported as is |
| daemons | (consumer protocols live in common) | `DaemonRuntimePort`, `HeartbeatPort` | `DaemonRuntime`, `Heartbeat` | `BaseDaemon`, `PingAlive` |
| deprecation | `DeprecatedNames` | `DeprecationPort` | `DeprecationShims` | `make_deprecated_getattr` |

### collectors-sdk

| Capability | Seam: contracts | Seam: ports | Core | Public adapters |
|---|---|---|---|---|
| daemons | `DEFAULT_PERIOD_SECONDS`, `DEFAULT_PLATFORM_TAG_COLOR` | `CollectorRegistrationPort`, `CollectorSchedulePort` | `CollectorRegistration`, `CollectorSchedule` | `CollectorDaemon` |
| detection | | `AlertMatchingPort` | `AlertMatcher` | `OpenAEVDetectionHelper` |
| expectations | `ExpectationData`, `ExpectationSignature`, `ExpectationTypeEnum` | `ExpectationMatchingPort`, `ExpectationUpdatePort` | `ExpectationMatcher`, `ExpectationUpdates` | `Expectation`, `DetectionExpectation`, `PreventionExpectation` |

### injectors-sdk

| Capability | Seam: contracts | Seam: ports | Core | Public adapters |
|---|---|---|---|---|
| helpers | `QueueListenerProtocol` (listener state) | `ConfigLookupPort`, `InjectorRegistrationPort`, `QueueConsumerPort`, `MqSslPort` | `ConfigLookup`, `InjectorRegistration`, `QueueConsumer`, `MqSsl` | `OpenAEVConfigHelper`, `OpenAEVInjectorHelper`, `ListenQueue`, `create_mq_ssl_context` |

## Adding a capability

1. **Seam** (`seam/<capability>/`): the data contracts in `models.py`, one `Protocol`
   per piece of behaviour the public API needs in `ports.py`, `SEAM_VERSION = "1.0.0"`
   in `__init__.py`. Import nothing from `_core` or `public`.
2. **Core** (`_core/<capability>/`): one class per port, implementing it with the
   exact method signatures. Import the seam, never `public`.
3. **Public** (`public/<capability>.py`): module-level default implementations typed
   by their port, adapters carrying the user-facing signatures and delegating to them,
   and the seam contracts users need. Set `__all__`.
4. **Root**: import the module in `public/__init__.py` and extend `__all__`.
5. **Tests**: behaviour through the public API; core implementations through their
   port when useful.
6. If the capability replaces a `pyoaev` name, add its deprecation shim in `pyoaev`
   (see [shim_strategy.md](shim_strategy.md)).
