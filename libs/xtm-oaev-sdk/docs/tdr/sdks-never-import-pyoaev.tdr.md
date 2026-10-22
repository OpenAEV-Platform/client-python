# The SDKs never depend on pyoaev; the API client is injected
---
scope: [xtm-oaev-sdk, collectors-sdk, injectors-sdk, dependencies]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

The SDKs never use pyoaev. When they need to talk to the OpenAEV platform, you hand them
the client (`api_client=` or `transport=`). pyoaev already depends on the SDKs: the
other way around would make a loop, and chain the SDKs to one specific client.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> `pyoaev` depends on the SDKs (TDR [pyoaev-hard-depends-on-the-sdks-during-deprecation](pyoaev-hard-depends-on-the-sdks-during-deprecation.tdr.md)) and is meant to end up as the OpenAEV HTTP
> client, and only that. The SDKs carry the shared, client-free runtime. One import back
> into `pyoaev` and you get a circular package dependency, with that runtime welded to a
> single client.

---

## **The TDR**
| **xtm-oaev-sdk, collectors-sdk and injectors-sdk must never import pyoaev; anything that talks to the platform receives its API client or transport as an argument typed by a seam protocol.**

> The injected types are `BaseClient` (seam `common`) and `SignatureTransportProtocol`
> (seam `signatures`). `pyoaev.OpenAEV` and its signature API satisfy them.

---

## **In Practice**
| *How this TDR manifests in the real world.*

```python
SignatureManager(transport=api.signature)
CollectorDaemon(configuration=configuration, callback=collect, api_client=api, collector_type="...")
OpenAEVInjectorHelper(config, icon, api_client=api)
```

- No injected client? `BaseDaemon` and `OpenAEVInjectorHelper` fall back on the overridable `_create_default_api_client` hook, and the SDK default raises rather than build one.
- `pyoaev` brings the legacy self-building constructors back by overriding that hook (TDR [shims-return-the-identical-sdk-object](shims-return-the-identical-sdk-object.tdr.md)).
- `test/test_boundaries.py` in each SDK fails the moment a source imports `pyoaev` (or `requests`).

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

| Approach | Result | Lesson |
| --- | --- | --- |
| Keep the legacy constructors that built `OpenAEV(...)` themselves | That drags `pyoaev` into the SDK | Client construction lives in `pyoaev`'s client-building adapters, and only there |

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- the API client itself moves into an SDK;
- an SDK needs a client capability that cannot be expressed as a protocol without importing `pyoaev` types.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- Pulling client construction out took a hook (`_create_default_api_client`): that is how `pyoaev` restores the old constructors without the SDK ever knowing.

---

## **Resources**
- [xtm-oaev-sdk boundaries test](../../test/test_boundaries.py)
- [Shim strategy, dependency direction](../shim_strategy.md)
