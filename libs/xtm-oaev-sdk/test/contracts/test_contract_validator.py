"""Tests for the local validation of inject content against its contract.

Feature: Contract validation without the platform
  Before an injector runs an inject without the platform, its content is checked
  against the injector contract the way the platform checks it: mandatory fields,
  mandatory groups and conditionally mandatory fields, plus the select choices and
  single-value cardinality the contract declares.
"""

from typing import Any, Callable

import pytest
import xtm_oaev_sdk as sdk


def _given_contract_validator() -> Callable[..., list[Any]]:
    """Given the SDK validates inject content against a contract"""
    validator = getattr(sdk, "ContractValidator", None)
    assert (
        validator is not None
    ), "Expected xtm_oaev_sdk.ContractValidator to exist on public surface"
    return validator().validate


def _given_scan_contract() -> list[Any]:
    """Given a scan contract with:
    | field         | type     | rule                                      |
    | targets       | text     | mandatory                                 |
    | assets        | asset    | in the mandatory group assets, hosts      |
    | hosts         | text     | in the mandatory group assets, hosts      |
    | scan_type     | select   | choices tcp, udp                          |
    | ports         | text     | mandatory when scan_type is tcp           |
    | report_format | select   | single value, choices json, xml           |
    """
    return [
        sdk.ContractText(key="targets", label="Targets", mandatory=True),
        sdk.ContractAsset(label="Assets", mandatoryGroups=["assets", "hosts"]),
        sdk.ContractText(
            key="hosts", label="Hosts", mandatoryGroups=["assets", "hosts"]
        ),
        sdk.ContractSelect(
            key="scan_type",
            label="Scan type",
            choices={"tcp": "TCP", "udp": "UDP"},
        ),
        sdk.ContractText(
            key="ports",
            label="Ports",
            mandatoryConditionFields=["scan_type"],
            mandatoryConditionValues={"scan_type": ["tcp"]},
        ),
        sdk.ContractSelect(
            key="report_format",
            label="Report format",
            choices={"json": "JSON", "xml": "XML"},
            cardinality=sdk.ContractCardinality.One,
        ),
    ]


def _given_valid_content(**overrides: Any) -> dict[str, Any]:
    """Given inject content that fills the scan contract"""
    content: dict[str, Any] = {
        "targets": "10.0.0.5",
        "hosts": "web-01",
        "scan_type": "tcp",
        "ports": "22,443",
        "report_format": "json",
    }
    content.update(overrides)
    return content


def _given_content_without(content: dict[str, Any], *keys: str) -> dict[str, Any]:
    """Given that content without "<keys>" """
    return {key: value for key, value in content.items() if key not in keys}


def _when_validating(
    validate: Callable[..., list[Any]],
    contract: list[Any],
    content: dict[str, Any],
    provided_keys: tuple[str, ...] = (),
) -> list[Any]:
    """When the content is validated against the contract"""
    return validate(contract, content, provided_keys)


def _then_content_is_valid(violations: list[Any]) -> None:
    """Then the content has no violation"""
    assert violations == []


def _then_violations_are(violations: list[Any], *expected: tuple[str, str]) -> None:
    """Then the violations are exactly "<key> <kind>" """
    assert sorted((v.key, v.kind) for v in violations) == sorted(expected)


def _then_every_violation_names_its_field(violations: list[Any]) -> None:
    """Then every violation message names its field"""
    assert violations, "Expected at least one violation"
    for violation in violations:
        assert violation.key in violation.message


def test_content_filling_its_contract_is_valid() -> None:
    """It accepts content that satisfies every rule of the contract.

    Scenario: Content filling its contract is valid
      Given the SDK validates inject content against a contract
      And a scan contract
      And inject content that fills the scan contract
      When the content is validated against the contract
      Then the content has no violation
    """
    validate = _given_contract_validator()
    contract = _given_scan_contract()
    content = _given_valid_content()
    violations = _when_validating(validate, contract, content)
    _then_content_is_valid(violations)


@pytest.mark.parametrize("value", [None, "", [], {}], ids=["absent", "''", "[]", "{}"])
def test_missing_mandatory_field_is_reported(value: Any) -> None:
    """It reports a mandatory field that is absent or empty, as the platform reads it.

    Scenario Outline: A missing mandatory field is reported
      Given the SDK validates inject content against a contract
      And a scan contract
      And inject content that fills the scan contract, with targets <value>
      When the content is validated against the contract
      Then the violations are exactly "targets mandatory"

      Examples:
        | value  |
        | absent |
        | ''     |
        | []     |
        | {}     |
    """
    validate = _given_contract_validator()
    contract = _given_scan_contract()
    content = _given_valid_content(targets=value)
    violations = _when_validating(validate, contract, content)
    _then_violations_are(violations, ("targets", "mandatory"))


