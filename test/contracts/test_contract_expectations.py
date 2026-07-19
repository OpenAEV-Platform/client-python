import json
import unittest

from pyoaev import utils
from pyoaev.contracts.contract_config import (
    ContractCardinality,
    ContractExpectations,
    Expectation,
    ExpectationType,
)


def _expectation(expectation_type, name, is_predefined):
    return Expectation(
        expectation_type=expectation_type,
        expectation_name=name,
        expectation_description="",
        expectation_score=100,
        expectation_expectation_group=False,
        expectation_is_predefined=is_predefined,
    )


def _serialize(field):
    return json.loads(json.dumps(field, cls=utils.EnhancedJSONEncoder))


class TestContractExpectations(unittest.TestCase):
    def test_predefined_derived_from_flag(self):
        """
        The platform pre-fills expectations from the field-level
        ``predefinedExpectations`` array, so it must be populated from the
        expectations flagged ``expectation_is_predefined=True``.
        """
        field = ContractExpectations(
            key="expectations",
            label="Expectations",
            cardinality=ContractCardinality.Multiple,
            availableExpectations=[
                _expectation(ExpectationType.detection, "Detection", True),
                _expectation(ExpectationType.prevention, "Prevention", True),
                _expectation(ExpectationType.vulnerability, "Not vulnerable", False),
            ],
        )

        data = _serialize(field)

        self.assertEqual("expectation", data["type"])
        self.assertEqual(
            ["DETECTION", "PREVENTION", "VULNERABILITY"],
            [e["expectation_type"] for e in data["availableExpectations"]],
        )
        # Only the flagged ones are pre-filled.
        self.assertEqual(
            ["DETECTION", "PREVENTION"],
            [e["expectation_type"] for e in data["predefinedExpectations"]],
        )

    def test_explicit_predefined_is_kept(self):
        detection = _expectation(ExpectationType.detection, "Detection", False)
        field = ContractExpectations(
            key="expectations",
            label="Expectations",
            availableExpectations=[detection],
            predefinedExpectations=[detection],
        )

        data = _serialize(field)

        self.assertEqual(
            ["DETECTION"],
            [e["expectation_type"] for e in data["predefinedExpectations"]],
        )

    def test_explicit_empty_list_overrides_flags(self):
        """
        An explicit empty ``predefinedExpectations`` list must suppress the
        derivation even when some available expectations carry the predefined
        flag, while still serializing as an (empty) array.
        """
        field = ContractExpectations(
            key="expectations",
            label="Expectations",
            availableExpectations=[
                _expectation(ExpectationType.detection, "Detection", True),
            ],
            predefinedExpectations=[],
        )

        data = _serialize(field)

        self.assertEqual([], data["predefinedExpectations"])

    def test_no_flag_yields_no_predefined(self):
        field = ContractExpectations(
            key="expectations",
            label="Expectations",
            availableExpectations=[
                _expectation(ExpectationType.vulnerability, "Not vulnerable", False),
            ],
        )

        data = _serialize(field)

        self.assertEqual([], data["predefinedExpectations"])


if __name__ == "__main__":
    unittest.main()
