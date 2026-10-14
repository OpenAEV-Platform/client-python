# Legacy patch targets are part of the compatibility surface
---
scope: [pyoaev, shims, testing, compatibility]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

The connectors' tests swap some pyoaev pieces for fakes: they "patch" them. Those pieces
have to stay where the tests expect them, and swapping them has to keep affecting the
code that really runs. Otherwise those tests break, with no import error to tell you
why.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> Connector test suites patch `pyoaev` module attributes. Before a single line moved,
> every `pyoaev` patch target used by the connectors' tests was listed. Move the code
> without keeping them and those suites break, without a single import error.

---

## **The TDR**
| **Module attributes that connectors patch must stay reachable at their legacy path and still reach the code that actually runs.**



---

## **In Practice**
| *How this TDR manifests in the real world.*

- `pyoaev.signatures.signature_manager` still imports `socket` and `subprocess`: patching `...signature_manager.socket.gethostbyname` reaches the shared stdlib module the SDK uses.
- The client-building adapters call `OpenAEV` through their module global, so `patch("pyoaev.daemons.base_daemon.OpenAEV")` and `patch("pyoaev.helpers.OpenAEV")` apply.
- `pyoaev.utils.PingAlive.start` and `pyoaev.daemons.collector_daemon.CollectorDaemon._setup` land on the class the connectors instantiate (TDR [shims-return-the-identical-sdk-object](shims-return-the-identical-sdk-object.tdr.md)).

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

No alternative was explored: the patch targets counted as surface from day one.

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- the connectors stop patching `pyoaev` paths;
- the shims are removed.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- A patch target can be a stdlib module re-bound in a legacy module. Keep the import line and it keeps working; that is all it takes.

---

## **Resources**
- [collectors/injectors shim tests](../../../../test/test_sdk_split_shims.py)
- [Shim strategy, rules learned the hard way](../shim_strategy.md)
