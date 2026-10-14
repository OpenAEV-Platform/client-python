# pyoaev hard-depends on the SDKs that host its former code
---
scope: [pyoaev, packaging, dependencies, compatibility]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

Old connectors only install pyoaev, but what they use lives in the SDKs now. So
installing pyoaev always installs the SDKs too, not only when you ask for an option.
That's what keeps old connectors running while the old paths still exist.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> A connector that lists only `pyoaev` still imports `CollectorDaemon`,
> `OpenAEVInjectorHelper` and friends from their legacy paths. Those names live in the
> SDKs now. For TDR [no-breaking-change-for-legacy-pyoaev-code](no-breaking-change-for-legacy-pyoaev-code.tdr.md) to hold, `pyoaev` has to carry them in.

---

## **The TDR**
| **While pyoaev ships deprecation shims, it must declare a hard dependency on every SDK those shims serve, never an optional extra.**

> Third-party packages `pyoaev` no longer imports itself (`pika`, `thefuzz`, `PyYAML`,
> `pydantic-settings`, `python-json-logger`) are gone from its own declaration. They still
> ride in transitively through the SDKs, so an install pulls the same packages as before.

---

## **In Practice**
| *How this TDR manifests in the real world.*

- `pyproject.toml` requires `xtm-oaev-sdk`, `collectors-sdk` and `injectors-sdk` (`>=0.1.0,<0.2.0`).
- Until the SDKs are published, CI pulls collectors-sdk and injectors-sdk straight from git through `libs/sdk-requirements.txt`.

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

| Approach | Result | Lesson |
| --- | --- | --- |
| Optional extras (`pyoaev[collectors]`, `pyoaev[injectors]`) with lazily loaded SDKs | Proposed to spare every `pyoaev` install both SDKs; legacy imports would then blow up for connectors listing only `pyoaev` | Rejected: no breaking change wins |

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- the shims are removed: `collectors-sdk` and `injectors-sdk` can be dropped (keep `xtm-oaev-sdk` if the client still uses its errors and transport models);
- an SDK gains heavy dependencies that `pyoaev` users should not pay for.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- The install footprint did not grow. What moved out of `pyoaev` comes straight back in through the SDKs.

---

## **Resources**
- [pyproject.toml](../../../../pyproject.toml)
- [SDK requirements for CI](../../../../libs/sdk-requirements.txt)
