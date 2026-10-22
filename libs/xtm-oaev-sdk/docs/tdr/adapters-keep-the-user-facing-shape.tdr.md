# Public adapters keep the shape of the code they replace
---
scope: [xtm-oaev-sdk, collectors-sdk, injectors-sdk, compatibility]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

The classes you use from the SDK look and behave exactly like before: same names, same
arguments, same methods to override. Only the work they do moved, to a place behind
them. Think of swapping a car's engine without touching the steering wheel or the
pedals.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> The layering went onto existing code with behaviour held identical. Users subclass SDK
> classes, hand them to frameworks, read their attributes and override their hooks. A
> facade would snap inheritance.

---

## **The TDR**
| **A public adapter must keep the signatures, docstrings, attributes, overridable hooks and framework base class of the code it replaces; only the logic moves to the core.**



---

## **In Practice**
| *How this TDR manifests in the real world.*

- Framework subclasses stay subclasses and override only the hook: `EnhancedJSONEncoder` (`json.JSONEncoder.default`), `CustomJsonFormatter` (`add_fields`), `ConnectorConfigSchemaGenerator` (`GenerateJsonSchema`), `SettingsLoader` (`settings_customise_sources`), `PingAlive` / `ListenQueue` (`threading.Thread`).
- Stateful adapters keep attributes (`_configuration`, `api`, `logger`, `local_logger`…) and hooks (`_setup`, `_start_loop`, `_try_callback`, `_create_default_api_client`, `_utcnow`…).
- The public surface was compared before and after the refactors.

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

| Approach | Result | Lesson |
| --- | --- | --- |
| A facade in front of classes users subclass (`BaseDaemon`, `CollectorDaemon`, `BaseConfigModel`) | Would break inheritance | The adapter is the class; the logic behind it moves |

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- an SDK major version is allowed to change its public shape;
- a hook is formally deprecated.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- Adapters hold the state. The core holds the logic.

---

## **Resources**
- [Seam strategy, patterns](../seam_strategy.md)
