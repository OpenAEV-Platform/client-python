# Importing pyoaev never warns; only touching a moved name does
---
scope: [pyoaev, shims, deprecation]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

Writing `import pyoaev` must never show a deprecation warning. A warning only shows up
when you actually use a name that moved to the SDKs. Otherwise it would warn people
about code they never touched, and crash programs that treat warnings as errors.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> A warning on a bare `import pyoaev` hits code that never touched a moved name, and it
> crashes anything running under `-W error`.

---

## **The TDR**
| **Importing any pyoaev module must not emit a DeprecationWarning; only accessing a moved name may warn.**

> `pyoaev`'s own code imports from the SDKs, never from its shims. And no module
> star-imports a shim module. Ever.

---

## **In Practice**
| *How this TDR manifests in the real world.*

- The package root binds the shim submodules and serves their names through its own `__getattr__`; `pyoaev.__all__` is unchanged.
- `test_importing_pyoaev_modules_is_silent` imports every `pyoaev` module under `-W error`.
- `test_sdk_objects_stay_silent_once_pyoaev_is_loaded` checks that SDK users get no warning.

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

| Approach | Result | Lesson |
| --- | --- | --- |
| Star-import shim modules from `pyoaev/__init__` | `import *` walks `__all__` and trips every lazy name: `import pyoaev` warned, and crashed under `-W error` | Serve package-level names through the root `__getattr__` |

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- the shims are removed;
- a moved name has to be eagerly bound at import time for a technical reason.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- `from pyoaev import *` still warns for the moved names in `pyoaev.__all__`. That is the signal doing its job, not a leak.

---

## **Resources**
- [Shim contract tests](../../test/common/shim/test_shim_contract.py)
- [collectors/injectors shim tests](../../../../test/test_sdk_split_shims.py)
