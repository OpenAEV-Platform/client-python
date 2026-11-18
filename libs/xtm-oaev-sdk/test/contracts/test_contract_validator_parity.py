"""Parity of the contract validator with the platform's health-check.

Feature: Contract validation verdicts match the platform's
  Each case of ``fixtures/health_check_parity.json`` is one test of the platform's own
  health-check (``HealthCheckUtilsTest``): the contract fields as the platform serializes
  them, the inject content, the targets the inject carries apart from its content, and
  whether the platform finds the inject ready. The SDK reaches the same verdict.
"""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import pytest
import xtm_oaev_sdk as sdk

PARITY = json.loads(
    (Path(__file__).parent / "fixtures" / "health_check_parity.json").read_text(
        encoding="utf-8"
    )
)["cases"]


def _given_contract_validator() -> Callable[..., list[Any]]:
    """Given the SDK validates inject content against a contract"""
    return sdk.ContractValidator().validate


def _given_platform_fields(case: dict[str, Any]) -> list[Any]:
    """Given the contract fields as the platform serializes them"""
    return [
        SimpleNamespace(
            key=field["key"],
            type=field["type"],
            mandatory=field.get("mandatory", True),
            mandatoryGroups=field.get("mandatoryGroups"),
            mandatoryConditionFields=field.get("mandatoryConditionFields"),
            mandatoryConditionValues=field.get("mandatoryConditionValues"),
            defaultValue=field.get("defaultValue"),
            cardinality=field.get("cardinality"),
            choices=field.get("choices"),
        )
        for field in case["fields"]
    ]


def _when_validating(
    validate: Callable[..., list[Any]], fields: list[Any], case: dict[str, Any]
) -> list[Any]:
    """When the content is validated, with the targets the inject carries given apart"""
    provided = {key: values for key, values in case["provided"].items() if values}
    return validate(fields, case["content"], provided)


def _then_ready_is(violations: list[Any], ready: bool) -> None:
    """Then the inject is ready exactly when the platform finds it ready"""
    assert (violations == []) is ready, f"Expected ready={ready}, got {violations}"


@pytest.mark.parametrize(
    "case", PARITY, ids=[case["source"].split(".")[-1] for case in PARITY]
)
def test_verdict_matches_the_platform_health_check(case: dict[str, Any]) -> None:
    """It finds an inject ready exactly when the platform's health-check does.

    Scenario Outline: The verdict matches the platform health-check
      Given the SDK validates inject content against a contract
      And the contract fields as the platform serializes them
      When the content is validated, with the targets the inject carries given apart
      Then the inject is ready exactly when the platform finds it ready
    """
    validate = _given_contract_validator()
    fields = _given_platform_fields(case)
    violations = _when_validating(validate, fields, case)
    _then_ready_is(violations, case["ready"])
