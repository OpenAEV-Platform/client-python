# Every SDK module imports on its own in a fresh interpreter
---
scope: [xtm-oaev-sdk, collectors-sdk, injectors-sdk, testing]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

Every file of the SDK has to work as the very first thing you import, in a fresh Python,
with warnings turned into errors. That flushes out hidden loops between files, the kind
that only work because the tests happen to import things in a lucky order.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> Three layers per capability, plus module-level default wiring: an import cycle can hide
> behind a lucky import order in the test session.

---

## **The TDR**
| **Every SDK module must import successfully as the first import of a fresh interpreter running with -W error.**



---

## **In Practice**
| *How this TDR manifests in the real world.*

`test_every_sdk_module_imports_first_in_a_fresh_interpreter` (in each SDK's
`test/test_boundaries.py`) runs `python -W error -c "import <module>"` for every module.

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

No alternative was explored for this decision.

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- a CI tool checks import cycles statically and the subprocess cost becomes a problem.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- No material lesson beyond the TDR itself.

---

## **Resources**
- [Boundaries test](../../test/test_boundaries.py)
