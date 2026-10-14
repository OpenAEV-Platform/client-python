# Shim strategy: splitting pyoaev without breaking anyone

`pyoaev` used to carry everything: the OpenAEV API client, and on top of it
configuration, contracts, signatures, the daemon runtime, errors, helpers. That
shared code now lives in three SDKs (`xtm-oaev-sdk`, `collectors-sdk`,
`injectors-sdk`), and `pyoaev` is back to its actual job: being the API client.

One rule governs the split: **no breaking change for existing code.** Every
collector and injector written against `pyoaev` keeps running untouched until the
shims are deliberately pulled. This document lays out how that holds, and why it is
built this way.

## The contract

For every name a released `pyoaev` exposed:

1. **The legacy path still resolves**: `from pyoaev.configuration import Configuration`,
   `pyoaev.helpers.OpenAEVInjectorHelper`, `from pyoaev import AssetCategory`…
2. **It resolves to the SDK object**, and to the *identical* object whenever possible,
   so `is`, `isinstance`, subclassing, pickling-by-reference and introspection behave
   exactly as before.
3. **Access fires a `DeprecationWarning`** naming the new import, pinned to the
   **consumer's line**, so the default warning filters actually show it.
4. **Importing `pyoaev` stays silent**: only touching a moved name warns.
5. **Patch targets keep landing**: what connectors' tests patch (`pyoaev.utils.PingAlive.start`,
   `pyoaev.daemons.collector_daemon.CollectorDaemon._setup`,
   `pyoaev.daemons.base_daemon.OpenAEV`, `pyoaev.signatures.signature_manager.socket.gethostbyname`…)
   still hits the code that actually runs.

## Dependency direction

```
xtm-oaev-sdk  ←  collectors-sdk
      ↑       ←  injectors-sdk
      └──────────────┴──────────  pyoaev (API client + shims)
```

- The SDKs **never** import `pyoaev`. When they need the platform, the API client
  gets injected (`xtm_oaev_sdk.BaseClient` protocol; `pyoaev.OpenAEV` satisfies it).
- `pyoaev` **hard-depends** on the three SDKs for the whole deprecation window. That
  is what keeps a connector that only lists `pyoaev` alive. An optional extra
  (`pyoaev[collectors]`) would have broken exactly those connectors.
- The direct dependencies `pyoaev` no longer imports (`pika`, `thefuzz`, `PyYAML`,
  `pydantic-settings`, `python-json-logger`) are gone from its `pyproject.toml`.
  They still arrive transitively through the SDKs, so a `pyoaev` install pulls the
  same third-party packages as before.

## The mechanism: PEP 562 module `__getattr__`

Every shim module serves its moved names lazily, through a module-level
`__getattr__` built by the SDK primitive `make_deprecated_getattr`:

```python
"""DEPRECATED: moved to :mod:`xtm_oaev_sdk`."""

import xtm_oaev_sdk as _sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

__all__ = [  # noqa: F822 (names are served by the PEP 562 __getattr__ below)
    "DictionarySource",
    "EnvironmentSource",
]

__getattr__ = _make_deprecated_getattr(
    {
        name: (f"Use 'from xtm_oaev_sdk import {name}' instead.", getattr(_sdk, name))
        for name in __all__
    },
    module_name=__name__,
)
```

`make_deprecated_getattr(mapping, module_name=...)` validates the
`{old_name: (message, replacement)}` mapping once, then hands back a `__getattr__`
that warns (`DeprecationWarning`, `stacklevel=2`) and returns the replacement **as
is**. Unknown names still raise `AttributeError`. Typos never get swallowed.

### Why not the alternatives

- **`typing_extensions.deprecated(...)(cls)`** does not wrap the
  class. It **patches the original class in place** (`__new__` /
  `__init_subclass__`). The moment anything imported `pyoaev`, users of
  `xtm_oaev_sdk.Configuration` *also* caught "use `xtm_oaev_sdk`" warnings. Rejected.
