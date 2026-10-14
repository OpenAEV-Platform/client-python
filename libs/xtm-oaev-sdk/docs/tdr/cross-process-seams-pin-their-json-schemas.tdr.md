# Seams crossing a process boundary pin their JSON schemas
---
scope: [xtm-oaev-sdk, signatures, port_io, testing, versioning]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 21:39:05
---

## ELI5

Some of our data gets read by another program, like the platform. Change the shape of
that data by accident and the other program breaks, while our own tests notice nothing.
So we keep a fingerprint of each shape. Change the shape, a test fails, and you have to
choose, on purpose, to bump the version and update the fingerprint.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> The inbound signature I/O (injector configs, execution signatures, tool output) and the
> port I/O wire payloads leave the process. Let a schema drift silently and the other side
> breaks while every local test stays green.

---

## **The TDR**
| **A seam whose models cross a process boundary must pin their JSON schemas with golden hashes, regenerated only together with a version bump.**

> Seams whose models never leave the process carry a `SEAM_VERSION` and no pinned schema.

---

## **In Practice**
| *How this TDR manifests in the real world.*

- `test/seam/test_signatures_seam_schema_pin.py` and `test/seam/test_port_io_schema_pin.py` hash each model's `model_json_schema()`, serialized with sorted keys, and hold it against the golden hashes in `test/seam/fixtures/`.
- The same tests also assert the seam version, make sure the seam module stays closed, and (signatures) that the package root re-exports the seam's own objects.
- To change the contract: change the model, bump the version and its expected value in the version test, run `test/seam/generate_*_golden.py`, and commit all of it together, in one go. The step-by-step procedure lives in `CONTRIBUTING.md`, "Pinned seam schemas".

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

No alternative was explored for this decision.

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- the schemas are published and checked by the platform side;
- a CI contract tool replaces the in-repository pins;
- dependency upgrades keep moving the hashes while the wire format stays exactly the same.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- These two pins predate the call to keep architecture checks out of the SDK tests.
- The golden files store hashes, not schemas. A failure tells you *that* a schema moved, never *how*: dumping `model_json_schema()` on both commits and diffing is the only way to see it.
- The hashed schema includes the docstrings of models and enums. Reword one and the pin trips, as surely as if you had retyped a field.
- Each pin test and its generator keep their own copy of the model list. Pin a new model and you edit both.

---

## **Resources**
- [Schema pin tests](../../test/seam/)
- [Contributing: pinned seam schemas](../../CONTRIBUTING.md#pinned-seam-schemas-testseam)
