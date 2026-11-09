"""Tests for the legacy signature names.

Feature: Signature types instead of the legacy names
  Injectors used to send the execution signature field names (start_time,
  source_ipv4, target_hostname…) where collectors expect the signature types
  (start_date, source_ipv4_address, target_hostname_address…). The platform stores a
  signature under the name it arrives with, and its migration renamed the stored ones
  only once. The SDK now sends the signature types, and reads a legacy name as the
  type it stands for, with the same pairs as the platform's migration.
"""

from types import SimpleNamespace
from typing import Any

import pytest
import xtm_oaev_sdk as sdk
from pydantic import BaseModel, ValidationError

PAIRS = [
    ("start_time", "start_date"),
    ("end_time", "end_date"),
    ("source_ipv4", "source_ipv4_address"),
    ("source_ipv6", "source_ipv6_address"),
    ("target_ipv4", "target_ipv4_address"),
    ("target_ipv6", "target_ipv6_address"),
    ("target_hostname", "target_hostname_address"),
]


class _StoredSignature(BaseModel):
    type: sdk.SignatureTypes
    value: str


def _given_legacy_mapping() -> dict[str, str]:
    """Given the SDK publishes the legacy signature names"""
    mapping = getattr(sdk, "LEGACY_SIGNATURE_TYPES", None)
    assert (
        mapping is not None
    ), "Expected xtm_oaev_sdk.LEGACY_SIGNATURE_TYPES to exist on public surface"
    return mapping


def _given_execution_signature() -> sdk.ExecutionSignature:
    """Given an execution signature with a start, an end, a source IPv4 and a target
    hostname"""
    return sdk.ExecutionSignature(
        start_time="2026-11-05T10:00:00Z",
        end_time="2026-11-05T10:01:00Z",
        source_ipv4="10.0.0.9",
        target_hostname="lab-1",
    )


def _when_reading_a_stored_signature(name: str) -> Any:
    """When a signature stored under "<name>" is read"""
    try:
        return _StoredSignature(type=name, value="x").type
    except ValidationError as error:
        return error


def _when_building_the_payload(signature: sdk.ExecutionSignature) -> list[str]:
    """When the signature payload is built for one detection target"""
    payload = sdk.SignatureManager.build_payload(
        signature,
        [SimpleNamespace(agent_id="agent-1", asset_id="asset-1", asset_group_id=None)],
        ["DETECTION"],
    )
    values = payload["targets"][0]["signature_values"][0]["values"]
    return [value["signature_type"] for value in values]


def _then_it_reads_as(read: Any, signature_type: str) -> None:
    """Then it reads as the signature type "<signature_type>" """
    assert read == sdk.SignatureTypes(signature_type), f"Got {read!r}"


def _then_it_is_refused(read: Any) -> None:
    """Then it is refused"""
    assert isinstance(read, ValidationError), f"Expected a refusal, got {read!r}"


def _then_mapping_is(mapping: dict[str, str], pairs: list[tuple[str, str]]) -> None:
    """Then the legacy names map exactly to <pairs>"""
    assert mapping == dict(pairs)


def _then_payload_names_are(names: list[str], *expected: str) -> None:
    """Then the payload carries exactly the signature types "<expected>" """
    assert names == list(expected)


@pytest.mark.parametrize(("legacy", "signature_type"), PAIRS)
def test_a_legacy_name_reads_as_its_signature_type(
    legacy: str, signature_type: str
) -> None:
    """It reads a signature stored under a legacy name as its signature type.

    Scenario Outline: A legacy name reads as its signature type
      When a signature stored under "<legacy>" is read
      Then it reads as the signature type "<signature_type>"

      Examples:
        | legacy          | signature_type          |
        | start_time      | start_date              |
        | end_time        | end_date                |
        | source_ipv4     | source_ipv4_address     |
        | source_ipv6     | source_ipv6_address     |
        | target_ipv4     | target_ipv4_address     |
        | target_ipv6     | target_ipv6_address     |
        | target_hostname | target_hostname_address |
    """
    read = _when_reading_a_stored_signature(legacy)
    _then_it_reads_as(read, signature_type)


def test_the_legacy_names_are_published() -> None:
    """It publishes the legacy name of each signature type, as the platform migrates them.

    Scenario: The legacy names are published
      Given the SDK publishes the legacy signature names
      Then the legacy names map exactly to the seven pairs of the platform's migration
    """
    mapping = _given_legacy_mapping()
    _then_mapping_is(mapping, PAIRS)


def test_payloads_carry_the_signature_types() -> None:
    """It sends the signature types, never the legacy names.

    Scenario: Payloads carry the signature types
      Given an execution signature with a start, an end, a source IPv4 and a target hostname
      When the signature payload is built for one detection target
      Then the payload carries exactly the signature types "start_date", "end_date", "source_ipv4_address" and "target_hostname_address"
    """
    signature = _given_execution_signature()
    names = _when_building_the_payload(signature)
    _then_payload_names_are(
        names,
        "start_date",
        "end_date",
        "source_ipv4_address",
        "target_hostname_address",
    )


# ---- Constraints identified ----


def test_an_unknown_name_is_still_refused() -> None:
    """It still refuses a name that is neither a signature type nor a legacy name.

    Scenario: An unknown name is still refused
      When a signature stored under "ports_discovered" is read
      Then it is refused
    """
    read = _when_reading_a_stored_signature("ports_discovered")
    _then_it_is_refused(read)
