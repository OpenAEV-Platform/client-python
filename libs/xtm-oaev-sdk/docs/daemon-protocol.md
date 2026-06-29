# DaemonProtocol

Behavioral contract for daemon implementations shared by collector and injector runtimes.

## Purpose

Both collector and injector extensions need a daemon runtime that provides:
- A `start()` method to boot the daemon (setup + main loop)
- A `set_callback()` method to configure the periodic work function
- A `get_id()` method to retrieve the daemon instance identifier

`DaemonProtocol` captures this shared surface as a `@runtime_checkable` Protocol. Extension SDKs type-hint against it instead of importing the concrete `BaseDaemon` from pyoaev.

## API

```python
from xtm_oaev_sdk import DaemonProtocol

@runtime_checkable
class DaemonProtocol(Protocol):
    def start(self) -> None: ...
    def set_callback(self, callback: Callable[..., Any]) -> None: ...
    def get_id(self) -> str | None: ...
```

### Methods

| Method | Purpose |
|---|---|
| `start()` | Run one-time setup then enter the main execution loop |
| `set_callback(callback)` | Configure the function called periodically by the daemon |
| `get_id()` | Return the daemon instance identifier (collector_id, injector_id, etc.) |

## Structural Satisfaction

pyoaev's `BaseDaemon` satisfies this Protocol structurally with zero changes:

```python
from pyoaev.daemons import BaseDaemon
from xtm_oaev_sdk import DaemonProtocol

# BaseDaemon implements start(), set_callback(), get_id()
assert isinstance(my_daemon, DaemonProtocol)  # True
```

No inheritance is required. Any class implementing the three methods passes the `isinstance` check at runtime.

## Usage in Extension SDKs

Extension SDKs can type-hint against `DaemonProtocol` without importing pyoaev:

```python
from xtm_oaev_sdk import DaemonProtocol

class BaseCollector:
    def __init__(self, daemon: DaemonProtocol, ...):
        self._daemon = daemon
```

This decouples extension SDKs from the concrete daemon implementation, enabling:
- Testing with mock daemons (no OpenAEV API client needed)
- Future daemon rewrites without breaking extension code
- Clear behavioral contract visible in type signatures

## What is NOT in the Protocol

Implementation details stay in the concrete daemon:

| Excluded | Why |
|---|---|
| `_setup()` | Abstract in BaseDaemon, implementation-specific |
| `_start_loop()` | Abstract in BaseDaemon, implementation-specific |
| `_try_callback()` | Error-handling strategy, not behavioral contract |
| Constructor parameters | Configuration, API client wiring is runtime-specific |
| `PingAlive` thread | Heartbeat mechanism belongs to the concrete daemon |

## Scope Boundary

| Concern | Owner |
|---|---|
| DaemonProtocol (behavioral contract) | `xtm-oaev-sdk` |
| BaseDaemon (concrete ABC) | `pyoaev` |
| CollectorDaemon | `pyoaev` |
| Daemon type-hints in extension SDKs | `injectors-sdk` / `collectors-sdk` (future) |
