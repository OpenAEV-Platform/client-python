import unittest
from types import SimpleNamespace
from uuid import uuid4

from pyoaev.apis.inject_expectation.model import (
    DetectionExpectation,
    PreventionExpectation,
)
from pyoaev.signatures.models import (
    ExecutionSignature,
    ExtraSignatureData,
    SignaturePayload,
)
from pyoaev.signatures.signature_manager import SignatureManager
from pyoaev.signatures.types import SignatureTypes

TARGET = SimpleNamespace(agent_id="agent-1", asset_id="asset-1", asset_group_id=None)
CANONICAL_TYPES = {signature_type.value for signature_type in SignatureTypes}


def _network_signature(**fields):
    return ExecutionSignature(
        start_time="2026-10-16T08:00:00Z",
        end_time="2026-10-16T08:05:00Z",
        source_ipv4="10.0.0.5",
        source_ipv6="fd00::5",
        **fields,
    )


def _values(payload, target_index=0, group_index=0):
    group = payload["targets"][target_index]["signature_values"][group_index]
    return {
        value["signature_type"]: value["signature_value"] for value in group["values"]
    }


def _as_stored_by_platform(payload):
    """Signatures as the platform stores them (SignatureOutputProcessor): the type
    as is, and only non-empty scalar values, as text."""
    stored = []
    for target in payload["targets"]:
        for group in target["signature_values"]:
            for value in group["values"]:
                signature_value = value["signature_value"]
                if isinstance(signature_value, (list, dict)) or signature_value in (
                    None,
                    "",
                ):
                    continue
                stored.append(
                    {
                        "type": value["signature_type"],
                        "value": str(signature_value),
                    }
                )
    return stored


class TestBuildPayloadSignatureTypes(unittest.TestCase):
    def test_network_ipv4_signature_uses_canonical_signature_types(self):
        payload = SignatureManager.build_payload(
            _network_signature(target_ipv4="192.0.2.11"), [TARGET], ["DETECTION"]
        )

        self.assertEqual(
            {
                "start_date": "2026-10-16T08:00:00Z",
                "end_date": "2026-10-16T08:05:00Z",
                "source_ipv4_address": "10.0.0.5",
                "source_ipv6_address": "fd00::5",
                "target_ipv4_address": "192.0.2.11",
            },
            _values(payload),
        )

    def test_network_ipv6_and_hostname_targets_use_canonical_signature_types(self):
        payload = SignatureManager.build_payload(
            [
                _network_signature(target_ipv6="2001:db8::11"),
                _network_signature(target_hostname="web.example.com"),
            ],
            [TARGET, TARGET],
            ["DETECTION"],
        )

        self.assertEqual("2001:db8::11", _values(payload, 0)["target_ipv6_address"])
        self.assertEqual(
            "web.example.com", _values(payload, 1)["target_hostname_address"]
        )

    def test_cloud_signature_keeps_cloud_types_and_renames_dates(self):
        signature = ExecutionSignature(
            start_time="2026-10-16T08:00:00Z",
            cloud_provider="aws",
            cloud_account_id="123456789012",
            cloud_region="eu-west-3",
            target_service="s3",
        )

        payload = SignatureManager.build_payload(signature, [TARGET], ["PREVENTION"])

        self.assertEqual(
            {
                "start_date": "2026-10-16T08:00:00Z",
                "cloud_provider": "aws",
                "cloud_account_id": "123456789012",
                "cloud_region": "eu-west-3",
                "target_service": "s3",
            },
            _values(payload),
        )

    def test_every_signature_type_sent_is_a_signature_types_value(self):
        signature = _network_signature(target_ipv4="192.0.2.11")
        signature.partial_results = ["22/tcp open"]
        extra = ExtraSignatureData(
            detection={"ports_discovered": [22, 80], "process_name": "nmap"},
            prevention={"services_discovered": [{"port": 22}]},
            vulnerability={"cves_tested": [], "cves_found_vulnerable": []},
        )

        payload = SignatureManager.build_payload(
            signature, [TARGET], ["DETECTION", "PREVENTION", "VULNERABILITY"], extra
        )

        for group in payload["targets"][0]["signature_values"]:
            for value in group["values"]:
                self.assertIn(value["signature_type"], CANONICAL_TYPES)