- **A wrapper class or proxy** breaks identity: `isinstance` against the SDK class,
  metaclasses and signature introspection all shift. Rejected.
- **A plain re-export** (`from xtm_oaev_sdk import X`) keeps identity but never
  warns, so nobody would ever migrate. Rejected.
- **Optional dependencies or lazy imports of the SDKs** would make legacy imports
  blow up for connectors that only list `pyoaev`. Rejected (see dependency direction).

## The kinds of shims

| Kind | Example | How it is served |
|---|---|---|
| **Moved, identical** (the vast majority) | `pyoaev.configuration.Configuration` → `xtm_oaev_sdk.Configuration` | the SDK object itself |
| **Renamed** | `pyoaev.signatures.ExpectationType` → `xtm_oaev_sdk.SignatureExpectationType`; `pyoaev.contracts.contract_config.ExpectationType` → `xtm_oaev_sdk.ContractExpectationType` | the SDK object; the message names the new name |
| **Client-building adapter** | `pyoaev.daemons.BaseDaemon`, `pyoaev.daemons.CollectorDaemon`, `pyoaev.signatures.SignatureManager`, `pyoaev.helpers.OpenAEVInjectorHelper` | a thin subclass of the SDK class (see below) |
| **Value without public replacement** | `pyoaev.contracts.variable_helper.USER`…, `pyoaev.helpers.TRUTHY` / `FALSY` | the literal value, with a message pointing at the right API |
| **Private legacy helper** | `pyoaev.helpers._is_base64_encoded` | the collectors-sdk implementation, "private and will be removed" |
| **Legacy-only glue** | `pyoaev.helpers.OpenAEVCollectorHelper` (already deprecated) | kept in `pyoaev` on top of the collectors-sdk daemon, warns on access |
| **Re-exported names** | `pyoaev.daemons.base_daemon.Configuration`, `pyoaev.apis.inject_expectation.model.expectation.SignatureTypes`… | the SDK object (names a module merely imported are part of its surface too) |

### Client-building adapters

The SDKs take the API client as an argument (`api_client=` / `transport=`). The
legacy constructors built `OpenAEV(...)` themselves. So those legacy names resolve to
a thin subclass of the SDK class whose only job is to restore that behaviour:

| Legacy name | Subclass of | What it adds |
|---|---|---|
| `pyoaev.daemons.BaseDaemon` | `xtm_oaev_sdk.BaseDaemon` | `_create_default_api_client()` builds `OpenAEV` from `openaev_url` / `openaev_token` / `openaev_tenant_id` |
| `pyoaev.daemons.CollectorDaemon` | `collectors_sdk.CollectorDaemon` + the class above | same hook; still an instance of the legacy `BaseDaemon` |
| `pyoaev.signatures.SignatureManager` | `xtm_oaev_sdk.SignatureManager` | `SignatureManager(client, logger)` uses `client.signature` as transport |
| `pyoaev.helpers.OpenAEVInjectorHelper` | `injectors_sdk.OpenAEVInjectorHelper` | `_create_default_api_client(config)` builds `OpenAEV` from the config helper |

`isinstance(legacy_object, <SDK class>)` holds. Each adapter is **one object**,
whatever path reaches it (`pyoaev.daemons.CollectorDaemon is
pyoaev.daemons.collector_daemon.CollectorDaemon is pyoaev.helpers.CollectorDaemon`),
so patching a method on any of those paths hits the class connectors instantiate.

## Rules learned the hard way

- **Assign `__getattr__` directly.** A `def __getattr__(name): return
  _deprecated_getattr(name)` wrapper slips in an extra frame. The warning then gets
  pinned to the shim file, and Python's default filters (which only show
  `DeprecationWarning` for `__main__`) hide it from scripts.
- **Never star-import a shim module.** `from pyoaev.signatures import *` walks
  `__all__`, trips every lazy name and makes `import pyoaev` warn. Instead, the
  `pyoaev` package root binds the shim submodules and serves their names through its
  own `__getattr__` (`pyoaev.__all__` is unchanged, so `from pyoaev import *` keeps
  exporting the same names, and warns for the moved ones).
