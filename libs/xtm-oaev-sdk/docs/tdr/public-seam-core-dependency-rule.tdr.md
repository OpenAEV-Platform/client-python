# public and _core depend on the seam; the seam depends on neither
---
scope: [xtm-oaev-sdk, collectors-sdk, injectors-sdk, architecture]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

Each part of an SDK has three layers: `public` (what users touch), `_core` (the engine)
and the seam (the agreement between the two). Both sides lean on the agreement, never on
each other. The one exception: `public` chooses which engine to plug in. So the engine
can be rebuilt freely, as long as it keeps the agreement.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> The SDKs were designed in three layers: `public` is what users get, `_core` is the code
> behind it, and the seam is the contract between the two, so that "as long as `_core`
> answers it, `public` stays usable with no breaking change".

---

## **The TDR**
| **Within each SDK capability, the seam imports neither public nor _core, _core never imports public, and public imports _core only to wire the default implementation of each port.**

> Public never hands out a core object. Every exported name is either an adapter defined
> in `public/` or a contract defined in `seam/`. The seam may import the standard library,
> third-party libraries, other packages' public API and sibling seam modules, and that is
> the whole list.

---

## **In Practice**
| *How this TDR manifests in the real world.*

```python
_truthiness: TruthinessPort = Truthiness()
_sources: ConfigurationSourcesPort = ConfigurationSources()
_resolver: ConfigurationResolverPort = ConfigurationResolver(_sources, _truthiness)
```

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

| Approach | Result | Lesson |
| --- | --- | --- |

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- users need to swap implementations at runtime beyond the module-level defaults;

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:

---

## **Resources**
- [Seam strategy, rules](../seam_strategy.md)
