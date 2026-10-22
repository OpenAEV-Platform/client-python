# Adapters pass their own methods to the core to keep dispatch and patch points
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

Some SDK classes used to call their own methods, and that logic moved to the core. So
now the class hands its own method to the core, instead of letting the core redo the
call. Override that method or fake it, and it still counts.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> Logic moves to the core. If the core then reimplemented the calls that used to go
> through `self`, subclass overrides and test patches would be bypassed without a sound.

---

## **The TDR**
| **When the original code dispatched through its own object, the adapter must pass the bound method or a callable to the core instead of letting the core reimplement the call.**

> Same deal for a dependency the core may not import: the adapter passes it down.

---

## **In Practice**
| *How this TDR manifests in the real world.*

```python
def _source_context(self, config):
    return _engine.source_context(
        config, self.resolve_container_ip, lambda: self._cached_ipv6
    )
```

- `SignatureManager.post_execution_updates` passes `self._utcnow`.
- `Expectation.match_alert` passes `self.match_fuzzy` / `self.match_simple`.
- `OpenAEVDetectionHelper` passes `self.match_alert_element_fuzzy` / `self._decode_value`.
- `CollectorDaemon` passes `self._try_callback` to the scheduler.
- `Configuration.schema()` passes the public `ConnectorConfigSchemaGenerator` to the core resolver.

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

No alternative was explored for this decision.

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- the hooks are formally deprecated and no longer need to stay overridable;
- the core gets an explicit strategy object replacing the callables.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:
- Call order is part of the behaviour: `_utcnow` is still read only after the tool output validates.

---

## **Resources**
- [Seam strategy, pass callables](../seam_strategy.md)
- [Signatures adapter](../../xtm_oaev_sdk/public/signatures.py)
