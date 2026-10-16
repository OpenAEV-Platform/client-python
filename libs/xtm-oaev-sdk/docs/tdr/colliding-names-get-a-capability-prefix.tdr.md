# Colliding moved names are renamed with their capability prefix
---
scope: [xtm-oaev-sdk, public-api, shims]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

You import everything in the SDK from one single place, so two things can't share a
name. pyoaev had two different things both called `ExpectationType`. They became
`SignatureExpectationType` and `ContractExpectationType`. The old names still work, and
they tell you the new one.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> The SDK root namespace is flat (TDR [import-from-the-package-root](import-from-the-package-root.tdr.md)). `pyoaev` had two different
> `ExpectationType`, one in `signatures` and one in `contracts.contract_config`. Two
> classes, one name, one flat root: they could not both keep it.

---

## **The TDR**
| **A moved name that collides with another capability's name in the flat root namespace must be renamed with its capability as prefix, and its legacy shim must name the new name.**

> The rule generalises the two existing cases.

---

## **In Practice**
| *How this TDR manifests in the real world.*

- `pyoaev.signatures.ExpectationType` → `xtm_oaev_sdk.SignatureExpectationType`
- `pyoaev.contracts.contract_config.ExpectationType` → `xtm_oaev_sdk.ContractExpectationType`

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

No alternative was explored for this decision.

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- public sub-namespaces are introduced;
- a collision appears where a capability prefix does not disambiguate.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- No material lesson beyond the TDR itself.

---

## **Resources**
- [Shim strategy, kinds of shims](../shim_strategy.md)