class TestBuildPayloadExtraSignatures(unittest.TestCase):
    def test_unknown_extra_keys_are_left_out_and_logged(self):
        extra = ExtraSignatureData(
            detection={"ports_discovered": [22, 80], "services_discovered": []}
        )

        with self.assertLogs(
            "pyoaev.signatures.signature_manager", level="WARNING"
        ) as logs:
            payload = SignatureManager.build_payload(
                _network_signature(target_ipv4="192.0.2.11"),
                [TARGET],
                ["DETECTION"],
                extra,
            )

        self.assertNotIn("ports_discovered", _values(payload))
        self.assertNotIn("services_discovered", _values(payload))
        self.assertEqual(1, len(logs.records))
        self.assertIn("ports_discovered, services_discovered", logs.output[0])

    def test_extra_keys_that_are_signature_types_are_sent(self):
        extra = ExtraSignatureData(
            detection={"process_name": "nmap", "command_line": "nmap -sV 192.0.2.11"}
        )

        payload = SignatureManager.build_payload(
            _network_signature(target_ipv4="192.0.2.11"), [TARGET], ["DETECTION"], extra
        )

        self.assertEqual("nmap", _values(payload)["process_name"])
        self.assertEqual("nmap -sV 192.0.2.11", _values(payload)["command_line"])

    def test_extra_keys_named_like_execution_signature_fields_are_renamed(self):
        extra = ExtraSignatureData(detection={"target_hostname": "web.example.com"})

        payload = SignatureManager.build_payload(
            _network_signature(target_ipv4="192.0.2.11"), [TARGET], ["DETECTION"], extra
        )

        self.assertEqual("web.example.com", _values(payload)["target_hostname_address"])
        self.assertNotIn("target_hostname", _values(payload))

    def test_extra_signature_overrides_the_execution_signature_value(self):
        extra = ExtraSignatureData(detection={"end_date": "2026-10-16T09:00:00Z"})

        payload = SignatureManager.build_payload(
            _network_signature(target_ipv4="192.0.2.11"), [TARGET], ["DETECTION"], extra
        )

        group = payload["targets"][0]["signature_values"][0]
        end_dates = [v for v in group["values"] if v["signature_type"] == "end_date"]
        self.assertEqual(
            [{"signature_type": "end_date", "signature_value": "2026-10-16T09:00:00Z"}],
            end_dates,
        )

    def test_extras_only_apply_to_their_expectation_type(self):
        extra = ExtraSignatureData(detection={"process_name": "nmap"})

        payload = SignatureManager.build_payload(
            _network_signature(target_ipv4="192.0.2.11"),
            [TARGET],
            ["DETECTION", "PREVENTION"],
            extra,
        )

        self.assertIn("process_name", _values(payload, group_index=0))
        self.assertNotIn("process_name", _values(payload, group_index=1))

    def test_list_dict_and_none_values_are_left_out(self):
        signature = _network_signature(target_ipv4="192.0.2.11")
        signature.partial_results = ["22/tcp open"]
        extra = ExtraSignatureData(
            detection={
                "url_hash": ["aaa", "bbb"],
                "file_hash": {"sha256": "ccc"},
                "file_name": None,
            }
        )

        with self.assertLogs(
            "pyoaev.signatures.signature_manager", level="WARNING"
        ) as logs:
            payload = SignatureManager.build_payload(
                signature, [TARGET], ["DETECTION"], extra
            )

        for key in ("url_hash", "file_hash", "file_name", "partial_results"):
            self.assertNotIn(key, _values(payload))
        self.assertIn("file_hash, file_name, partial_results, url_hash", logs.output[0])

    def test_nothing_is_logged_when_every_signature_is_sent(self):
        with self.assertNoLogs("pyoaev.signatures.signature_manager", level="WARNING"):
            SignatureManager.build_payload(
                _network_signature(target_ipv4="192.0.2.11"),
                [TARGET],
                ["DETECTION", "PREVENTION"],
            )


