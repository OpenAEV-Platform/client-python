# Contributing to xtm-oaev-sdk

This guide is about what's specific to the SDKs. Everything repository-wide
(Conventional Commits titles with an issue reference, signed commits, labels, coverage)
lives in the repository's [CONTRIBUTING.md](../../CONTRIBUTING.md). `collectors-sdk`
and `injectors-sdk` run on this guide too, plus a short one of their own.

## Set up

From the repository root, on Python 3.12 or later, since the code uses `typing.override`:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ./libs/xtm-oaev-sdk -r libs/sdk-requirements.txt -e '.[dev]'
```

`libs/sdk-requirements.txt` pulls `collectors-sdk` and `injectors-sdk` from git,
because `pyoaev` depends on them.

## Run the checks

```bash
isort --check-only .
black --check .
flake8 --ignore=E,W --extend-exclude=.venv .
python -m pytest                          # pyoaev and xtm-oaev-sdk
python -m pytest libs/xtm-oaev-sdk/test   # the SDK alone
```

CI runs the exact same four tools. Locally, `pre-commit run --files <files>` takes
care of isort, black and the file hygiene hooks.

## Where code goes

Every capability is cut in three: `public/` (adapters), `seam/` (contracts), `_core/`
(implementations). [docs/seam_strategy.md](docs/seam_strategy.md) lays out the layering
and the patterns that hold it together. The rules, each one nailed down as a TDR in
[docs/tdr](docs/tdr/TDR_ToC.md):

- the seam imports neither `public` nor `_core`, `_core` never imports `public`, and
  `public` touches `_core` only to wire default implementations
  ([public-seam-core-dependency-rule](docs/tdr/public-seam-core-dependency-rule.tdr.md));
- every piece of behaviour goes behind a port, one-liners included
  ([every-behaviour-behind-a-port](docs/tdr/every-behaviour-behind-a-port.tdr.md));
- adapters keep the signatures, attributes, hooks and base classes of what they replace
  ([adapters-keep-the-user-facing-shape](docs/tdr/adapters-keep-the-user-facing-shape.tdr.md));
- users import from the package root, nowhere else
  ([import-from-the-package-root](docs/tdr/import-from-the-package-root.tdr.md));
- the SDK never imports `pyoaev`, `pika`, `thefuzz` or `requests`
  ([sdks-never-import-pyoaev](docs/tdr/sdks-never-import-pyoaev.tdr.md),
  [xtm-oaev-sdk-stays-connector-agnostic](docs/tdr/xtm-oaev-sdk-stays-connector-agnostic.tdr.md)).

`test/test_boundaries.py` catches the forbidden imports.

Adding a capability? The checklist sits at the end of
[docs/seam_strategy.md](docs/seam_strategy.md). Follow it.

## Changing a seam

A seam change is a contract change. Treat it like one
([seam-changes-are-versioned-contract-changes](docs/tdr/seam-changes-are-versioned-contract-changes.tdr.md)):

1. bump the capability's `SEAM_VERSION` (`PORT_IO_CONTRACT_VERSION` for `seam/port_io`);
2. for `seam/signatures/seam.py` or `seam/port_io`, update the pinned schemas in the same
   change, not in a follow-up (see [Pinned seam schemas](#pinned-seam-schemas-testseam));
3. add an entry to [CHANGELOG.md](CHANGELOG.md);
4. if a public name changes or disappears, the old one keeps working through a
   deprecation shim (`make_deprecated_getattr`) first.

## Pinned seam schemas (`test/seam`)

Some seams carry models that leave the process: the inbound signature I/O in
`seam/signatures/seam.py` (injector configs, execution signatures, tool output) and the
wire payloads in `seam/port_io`. Another process reads them. Change their schema and the
other side breaks while every local test stays happily green. `libs/xtm-oaev-sdk/test/seam/`
pins those schemas: touch one and a test goes red, forcing a deliberate decision
([cross-process-seams-pin-their-json-schemas](docs/tdr/cross-process-seams-pin-their-json-schemas.tdr.md)).

### What is in there

| File | Role |
|---|---|
| `fixtures/signatures_seam_schemas.json`, `fixtures/port_io_schemas.json` | The golden files: one SHA-256 per model, computed from its `model_json_schema()` serialized with sorted keys. Hashes only. The schemas themselves are not in there. |
| `test_signatures_seam_schema_pin.py`, `test_port_io_schema_pin.py` | Recompute every hash and hold it against the golden file. On top of that, they assert the seam version, make sure the seam module imports nothing from the SDK internals, and (signatures) that the package root re-exports the very same objects. |
| `generate_signatures_seam_golden.py`, `generate_port_io_golden.py` | Overwrite the golden file with the hashes of the current models. No check. No confirmation. |

The other seams carry a `SEAM_VERSION` and no pinned schema. Their models never leave
the process, so there is no other side to break.

### When it fails

The moment `model_json_schema()` changes for a pinned model, for any reason:

- a field is added, removed, renamed or retyped, or its default changes;
- a `Field` description changes, or the docstring of a model or enum. Yes, the
  docstring: it becomes the schema `description`;
- a pydantic upgrade renders the schema differently, even though no model changed.

### Updating it on purpose

From the repository root:

1. make the model change;
2. bump the version: `SEAM_VERSION` in `seam/signatures/seam.py` or
   `PORT_IO_CONTRACT_VERSION` in `seam/port_io/models.py`, plus the expected value in
   `test_seam_version_is_pinned` or `test_port_io_contract_version_is_pinned`;
3. regenerate the golden file:

   ```bash
   python libs/xtm-oaev-sdk/test/seam/generate_signatures_seam_golden.py
   python libs/xtm-oaev-sdk/test/seam/generate_port_io_golden.py
   ```

4. run `python -m pytest libs/xtm-oaev-sdk/test/seam`;
5. commit the model, the version, the test and the golden file together, with a
   [CHANGELOG.md](CHANGELOG.md) entry.

Pinning a new model? Add it to the model dictionary of the test *and* of its generator.
Each keeps its own copy, and forgetting one is the trap.

### Seeing what changed

The golden files only hold hashes, so a failure tells you *that* a schema moved, never
*how*. To see it, dump the schema on your branch and on the base commit (a
`git worktree` does the job), then diff the two:

```bash
python -c "import json; from xtm_oaev_sdk.seam.port_io import ExecutionDetails as M; print(json.dumps(M.model_json_schema(), indent=2, sort_keys=True))"
```

NEVER regenerate a golden file just to turn a red test green, and NEVER edit a hash by
hand. That silences the one alarm this directory exists for. If a hash moved without any
model change (a pydantic upgrade, say), compare the dumped schemas and ask before deciding
whether the wire contract really changed.

## Moving code out of pyoaev

Legacy code keeps working. Non-negotiable
([no-breaking-change-for-legacy-pyoaev-code](docs/tdr/no-breaking-change-for-legacy-pyoaev-code.tdr.md)):

- serve the old path with a shim, by the rules of [docs/shim_strategy.md](docs/shim_strategy.md);
- move the old tests verbatim into `libs/xtm-oaev-sdk/test/<capability>/shim/`;
- `test/test_legacy_surface.py` stays green. Never regenerate its fixture from the
  working tree: it records the released `pyoaev`, and that is the whole point.

## Tests

Tests live in `libs/xtm-oaev-sdk/test/<capability>/` and go through the public API to
hit behaviour. Write them as `_given_` / `_when_` / `_then_` helpers, topped with a
one-line "It ..." docstring:

```python
def test_configuration_resolves_with_override_priority(tmp_path, monkeypatch) -> None:
    """It prioritizes override over env, file, and default."""
    module = _given_public_module()
    ...
    _when_set_configuration_value(configuration, "target", "override-value")
```

## Commits

Repository conventions first. On top of them, the SDK history prefixes a gitmoji and
uses the `sdk` scope, one capability or concern per commit:

```
:recycle: refactor(sdk): enhancing port-adapter public boundaries for configuration
```

## Documentation

- [README.md](README.md): the intent, and a quickstart;
- [docs/shim_strategy.md](docs/shim_strategy.md) and
  [docs/seam_strategy.md](docs/seam_strategy.md): the how and the why;
- [docs/migration_guide.md](docs/migration_guide.md): getting connectors onto the SDKs;
- [docs/tdr](docs/tdr/TDR_ToC.md): the technical decision records. A new decision gets
  its own `<slug>.tdr.md`, same header as the others, `draft` status, and a line in
  `TDR_ToC.md`.
