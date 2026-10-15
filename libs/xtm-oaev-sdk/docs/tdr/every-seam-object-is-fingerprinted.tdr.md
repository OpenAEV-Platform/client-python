# Every seam object is fingerprinted
---
scope: [xtm-oaev-sdk, seam, testing, versioning]
status: draft
superseded_by:
supersedes: cross-process-seams-pin-their-json-schemas
Aliases:
Creation Date: 2026/10/15 08:36:35
Modification Date: 2026/10/15 08:36:35
---

## ELI5

The seam is the promise between the parts of the SDK, and part of that promise travels
to the platform. Every piece of it gets a fingerprint. Change a piece, even by accident,
and its fingerprint changes: a test goes red. Then you choose, on purpose, to bump the
version and save the new fingerprint.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> Pinning the JSON schemas of two seam modules left the rest of the seam wide open:
> ports, enums living elsewhere, constants, functions. And each pin kept its own model
> list, which nobody remembered to extend. A seam change could walk right through with
> every test green.

---

## **The TDR**
| **Every public top-level object of every seam module must be fingerprinted in one golden, discovered dynamically, and the golden is regenerated only together with a deliberate seam change and its version bump.**

> No hand-kept list. The next run picks up any new seam module or object.

---

## **In Practice**
| *How this TDR manifests in the real world.*

- `test/seam/generate_seam_golden.py` parses every `*.py` file under `xtm_oaev_sdk/seam/` and fingerprints each public class, function, constant and type alias: the sha256 of its normalized AST, minus formatting, comments and docstrings. Pydantic models get their validation and serialization JSON schemas folded in too.
- It rewrites `test/seam/fixtures/seam_golden.json`: changed fingerprints updated, new objects added, deleted ones removed. It prints what moved, and warns when a capability changed but its version did not.
- `test/seam/test_seam_golden.py` recomputes the fingerprints and fails on anything added, removed or changed, and names every object. It also checks that the package root re-exports the seam's own objects.
- `test/seam/test_seam_closed.py` keeps the two closed-import checks: `port_io` imports only the signatures seam, and the signatures seam imports nothing from the SDK.
- The step-by-step procedure lives in `CONTRIBUTING.md`, "Seam golden".

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

- **Keep the JSON schema pins, add more models to their lists.** Rejected: they only see pydantic models, and someone still has to keep the lists by hand.
- **Fingerprint `inspect.getsource()`.** Rejected: a comment or a reformat would trip it. That is noise, not a contract change.

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- the seam contracts are published and checked by the platform side;
- a CI contract tool replaces the in-repository golden;
- Python or pydantic upgrades keep moving fingerprints while no contract changed.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- The AST drops formatting and comments for free. Docstrings do not go quietly: strip them by hand. Skip the AST's empty fields too, or the text shifts between Python versions.
- A pydantic model's JSON schema carries its docstring and field descriptions. Those reach the wire, so rewording one counts as a change.
- The golden stores hashes, not definitions. A failure tells you which object moved; `git diff` on it tells you how.

---

## **Resources**
- [Seam golden tests](../../test/seam/)
- [Contributing: seam golden](../../CONTRIBUTING.md#seam-golden-testseam)
- [Superseded: seams crossing a process boundary pin their JSON schemas](cross-process-seams-pin-their-json-schemas.tdr.md)