- **pyoaev's own code imports from the SDKs**, never from its shims. Importing any
  `pyoaev` module, `pyoaev.apis` included, stays silent.
- **Keep patch surfaces.** `pyoaev.signatures.signature_manager` still imports
  `socket` and `subprocess` (tests patch `...signature_manager.socket.gethostbyname`,
  which reaches the shared stdlib module the SDK uses). The client-building adapters
  call `OpenAEV` through their module global, so `patch("pyoaev.daemons.base_daemon.OpenAEV")`
  and `patch("pyoaev.helpers.OpenAEV")` still bite.
- **`__all__` lists lazily served names**: flake8 flags F822 outside `__init__.py`,
  so the line carries `# noqa: F822` with the reason.
- **Known quirk**: `from <package> import X` on a shim *package* warns twice
  (importlib's `_handle_fromlist` probes with `hasattr` before the real lookup).
  Plain modules warn once. Harmless, and baked into PEP 562.

## Where the shims are

| pyoaev module | Serves |
|---|---|
| `pyoaev/__init__.py` | the moved names it exported (asset enums, exceptions, configuration, contracts, signatures) |
| `pyoaev/configuration/*` | xtm-oaev-sdk configuration |
| `pyoaev/contracts/*` | xtm-oaev-sdk contracts (`ExpectationType` renamed, variable constants) |
| `pyoaev/signatures/*` | xtm-oaev-sdk signatures (`ExpectationType` renamed, `SignatureManager` adapter) |
| `pyoaev/exceptions.py`, `asset_types.py`, `security_domain/types.py` | xtm-oaev-sdk common |
| `pyoaev/utils.py` | xtm-oaev-sdk common and `PingAlive`; keeps the HTTP helpers `get_content_type`, `response_content` |
| `pyoaev/daemons/*` | `BaseDaemon` / `CollectorDaemon` adapters |
| `pyoaev/helpers.py` | collectors-sdk detection, injectors-sdk helpers (`OpenAEVInjectorHelper` adapter), xtm SSL helpers, `OpenAEVCollectorHelper` |
| `pyoaev/apis/inject_expectation/model/*` | collectors-sdk expectations (the API manager builds them) |

## How it is tested

| Test | Guards |
|---|---|
| `libs/xtm-oaev-sdk/test/<capability>/shim/test_shim_contract.py` | identity, warning text, pinning to the consumer's line, silent imports, unknown names, adapters (client construction, `isinstance`) |
| `libs/xtm-oaev-sdk/test/<capability>/shim/test_*.py` | the original pyoaev tests, moved **verbatim**: they still drive the legacy paths |
| `test/test_sdk_split_shims.py` | the collectors-sdk / injectors-sdk shims, adapters and connector patch targets |
| `test/test_legacy_surface.py` | every public name of the **released** pyoaev, recorded in `test/fixtures/legacy_surface.json` by `test/generate_legacy_surface.py` from the release, not the working tree) still resolves |

Beyond the suites, the split went through the real collectors|injectors own test suites
run once against the released `pyoaev` and once
against the new stack. Identical results.

## Observable differences (not API breaks)

- Legacy imports warn (that is the whole point of the shims).
- The client-building adapters are subclasses, not the identical SDK classes.
- An `AppLogger` built without a name, and a `SignatureManager` built without a
  logger, log under the SDK module name instead of the former pyoaev one.

## Removing the shims

In a major release of `pyoaev`:

1. delete the shim modules and the `__getattr__` of `pyoaev/__init__.py`;
2. delete the client-building adapters and `OpenAEVCollectorHelper`;
3. drop the `xtm-oaev-sdk` / `collectors-sdk` / `injectors-sdk` dependencies only the
   shims need (keep `xtm-oaev-sdk` if the client still leans on its errors and
   transport models);
4. delete `test/test_legacy_surface.py` and the `shim/` test folders;
5. announce it: every removed name has been warning since the split, new import included.
