# The legacy surface is guarded against the released pyoaev
---
scope: [pyoaev, testing, compatibility]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

We keep a list of every public name in the pyoaev people actually installed, and a test
checks they all still work. That list comes from the real release, not from our work in
progress. Otherwise it would happily accept a name we lost by mistake. The old tests of
the moved code stay exactly as they were.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> Generate the guard from the working tree and it blesses whatever the split produced,
> lost names included. The reference has to be what users actually installed.

---

## **The TDR**
| **The legacy-surface guard must be generated from the released pyoaev package, and the pre-split tests of moved code must be kept verbatim against their legacy paths.**

> New behaviour tests target the SDKs. The moved `pyoaev` tests live under
> `libs/xtm-oaev-sdk/test/<capability>/shim/`, still hammering the legacy imports.

---

## **In Practice**
| *How this TDR manifests in the real world.*

- `test/generate_legacy_surface.py` records `test/fixtures/legacy_surface.json` from `pyoaev`.
- `test/test_legacy_surface.py` checks every one still resolves.

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

No alternative was explored for this decision.

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- the shims are removed.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- Moved verbatim, the old tests become a second guard: same assertions, still driving the legacy paths.

---

## **Resources**
- [Legacy surface guard](../../../../test/test_legacy_surface.py)
- [Legacy surface generator](../../../../test/generate_legacy_surface.py)
