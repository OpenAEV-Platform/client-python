"""Local validation of inject content against a contract.

The mandatory checks mirror the platform's injector-contract health checks, rule for
rule (openaev-platform, ``openaev-api/.../healthcheck/utils/HealthCheckUtils.java``,
``runContentChecks``, and ``openaev-model/.../helper/InjectModelHelper.java``):

- a mandatory field must be set (``isFieldSet``): a target field (teams, assets, asset
  groups, credentials) when the inject carries it apart from its content, a text or
  textarea field when it holds text or its contract default is not blank
  (``isFieldValid``), any other field when its value is neither missing nor empty;
- when no field of a mandatory group is set, every member of the group is reported;
- a conditionally mandatory field must be set when its condition field holds one of the
  listed values (``getFieldValue``: the target ids, or the content's text, booleans and
  list items), or always when no value is listed; a condition field the contract does
  not declare is ignored.

Select choices and single-value cardinality, declared by the contract, are checked on
top: the platform's form enforces them where injects are written.
"""

from typing import Any, Iterable, Mapping, Sequence

from xtm_oaev_sdk.seam.contracts import (
    ContractCardinality,
    ContractData,
    ContractElement,
    ContractViolation,
)

__all__ = ["ContractValidation"]

_TEXT_TYPES = ("text", "textarea")


def _is_set(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, tuple, dict, set)):
        return len(value) > 0
    return True


def _text(value: Any) -> str:
    """The value as the platform reads it as text (``JsonNode.asText``)."""
    if value is None or isinstance(value, (list, tuple, dict, set)):
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _content_values(value: Any) -> list[str]:
    """The values a condition compares, as ``getFieldValue`` reads the content."""
    if isinstance(value, (list, tuple, set)):
        return [_text(item) for item in value if item is not None]
    if isinstance(value, (str, bool)):
        text = _text(value)
        return [text] if text else []
    return []


def _listed(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [_text(item) for item in value]
    return [_text(value)]


def _provided(provided: Mapping[str, Sequence[str]] | Iterable[str]) -> dict:
    if isinstance(provided, Mapping):
        return {key: [str(v) for v in values] for key, values in provided.items()}
    return {key: [] for key in provided}


class ContractValidation:
    """Implements ``ContractValidationPort``."""

    def validate(
        self,
        contract: ContractData | Iterable[ContractElement],
        content: dict[str, Any],
        provided: Mapping[str, Sequence[str]] | Iterable[str] = (),
    ) -> list[ContractViolation]:
        fields = list(
            contract.fields if isinstance(contract, ContractData) else contract
        )
        by_key = {element.key: element for element in fields}
        given = _provided(provided)

        def field_set(element: Any) -> bool:
            key = element.key
            if key in given:
                return True
            value = content.get(key)
            if getattr(element, "type", None) in _TEXT_TYPES:
                if _text(value):
                    return True
                default = getattr(element, "defaultValue", None)
                return isinstance(default, str) and bool(default.strip())
            return _is_set(value)

        violations: list[ContractViolation] = []
        reported_groups: set[str] = set()
        for element in fields:
            key = element.key
            if element.mandatory and not field_set(element):
                violations.append(
                    ContractViolation(
                        key, "mandatory", f"'{key}' is mandatory and not set"
                    )
                )
            group = [m for m in element.mandatoryGroups or [] if m in by_key]
            if group and not any(field_set(by_key[member]) for member in group):
                for member in group:
                    if member not in reported_groups:
                        reported_groups.add(member)
                        violations.append(
                            ContractViolation(
                                member,
                                "mandatory_group",
                                f"'{member}': one of {group} must be set",
                            )
                        )
            if self._condition_requires(
                element, content, by_key, given
            ) and not field_set(element):
                violations.append(
                    ContractViolation(
                        key,
                        "mandatory_condition",
                        f"'{key}' is mandatory when"
                        f" {list(element.mandatoryConditionFields)} hold the listed"
                        " values",
                    )
                )
            violations.extend(self._value_violations(element, content.get(key)))
        return violations

    @staticmethod
    def _condition_requires(
        element: ContractElement,
        content: dict[str, Any],
        by_key: dict,
        given: dict[str, list[str]],
    ) -> bool:
        values = element.mandatoryConditionValues or {}
        for condition_key in element.mandatoryConditionFields or []:
            if condition_key is None or condition_key not in by_key:
                continue
            if isinstance(values, dict) and condition_key in values:
                expected = _listed(values[condition_key])
                actual = given.get(condition_key) or _content_values(
                    content.get(condition_key)
                )
                if not any(value in expected for value in actual):
                    continue
            return True
        return False

    @staticmethod
    def _value_violations(
        element: ContractElement, value: Any
    ) -> list[ContractViolation]:
        if not _is_set(value):
            return []
        key = element.key
        found: list[ContractViolation] = []
        cardinality = getattr(element, "cardinality", None)
        if cardinality == ContractCardinality.One and isinstance(value, (list, tuple)):
            if len(value) > 1:
                found.append(
                    ContractViolation(
                        key,
                        "cardinality",
                        f"'{key}' takes a single value, got {len(value)}",
                    )
                )
        choices = getattr(element, "choices", None)
        if choices:
            values = value if isinstance(value, (list, tuple, set)) else [value]
            unknown = [str(v) for v in values if str(v) not in choices]
            if unknown:
                found.append(
                    ContractViolation(
                        key,
                        "choice",
                        f"'{key}' has {unknown}, not among {sorted(choices)}",
                    )
                )
        return found
