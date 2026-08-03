import json
import unittest

from pyoaev import utils
from pyoaev.contracts.contract_config import ContractText, PrimitiveType


def _serialize(field):
    return json.loads(json.dumps(field, cls=utils.EnhancedJSONEncoder))


class ContractElementArgumentTypeTest(unittest.TestCase):
    def test_defaults_to_none_when_not_declared(self):
        """Existing contracts that never pass argumentType keep working
        unchanged — the platform normalizes a null value to PrimitiveType.Text
        on its own, so this is not a breaking change for anything already
        deployed."""
        untyped = ContractText(key="uri", label="URL")
        self.assertIsNone(untyped.argumentType)
        self.assertIsNone(_serialize(untyped)["argumentType"])

    def test_explicit_argument_type_round_trips(self):
        typed = ContractText(
            key="basicUser", label="Username", argumentType=PrimitiveType.Username
        )
        self.assertEqual(typed.argumentType, PrimitiveType.Username)
        self.assertEqual(_serialize(typed)["argumentType"], "username")

    def test_argument_type_is_independent_of_widget_type(self):
        """A field's rendering (ContractFieldType, on `type`) and its chaining
        semantics (PrimitiveType, on `argumentType`) are separate axes."""
        typed = ContractText(
            key="basicUser", label="Username", argumentType=PrimitiveType.Username
        )
        serialized = _serialize(typed)
        self.assertEqual(serialized["type"], "text")
        self.assertEqual(serialized["argumentType"], "username")


if __name__ == "__main__":
    unittest.main()
