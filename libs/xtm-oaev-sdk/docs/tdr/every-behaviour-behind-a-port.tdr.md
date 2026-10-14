# Every piece of behaviour goes behind a port, even a one-liner
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

Every piece of logic, even a one-line function, follows the same three-part pattern: an
agreement (the port), the code that does the job, and the public entry point people
call. No exception for small things. That way nobody wastes time arguing about which
rule applies.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> Give a layering rule size-based exceptions and every new helper turns into a debate
> about whether it deserves a seam. The call was uniformity: "we want unicity everywhere
> and not some exception".

---

## **The TDR**
| **Every piece of behaviour exposed by an SDK goes through a seam Protocol port, one _core implementation and a public adapter, whatever its size.**

> Data contracts are not behaviour; they live in the seam directly (TDR [seam-holds-data-contracts-and-their-own-invariants](seam-holds-data-contracts-and-their-own-invariants.tdr.md)).

---

## **In Practice**
| *How this TDR manifests in the real world.*

`is_truthy` gets `TruthinessPort`, `Truthiness` and the public `is_truthy`: exactly the
treatment `SignatureManager` gets. `build_marker` goes through `MarkerPort` / `MarkerBuilder`.

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

| Approach | Lesson |
| --- | --- |
| Reserve ports for real I/O boundaries; leave pure helpers such as `copy_dict` without a seam | Uniformity beats per-case judgement |

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- the boilerplate measurably slows contributions or reviews;
- a generator or base class can provide the port/adapter pair, changing what "one implementation per port" costs.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- The price is more files for trivial helpers.

---

## **Resources**
- [Seam strategy, behind a port](../seam_strategy.md)
