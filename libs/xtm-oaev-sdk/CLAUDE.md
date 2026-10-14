# xtm-oaev-sdk: agent instructions

Applies to work under `libs/xtm-oaev-sdk/`, and to the `pyoaev/` deprecation shims when
code moves out of `pyoaev`. Paths below are relative to the repository root.

xtm-oaev-sdk is the shared, client-free runtime of the OpenAEV connectors
(configuration, contracts, signatures, daemons, errors). `pyoaev` is the HTTP client
and serves the former names through deprecation shims. collectors-sdk and injectors-sdk
build on this SDK from their own repositories.

## Hard rules

1. NEVER break legacy `pyoaev` code. Every public name of the latest released `pyoaev`
   (recorded in `test/fixtures/legacy_surface.json`) MUST keep resolving from its legacy path, returning the SDK object and emitting a
   `DeprecationWarning` that names the new import. Why: connectors pin `pyoaev`, import
   its old paths and patch them in their tests.
2. Respect the layering of every capability:
   - `seam/<capability>/` imports neither `public/` nor `_core/`;
   - `_core/<capability>/` NEVER imports `public/` (type-only imports go under `TYPE_CHECKING`);
   - `public/<capability>.py` imports `_core/` ONLY to assign module-level defaults typed by
     their port (`_resolver: ConfigurationResolverPort = ConfigurationResolver(...)`);
   - every exported name is an adapter defined in `public/` or a contract defined in
     `seam/`, NEVER a `_core` object.

   Why: the core can then be rewritten freely while the public API keeps working.
3. Every piece of behaviour goes through a seam `Protocol` port, one `_core`
   implementation and a `public` adapter, one-liners included. No exceptions.
4. A public adapter MUST keep the signatures, docstrings, attributes, overridable hooks
   and framework base class of the code it replaces. When the old code called a method on
   `self`, pass that bound method to the core as a callable, so overrides and test
   patches keep applying.
5. NEVER import `pyoaev`, `pika`, `thefuzz` or `requests` in the SDK. The API client is
   injected (`BaseClient`, `SignatureTransportProtocol`).
6. Users import from the package root (`from xtm_oaev_sdk import X`). A new public name
   goes in its `public/<capability>.py` `__all__` and in `public/__init__.py`.
7. A seam change (field, type, enum member, error, port signature) is a contract change:
   bump that capability's `SEAM_VERSION` (`PORT_IO_CONTRACT_VERSION` for `seam/port_io`)
   and add an entry to `libs/xtm-oaev-sdk/CHANGELOG.md`. For `seam/signatures/seam.py` or
   `seam/port_io`, also update the expected version in the matching
   `test/seam/test_*_schema_pin.py` and regenerate the pinned schemas in the same change:
   `python libs/xtm-oaev-sdk/test/seam/generate_signatures_seam_golden.py` and
   `python libs/xtm-oaev-sdk/test/seam/generate_port_io_golden.py`. NEVER regenerate them
   to make a failing pin pass without a deliberate seam change; follow
   `libs/xtm-oaev-sdk/CONTRIBUTING.md`, "Pinned seam schemas".
8. NEVER regenerate `test/fixtures/legacy_surface.json` from the working tree: it records
   the released `pyoaev`. NEVER rewrite the legacy tests moved under
   `libs/xtm-oaev-sdk/test/<capability>/shim/`.

## Scope

Only make the changes directly requested. Do not add capabilities, abstractions, files,
dependencies or refactors beyond the task.

## Stop and ask before

- changing a seam contract or a `SEAM_VERSION`;
- renaming or removing a public name, or removing a `pyoaev` shim;
- adding or changing a dependency in any `pyproject.toml` or in `libs/sdk-requirements.txt`;
- editing `test/fixtures/legacy_surface.json`, the golden schema fixtures under
  `libs/xtm-oaev-sdk/test/seam/fixtures/`, or CI configuration;
- deleting any file.

## Done when

Run from the repository root, and report the real output:

```bash
isort --check-only . && black --check . && flake8 --ignore=E,W --extend-exclude=.venv .
python -m pytest libs/xtm-oaev-sdk/test test/test_legacy_surface.py test/test_sdk_split_shims.py
python -m pytest
```

All three pass. If a check fails, say which one and why. NEVER report a check as passing
without running it.

## Conventions

- Tests live in `libs/xtm-oaev-sdk/test/<capability>/`, exercise behaviour through the
  public API, and are written as `_given_*` / `_when_*` / `_then_*` helpers with a
  one-line `"""It ..."""` docstring. Copy the style of the neighbouring tests.
- Adding a capability: follow the checklist at the end of `libs/xtm-oaev-sdk/docs/seam_strategy.md`.
- Recording a decision: add `libs/xtm-oaev-sdk/docs/tdr/<slug>.tdr.md` with the header of
  an existing record and `status: draft`, plus a row in `docs/tdr/TDR_ToC.md`.
- Commit messages, when asked for: gitmoji + Conventional Commits with the `sdk` scope,
  e.g. `:recycle: refactor(sdk): enhancing port-adapter public boundaries for configuration`.

## Read when relevant

- `libs/xtm-oaev-sdk/docs/seam_strategy.md`: layering patterns and capability map.
- `libs/xtm-oaev-sdk/docs/shim_strategy.md`: moving code out of `pyoaev` without breaking it.
- `libs/xtm-oaev-sdk/docs/tdr/TDR_ToC.md`: the decision behind each rule above.
- `libs/xtm-oaev-sdk/CONTRIBUTING.md`: setup and repository conventions.
