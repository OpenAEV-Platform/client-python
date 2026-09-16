import json
import unittest

from pyoaev import utils
from pyoaev.contracts.contract_config import (
    ContractFieldKey,
    ContractFieldType,
    ContractReferencedCredential,
)
from pyoaev.credential.types import CredentialType


def _serialize(field):
    return json.loads(json.dumps(field, cls=utils.EnhancedJSONEncoder))


class ContractReferencedCredentialTest(unittest.TestCase):
    def test_defaults_match_platform_contract_expectations(self):
        field = ContractReferencedCredential()
        serialized = _serialize(field)

        self.assertEqual(field.key, ContractFieldKey.CredentialReference.value)
        self.assertEqual(field.label, "Select a credential reference")
        self.assertTrue(field.mandatory)
        self.assertFalse(field.multiple)
        self.assertIsNone(field.credential_reference_type)
        self.assertEqual(field.type, ContractFieldType.CredentialReference.value)
        self.assertEqual(serialized["key"], "credential_reference")
        self.assertEqual(serialized["type"], "credential-reference")
        self.assertEqual(serialized["label"], "Select a credential reference")
        self.assertTrue(serialized["mandatory"])
        self.assertFalse(serialized["multiple"])
        self.assertIsNone(serialized["credential_reference_type"])

    def test_explicit_credential_type_serializes_to_platform_label(self):
        field = ContractReferencedCredential(
            credential_reference_type=CredentialType.CLOUD_AZURE
        )

        self.assertEqual(field.credential_reference_type, CredentialType.CLOUD_AZURE)
        self.assertEqual(
            _serialize(field)["credential_reference_type"], "CLOUD_AZURE"
        )

    def test_identity_credential_type_serializes_to_platform_label(self):
        field = ContractReferencedCredential(
            credential_reference_type=CredentialType.IDENTITY
        )

        self.assertEqual(field.credential_reference_type, CredentialType.IDENTITY)
        self.assertEqual(_serialize(field)["credential_reference_type"], "IDENTITY")


if __name__ == "__main__":
    unittest.main()


