# Shims return the identical SDK object; adapters only where constructors differ
---
scope: [pyoaev, shims, compatibility]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

When old code asks pyoaev for a moved name, it gets the very same object the SDK
provides. Not a copy, not a look-alike, so checks like `isinstance` and `is` keep
working. The only exceptions are the classes that used to build the API client
themselves: they come back as a thin subclass that still does it.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> Legacy code compares with `is`, checks `isinstance`, subclasses, pickles by reference
> and patches. Hand it anything but the SDK object itself and one of those can snap. Some
> legacy constructors, though, built the `OpenAEV` client themselves, and the SDKs no
> longer do that (TDR [sdks-never-import-pyoaev](sdks-never-import-pyoaev.tdr.md)).

---

## **The TDR**
| **A shim must return the SDK object itself; a legacy name may resolve to a thin subclass only to restore legacy constructor behaviour, and that subclass must be one single object whatever legacy path reaches it.**

> A legacy value with no public replacement (`variable_helper.USER`…, `helpers.TRUTHY` /
> `FALSY`) is served as the literal value, with a message pointing at the right API.

---

## **In Practice**
| *How this TDR manifests in the real world.*

| Legacy name | Subclass of | Adds |
|---|---|---|
| `pyoaev.daemons.BaseDaemon` | `xtm_oaev_sdk.BaseDaemon` | `_create_default_api_client()` builds `OpenAEV` |
| `pyoaev.daemons.CollectorDaemon` | `collectors_sdk.CollectorDaemon` + the legacy `BaseDaemon` | same hook |
| `pyoaev.signatures.SignatureManager` | `xtm_oaev_sdk.SignatureManager` | `SignatureManager(client, logger)` sends through `client.signature` |
| `pyoaev.helpers.OpenAEVInjectorHelper` | `injectors_sdk.OpenAEVInjectorHelper` | `_create_default_api_client(config)` builds `OpenAEV` |

`pyoaev.daemons.CollectorDaemon is pyoaev.daemons.collector_daemon.CollectorDaemon is pyoaev.helpers.CollectorDaemon`.

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

| Approach | Result | Lesson |
| --- | --- | --- |
| Wrapper class or proxy for every legacy name | Breaks identity, `isinstance` against the SDK class, metaclasses and introspection | Return the object; subclass only where behaviour must be restored |

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- the SDK classes gain a client factory that makes the adapters unnecessary;
- the shims are removed.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- The legacy `CollectorDaemon` has to inherit from the legacy `BaseDaemon` adapter too. Skip that and `isinstance(daemon, pyoaev.daemons.BaseDaemon)` fails.

---

## **Resources**
- [Shim strategy, client-building adapters](../shim_strategy.md)
- [Shim contract tests](../../test/daemons/shim/test_shim_contract.py)
- [collectors/injectors shim tests](../../../../test/test_sdk_split_shims.py)
