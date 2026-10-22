# Legacy pyoaev code keeps working until a pyoaev major release
---
scope: [pyoaev, xtm-oaev-sdk, collectors-sdk, injectors-sdk, compatibility]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

pyoaev used to hold everything, and its shared code moved into the SDKs. Old code that
imports from pyoaev must keep working, with nothing more than a warning telling where
each thing went. That holds until a future major pyoaev release removes the old paths.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> `pyoaev` was a monolith: the OpenAEV API client, with configuration, contracts,
> signatures, the daemon runtime, errors and helpers piled on top. That shared code now
> lives in `xtm-oaev-sdk`, `collectors-sdk` and `injectors-sdk`.
>
> The collectors and injectors in the connector repositories import the former `pyoaev`
> paths, and their test suites patch them. The split had to land without dragging every
> connector into a migration on the same day: "no breaking change for old code".

---

## **The TDR**
| **Every public name of the latest released pyoaev must keep resolving from its legacy path, with a DeprecationWarning naming its new import, until a pyoaev major release removes the shims.**

> That covers names, the behaviour of legacy constructors (see TDR [shims-return-the-identical-sdk-object](shims-return-the-identical-sdk-object.tdr.md)) and the patch
> targets connectors lean on (see TDR [legacy-patch-targets-are-part-of-the-surface](legacy-patch-targets-are-part-of-the-surface.tdr.md)). What moves into the SDKs is the released
> `pyoaev` behaviour.

---

## **In Practice**
| *How this TDR manifests in the real world.*

- `from pyoaev.configuration import Configuration` warns and returns `xtm_oaev_sdk.Configuration`.
- `test/test_legacy_surface.py` checks that the names in modules of `pyoaev` still resolve (TDR [legacy-surface-guarded-from-the-release](legacy-surface-guarded-from-the-release.tdr.md)).
- The real collectors|injectors own suites ran against the released `pyoaev`, then against the new stack. Identical results.
- The removal steps for the next major release are already written down in `docs/shim_strategy.md`.

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

| Approach | Result | Lesson |
| --- | --- | --- |

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- a `pyoaev` major release is planned: the shims are removed and this TDR is revoked or superseded;
- every collector|injector imports from the SDKs and nobody consumes the legacy paths anymore;
- a deprecation policy fixes a time- or release-bound window instead of "until the next major".

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- The legacy surface runs wider than `__all__`: collectors also use names a module merely imported (`pyoaev.daemons.base_daemon.Configuration`), and patch targets.
- A few observable differences are not API breaks. They were accepted, then documented: warnings on legacy access, SDK module names for unnamed loggers, thin subclasses for the client-building adapters.

---

## **Resources**
- [Shim strategy](../shim_strategy.md)
- [Legacy surface guard](../../../../test/test_legacy_surface.py)
