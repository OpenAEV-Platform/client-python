# Technical Decision Records

The technical decision records of the SDK split. Each one is a rule that future work on
xtm-oaev-sdk, collectors-sdk, injectors-sdk and the `pyoaev` shims is expected to respect.

## Compatibility with pyoaev

| TDR | Status | Rule |
|---|---|---|
| [Legacy pyoaev code keeps working until a pyoaev major release](no-breaking-change-for-legacy-pyoaev-code.tdr.md) | draft | Every public name of the latest released pyoaev must keep resolving from its legacy path, with a DeprecationWarning naming its new import, until a pyoaev major release removes the shims. |
| [The SDKs never depend on pyoaev; the API client is injected](sdks-never-import-pyoaev.tdr.md) | draft | xtm-oaev-sdk, collectors-sdk and injectors-sdk must never import pyoaev; anything that talks to the platform receives its API client or transport as an argument typed by a seam protocol. |
| [pyoaev hard-depends on the SDKs that host its former code](pyoaev-hard-depends-on-the-sdks-during-deprecation.tdr.md) | draft | While pyoaev ships deprecation shims, it must declare a hard dependency on every SDK those shims serve, never an optional extra. |
| [Legacy names are served by a directly assigned PEP 562 __getattr__](legacy-names-served-by-pep562-module-getattr.tdr.md) | draft | A moved name must be served from its legacy module by a module-level __getattr__ built with make_deprecated_getattr and assigned directly, never wrapped in a def. |
| [Shims return the identical SDK object; adapters only where constructors differ](shims-return-the-identical-sdk-object.tdr.md) | draft | A shim must return the SDK object itself; a legacy name may resolve to a thin subclass only to restore legacy constructor behaviour, and that subclass must be one single object whatever legacy path reaches it. |
| [Importing pyoaev never warns; only touching a moved name does](importing-pyoaev-stays-silent.tdr.md) | draft | Importing any pyoaev module must not emit a DeprecationWarning; only accessing a moved name may warn. |
| [Legacy patch targets are part of the compatibility surface](legacy-patch-targets-are-part-of-the-surface.tdr.md) | draft | Module attributes that connectors patch must stay reachable at their legacy path and still reach the code that actually runs. |
| [The legacy surface is guarded against the released pyoaev](legacy-surface-guarded-from-the-release.tdr.md) | draft | The legacy-surface guard must be generated from the released pyoaev package, and the pre-split tests of moved code must be kept verbatim against their legacy paths. |

## Layering

| TDR | Status | Rule |
|---|---|---|
| [public and _core depend on the seam; the seam depends on neither](public-seam-core-dependency-rule.tdr.md) | draft | Within each SDK capability, the seam imports neither public nor _core, _core never imports public, and public imports _core only to wire the default implementation of each port. |
| [Every piece of behaviour goes behind a port, even a one-liner](every-behaviour-behind-a-port.tdr.md) | draft | Every piece of behaviour exposed by an SDK goes through a seam Protocol port, one _core implementation and a public adapter, whatever its size. |
| [The seam holds data contracts and only their intrinsic invariants](seam-holds-data-contracts-and-their-own-invariants.tdr.md) | draft | A seam may contain data contracts and logic that only reads or derives from their own data; anything doing I/O, orchestrating, or needing another capability goes behind a port. |
| [Data-and-behaviour classes split: the public class extends the seam data](public-class-extends-seam-data.tdr.md) | draft | When a user-facing class mixes data and behaviour, the seam holds the data class and the public class extends it, adding behaviour through ports; the core only knows the seam type. |
| [Public adapters keep the shape of the code they replace](adapters-keep-the-user-facing-shape.tdr.md) | draft | A public adapter must keep the signatures, docstrings, attributes, overridable hooks and framework base class of the code it replaces; only the logic moves to the core. |
| [Adapters pass their own methods to the core to keep dispatch and patch points](pass-bound-callables-to-keep-dispatch.tdr.md) | draft | When the original code dispatched through its own object, the adapter must pass the bound method or a callable to the core instead of letting the core reimplement the call. |

## Contracts and versioning

| TDR | Status | Rule |
|---|---|---|
| [A seam change is a versioned contract change](seam-changes-are-versioned-contract-changes.tdr.md) | draft | Any change to a seam contract (field, type, enum member, error, port signature) must bump that seam's version and be recorded in the changelog, and a change reaching the public surface must go through a deprecation shim first. |
| [Seams crossing a process boundary pin their JSON schemas](cross-process-seams-pin-their-json-schemas.tdr.md) | draft | A seam whose models cross a process boundary must pin their JSON schemas with golden hashes, regenerated only together with a version bump. |

## Public API, tests and checks

| TDR | Status | Rule |
|---|---|---|
| [Consumers import from the package root only](import-from-the-package-root.tdr.md) | draft | Consumers must import SDK names from the package root (xtm_oaev_sdk, collectors_sdk, injectors_sdk); public, seam and _core module paths are internal and may move. |
| [Colliding moved names are renamed with their capability prefix](colliding-names-get-a-capability-prefix.tdr.md) | draft | A moved name that collides with another capability's name in the flat root namespace must be renamed with its capability as prefix, and its legacy shim must name the new name. |
| [xtm-oaev-sdk stays agnostic of collectors, injectors and transports](xtm-oaev-sdk-stays-connector-agnostic.tdr.md) | draft | xtm-oaev-sdk must not contain collector- or injector-specific runtime, nor import pika, thefuzz or requests; those belong to collectors-sdk, injectors-sdk or pyoaev. |
| [Every SDK module imports on its own in a fresh interpreter](every-sdk-module-imports-alone.tdr.md) | draft | Every SDK module must import successfully as the first import of a fresh interpreter running with -W error. |

## Adding a TDR

Create `<slug>.tdr.md`, the slug naming the rule. Same header as the other records,
`status: draft`, then a row in this table. A TDR moves to `accepted` once validated. The
day it stops governing, it goes `superseded` (with `superseded_by` / `supersedes` set on
both records) or `revoked`.
