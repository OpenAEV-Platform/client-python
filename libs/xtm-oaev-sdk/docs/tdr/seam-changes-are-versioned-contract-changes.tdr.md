# A seam change is a versioned contract change
---
scope: [xtm-oaev-sdk, collectors-sdk, injectors-sdk, versioning]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

The seam is the agreement between the public part and the engine. Changing the engine is
free. Changing the agreement changes things for users, so it gets a new version number
and a changelog line. And if users can see the change, the old way keeps working, with a
warning, first.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> The whole point of the seam: the public API survives any core rewrite. Touch the seam
> itself and you have changed the contract, and unlike a core change, that has to be
> announced.

---

## **The TDR**
| **Any change to a seam contract (field, type, enum member, error, port signature) must bump that seam's version and be recorded in the changelog, and a change reaching the public surface must go through a deprecation shim first.**

> Every capability seam exposes `SEAM_VERSION`; `port_io` is versioned by
> `PORT_IO_CONTRACT_VERSION`.

---

## **In Practice**
| *How this TDR manifests in the real world.*

- every capability seam of the three SDKs defines `SEAM_VERSION`.
- `seam/port_io/models.py` defines `PORT_IO_CONTRACT_VERSION`.
- Deprecations use `make_deprecated_getattr` (TDR [legacy-names-served-by-pep562-module-getattr](legacy-names-served-by-pep562-module-getattr.tdr.md)).

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

No alternative was explored for this decision.

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- seam versions get derived automatically by tooling;
- the release process ties seam versions to package versions.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- No changelog file exists in the SDKs yet. The first seam change gets to create it.

---

## **Resources**
- [Seam strategy, versioning](../seam_strategy.md)
