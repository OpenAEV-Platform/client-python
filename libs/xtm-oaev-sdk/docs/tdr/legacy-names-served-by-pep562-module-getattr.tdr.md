# Legacy names are served by a directly assigned PEP 562 __getattr__
---
scope: [pyoaev, deprecation, shims]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

When old code asks pyoaev for a name that moved, a small lookup function in the old
module catches the request. It shows a warning pointing to the new import, then hands
back the real SDK object. It's plugged in directly, so the warning points at your line
of code, not at pyoaev's.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> Legacy access has three jobs: warn, so people migrate; return the SDK object, so nothing
> else moves; and leave SDK users alone.

---

## **The TDR**
| **A moved name must be served from its legacy module by a module-level __getattr__ built with make_deprecated_getattr and assigned directly, never wrapped in a def.**

> The returned `__getattr__` warns with `DeprecationWarning` and `stacklevel=2`, which pins
> the warning on the consumer's line. Unknown names still raise `AttributeError`.

---

## **In Practice**
| *How this TDR manifests in the real world.*

```python
__getattr__ = _make_deprecated_getattr(
    {
        name: (f"Use 'from xtm_oaev_sdk import {name}' instead.", getattr(_sdk, name))
        for name in __all__
    },
    module_name=__name__,
)
```

`__all__` lists the lazily served names, flagged with `# noqa: F822`.

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

| Approach | Result | Lesson |
| --- | --- | --- |
| `typing_extensions.deprecated(...)(cls)` | Patches the original class in place: the moment anything imported `pyoaev`, `xtm_oaev_sdk.Configuration()` warned too | Never mutate the SDK object to deprecate its legacy name |
| `def __getattr__(name): return _deprecated_getattr(name)` | The extra frame pins the warning on the shim file, and the default filters hide it from scripts | Assign the built `__getattr__` directly |
| Wrapper class or proxy | Breaks identity: `isinstance`, metaclasses, signature introspection | See TDR [shims-return-the-identical-sdk-object](shims-return-the-identical-sdk-object.tdr.md) |
| Plain re-export | Keeps identity, never warns. Nobody ever migrates | The warning is the migration signal |

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- the shims are removed.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- `from <package> import X` on a shim package warns twice (importlib's `_handle_fromlist` probes with `hasattr`); plain modules warn once. Accepted: that one is baked into PEP 562.

---

## **Resources**
- [Shim strategy, mechanism](../shim_strategy.md)
- [Deprecation adapter](../../xtm_oaev_sdk/public/deprecation.py)