class TestBuildPayloadLoggingExpectation(unittest.TestCase):
    """Injectors pass every expectation type of the inject: LOGGING must get its
    own group and never make the Detection and Prevention signatures fail."""

    def test_logging_gets_a_group_with_the_same_base_signatures(self):
        payload = SignatureManager.build_payload(
            _network_signature(target_ipv4="192.0.2.11"),
            [TARGET],
            ["DETECTION", "PREVENTION", "LOGGING"],
        )

        groups = payload["targets"][0]["signature_values"]
        self.assertEqual(
            ["DETECTION", "PREVENTION", "LOGGING"],
            [group["expectation_type"] for group in groups],
        )
        self.assertEqual(
            _values(payload, group_index=0), _values(payload, group_index=2)
        )
        self.assertEqual(
            _values(payload, group_index=1), _values(payload, group_index=2)
        )

    def test_logging_extras_only_apply_to_the_logging_group(self):
        extra = ExtraSignatureData(logging={"process_name": "nmap"})

        payload = SignatureManager.build_payload(
            _network_signature(target_ipv4="192.0.2.11"),
            [TARGET],
            ["DETECTION", "LOGGING"],
            extra,
        )

        self.assertNotIn("process_name", _values(payload, group_index=0))
        self.assertEqual("nmap", _values(payload, group_index=1)["process_name"])


class TestExtraSignatureDataGetExtra(unittest.TestCase):
    def test_logging_without_extras_is_empty(self):
        extra = ExtraSignatureData(detection={"process_name": "nmap"})

        self.assertEqual({}, extra.get_extra("LOGGING"))

    def test_unknown_type_is_empty_instead_of_raising(self):
        extra = ExtraSignatureData(detection={"process_name": "nmap"})

        self.assertEqual({}, extra.get_extra("FOO"))

    def test_known_types_are_case_insensitive(self):
        extra = ExtraSignatureData(logging={"process_name": "nmap"})

        self.assertEqual({"process_name": "nmap"}, extra.get_extra("logging"))
        self.assertEqual({"process_name": "nmap"}, extra.get_extra("LOGGING"))


class TestBuildPayloadIsParsedByCollectors(unittest.TestCase):
    """Regression for client-python#352: a collector must be able to parse the
    expectation signatures the platform stores from this payload."""

    def test_signatures_stored_from_the_payload_build_collector_expectations(self):
        signatures = [
            _network_signature(target_ipv4="192.0.2.11"),
            _network_signature(target_hostname="web.example.com"),
        ]
        # Same extra signatures as the Nmap injector
        extra_data = {
            "ports_discovered": [22, 80],
            "services_discovered": [{"port": 22, "service": "ssh"}],
        }
        extra = ExtraSignatureData(detection=extra_data, prevention=extra_data)

        payload = SignatureManager.build_payload(
            signatures, [TARGET, TARGET], ["DETECTION", "PREVENTION"], extra
        )
        SignaturePayload(**payload)
        stored = _as_stored_by_platform(payload)

        for model_cls in (DetectionExpectation, PreventionExpectation):
            expectation = model_cls(
                inject_expectation_id=uuid4(),
                inject_expectation_signatures=stored,
                api_client=None,
            )
            self.assertEqual(
                len(stored), len(expectation.inject_expectation_signatures)
            )
        self.assertIn(
            SignatureTypes.SIG_TYPE_TARGET_IPV4_ADDRESS,
            {signature.type for signature in expectation.inject_expectation_signatures},
        )


if __name__ == "__main__":
    unittest.main()
