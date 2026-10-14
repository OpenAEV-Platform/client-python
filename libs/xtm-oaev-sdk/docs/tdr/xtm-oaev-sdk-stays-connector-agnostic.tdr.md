# xtm-oaev-sdk stays agnostic of collectors, injectors and transports
---
scope: [xtm-oaev-sdk, dependencies, architecture]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

xtm-oaev-sdk is the shared base of both collectors and injectors. Nothing in it may
serve only one of them, and it stays away from libraries that belong elsewhere: RabbitMQ
and fuzzy matching go with injectors-sdk and collectors-sdk, HTTP requests with pyoaev.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> xtm-oaev-sdk is "the common sdk" under collectors-sdk and injectors-sdk. Put collector-
> or injector-specific code in it and you force it on the other connector type.

---

## **The TDR**
| **xtm-oaev-sdk must not contain collector- or injector-specific runtime, nor import pika, thefuzz or requests; those belong to collectors-sdk, injectors-sdk or pyoaev.**



---

## **In Practice**
| *How this TDR manifests in the real world.*

`test/test_boundaries.py` fails if an SDK source imports `pyoaev`, `requests`, `pika` or
`thefuzz`, or defines `ListenQueue`, `OpenAEVConfigHelper`, `OpenAEVCollectorHelper`,
`OpenAEVInjectorHelper`, `OpenAEVDetectionHelper` or `create_mq_ssl_context`.

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

No alternative was explored for this decision.

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- collectors and injectors converge on a shared transport;
- a third connector type needs part of a type-specific runtime.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- No material lesson beyond the TDR itself.

---

## **Resources**
- [Boundaries test](../../test/test_boundaries.py)
