# Data-and-behaviour classes split: the public class extends the seam data
---
scope: [xtm-oaev-sdk, collectors-sdk, architecture]
status: draft
superseded_by:
supersedes:
Aliases:
Creation Date: 2026/10/14 16:25:31
Modification Date: 2026/10/14 16:25:31
---

## ELI5

Some classes, like `Contract`, hold both data and actions. We cut them in two: the plain
data lives in the seam (the agreement layer), and the public class adds the actions on
top. You still create `Contract(...)` exactly as before.

---

## **Why This Exists**
| *The forcing reality that demanded this TDR.*

> `Contract` and `Expectation` are what users construct, and both mix data with behaviour
> (default variables, serialization, matching, updates). The seam cannot depend on
> behaviour. Users must keep constructing the same class.

---

## **The TDR**
| **When a user-facing class mixes data and behaviour, the seam holds the data class and the public class extends it, adding behaviour through ports; the core only knows the seam type.**



---

## **In Practice**
| *How this TDR manifests in the real world.*

```python
@dataclass
class Contract(ContractData):
    variables: list[ContractVariable] = field(
        default_factory=lambda: _variables.default_variables()
    )

    def to_contract_add_input(self, source_id: str) -> dict[str, Any]:
        return _serializer.to_add_input(self, source_id)
```

collectors-sdk plays the same move with `ExpectationData` / `Expectation`. After the
contracts split, the JSON of `to_contract_add_input()`, `to_contract_update_input()` and
`prepare_contracts()` came out byte-identical to the previous commit.

---

## **Alternatives Explored**
| *The paths we tried and why they failed.*

No alternative was explored for this decision.

---

## **Mutation Trigger**
| *When this TDR should be reconsidered.*

This TDR becomes questionable if:
- the data and behaviour can be separated in the user-facing API itself (a major version);
- the core needs behaviour from the public subclass.

## **Hansei**
| *Scars, surprises, and extracted wisdom.*

What we learned while forging this TDR:

---

## **Resources**
- [Seam strategy, patterns](../seam_strategy.md)
- [Contracts adapter](../../xtm_oaev_sdk/public/contracts.py)
