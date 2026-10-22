# Consumers import from the package root only
---
scope: [xtm-oaev-sdk, collectors-sdk, injectors-sdk, public-api]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

Always import from the top of the SDK: `from xtm_oaev_sdk import X`. The folders inside
(`public`, `seam`, `_core`) are the SDK's internal plumbing. What's in there can move at
any time, without asking you.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> The layers are internal wiring. Refactors moved names between `public`, `seam` and
> `_core` modules (out of `seam/configuration/__init__.py`, for one) and the package root
> never flinched.

---

## **The TDR**
| **Consumers must import SDK names from the package root (xtm_oaev_sdk, collectors_sdk, injectors_sdk); public, seam and _core module paths are internal and may move.**

> The package root's `__all__` is the stable API.

---

## **In Practice**
| *How this TDR manifests in the real world.*

```python
from xtm_oaev_sdk import Configuration, ContractBuilder, SignatureManager
```

Every legacy shim message points to the root import: `Use 'from xtm_oaev_sdk import X' instead.`

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

No alternative was explored for this decision.

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- the root namespace grows too large to stay flat and sub-namespaces become public;
- a consumer needs a seam type that the root does not export.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- A surface tool that treats every module as public reports internal moves as removals.

---

## **Resources**
- [README](../../README.md)
