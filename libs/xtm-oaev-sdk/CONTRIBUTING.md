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
2. regenerate the seam golden in the same change, not in a follow-up (see
   [Seam golden](#seam-golden-testseam));
3. add an entry to [CHANGELOG.md](CHANGELOG.md);
4. if a public name changes or disappears, the old one keeps working through a
   deprecation shim (`make_deprecated_getattr`) first.

## Seam golden (`test/seam`)

The seam is the contract between the public API and the core, and part of it rides the
wire: payloads sent to the platform, data coming back, the connector manifest. Every
change to it must be deliberate. `libs/xtm-oaev-sdk/test/seam/` fingerprints every
public object of every seam module, so any change fails a test until someone signs off
on it
([every-seam-object-is-fingerprinted](docs/tdr/every-seam-object-is-fingerprinted.tdr.md)).

### What is in there

| File | Role |
|---|---|
| `generate_seam_golden.py` | Finds the seam on its own: every `*.py` file under `xtm_oaev_sdk/seam/`, every public top-level definition (class, function, constant, type alias). It fingerprints each one, then rewrites the golden: changed fingerprints updated, new objects added, deleted objects removed. It prints what moved, and warns when a capability changed but its version did not. |
| `fixtures/seam_golden.json` | The golden: one entry per object, `"<module>.<name>": {"kind", "sha256"}`. |
| `test_seam_golden.py` | Recomputes the fingerprints and fails on any object added, removed or changed. It also checks that the package root re-exports the seam's own objects. |
| `test_seam_closed.py` | Checks that `port_io` imports only the signatures seam, and that the signatures seam imports nothing from the SDK. |

No list to maintain. The next run picks up any new seam object.

collectors-sdk and injectors-sdk carry the same golden under their own `test/seam/`. There,
run the generator from `libs/<sdk>`: `python test/seam/generate_seam_golden.py`.

### What a fingerprint covers

The sha256 of the definition's normalized AST. Formatting, comments and docstrings do
not count. So it moves with fields, defaults, enum members, method signatures,
validators and constant values. Pydantic models add their validation and serialization
JSON schemas on top, model and field descriptions included. Those reach the wire, so
rewording a pydantic model's docstring is a change.

### Updating it on purpose

From the repository root:

1. make the seam change;
2. bump the capability's `SEAM_VERSION` (`PORT_IO_CONTRACT_VERSION` for `seam/port_io`);
3. regenerate the golden:

   ```bash
   python libs/xtm-oaev-sdk/test/seam/generate_seam_golden.py
   ```

4. run `python -m pytest libs/xtm-oaev-sdk/test/seam`;
5. commit the seam change, the version bump and the golden in one go, with a
   [CHANGELOG.md](CHANGELOG.md) entry.

### Seeing what changed

A failure names every object that moved, as `<module>.<name>`. `git diff` that
definition: the code diff is the change. A pydantic model can move with no code change
at all (a pydantic upgrade, a referenced type). Then compare its schema on both commits:

```bash
python -c "import json; from xtm_oaev_sdk.seam.port_io import ExecutionDetails as M; print(json.dumps(M.model_json_schema(), indent=2, sort_keys=True))"
```

NEVER regenerate the golden just to turn a red test green. NEVER edit a hash by hand. If
a fingerprint moved with no seam change, find out why before you decide whether the
contract really changed.

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
