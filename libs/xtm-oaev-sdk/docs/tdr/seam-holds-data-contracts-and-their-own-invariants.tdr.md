# The seam holds data contracts and only their intrinsic invariants
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

The seam only holds data: models, lists of allowed values, errors, and small rules that
check or compute something from that data alone. Anything that talks to the outside
world, runs the show, or needs another part of the SDK goes behind a port instead.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> The seam must stay closed (TDR [public-seam-core-dependency-rule](public-seam-core-dependency-rule.tdr.md)), yet the data crossing it carries rules of its
> own: validators, derived fields, errors that extract their own message. Those rules are
> part of what the data is. I/O and orchestration are not.

---

## **The TDR**
| **A seam may contain data contracts and logic that only reads or derives from their own data; anything doing I/O, orchestrating, or needing another capability goes behind a port.**

> Data contracts: pydantic models, dataclasses, enums, exceptions, type aliases, constants.

---

## **In Practice**
| *How this TDR manifests in the real world.*

- validators and derived fields: `ConfigurationHint`, `ExpectationData`'s null signatures coerced to `[]`;
- `__post_init__` invariants of the contract elements;
- value objects: `SignatureMatch`, `SignatureType.make_struct_for_matching`;
- exceptions, including `OpenAEVError`'s message extraction: the core raises them and users catch them, so both sides must reach them.

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

No alternative was explored for this decision.

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- an invariant needs external state or another capability: it must move behind a port;
- the seams are generated from an external schema that cannot carry logic.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- Exceptions belong in the seam: both sides of the boundary need them.

---

## **Resources**
- [Seam strategy, what goes where](../seam_strategy.md)