def test_empty_mandatory_group_reports_every_member() -> None:
    """It reports every member of a mandatory group when none of them is set.

    Scenario: An empty mandatory group reports every member
      Given the SDK validates inject content against a contract
      And a scan contract
      And inject content that fills the scan contract
      And that content without "hosts"
      When the content is validated against the contract
      Then the violations are exactly "assets mandatory_group" and "hosts mandatory_group"
    """
    validate = _given_contract_validator()
    contract = _given_scan_contract()
    content = _given_content_without(_given_valid_content(), "hosts")
    violations = _when_validating(validate, contract, content)
    _then_violations_are(
        violations, ("assets", "mandatory_group"), ("hosts", "mandatory_group")
    )


def test_conditional_field_is_required_when_its_condition_is_met() -> None:
    """It requires a conditional field when its condition field holds a listed value.

    Scenario: A conditional field is required when its condition is met
      Given the SDK validates inject content against a contract
      And a scan contract
      And inject content that fills the scan contract, with scan_type "tcp"
      And that content without "ports"
      When the content is validated against the contract
      Then the violations are exactly "ports mandatory_condition"
    """
    validate = _given_contract_validator()
    contract = _given_scan_contract()
    content = _given_content_without(_given_valid_content(scan_type="tcp"), "ports")
    violations = _when_validating(validate, contract, content)
    _then_violations_are(violations, ("ports", "mandatory_condition"))


def test_conditional_field_is_optional_when_its_condition_is_not_met() -> None:
    """It leaves a conditional field optional when its condition value is not selected.

    Scenario: A conditional field is optional when its condition is not met
      Given the SDK validates inject content against a contract
      And a scan contract
      And inject content that fills the scan contract, with scan_type "udp"
      And that content without "ports"
      When the content is validated against the contract
      Then the content has no violation
    """
    validate = _given_contract_validator()
    contract = _given_scan_contract()
    content = _given_content_without(_given_valid_content(scan_type="udp"), "ports")
    violations = _when_validating(validate, contract, content)
    _then_content_is_valid(violations)


def test_select_value_outside_its_choices_is_reported() -> None:
    """It reports a select value that is not one of the field's choices.

    Scenario: A select value outside its choices is reported
      Given the SDK validates inject content against a contract
      And a scan contract
      And inject content that fills the scan contract, with scan_type "icmp"
      When the content is validated against the contract
      Then the violations are exactly "scan_type choice"
    """
    validate = _given_contract_validator()
    contract = _given_scan_contract()
    content = _given_valid_content(scan_type="icmp")
    violations = _when_validating(validate, contract, content)
    _then_violations_are(violations, ("scan_type", "choice"))


def test_several_values_for_a_single_value_field_are_reported() -> None:
    """It reports several values given to a field that takes a single one.

    Scenario: Several values for a single-value field are reported
      Given the SDK validates inject content against a contract
      And a scan contract
      And inject content that fills the scan contract, with report_format ["json", "xml"]
      When the content is validated against the contract
      Then the violations are exactly "report_format cardinality"
    """
    validate = _given_contract_validator()
    contract = _given_scan_contract()
    content = _given_valid_content(report_format=["json", "xml"])
    violations = _when_validating(validate, contract, content)
    _then_violations_are(violations, ("report_format", "cardinality"))


# ---- Constraints identified ----


def test_targets_given_outside_the_content_count_as_set() -> None:
    """It counts a target field as set when the inject's targets are given apart.

    Scenario: Targets given outside the content count as set
      Given the SDK validates inject content against a contract
      And a scan contract
      And inject content that fills the scan contract
      And that content without "hosts"
      When the content is validated against the contract, with "assets" given apart
      Then the content has no violation
    """
    validate = _given_contract_validator()
    contract = _given_scan_contract()
    content = _given_content_without(_given_valid_content(), "hosts")
    violations = _when_validating(validate, contract, content, ("assets",))
    _then_content_is_valid(violations)


def test_every_violation_names_its_field() -> None:
    """It gives each violation a message naming the field.

    Scenario: Every violation names its field
      Given the SDK validates inject content against a contract
      And a scan contract
      And inject content that fills the scan contract, with scan_type "icmp"
      And that content without "targets" and "hosts"
      When the content is validated against the contract
      Then every violation message names its field
    """
    validate = _given_contract_validator()
    contract = _given_scan_contract()
    content = _given_content_without(
        _given_valid_content(scan_type="icmp"), "targets", "hosts"
    )
    violations = _when_validating(validate, contract, content)
    _then_every_violation_names_its_field(violations)
