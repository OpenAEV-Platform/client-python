import unittest

from pyoaev.credential import CredentialType as PublicCredentialType
from pyoaev.credential.types import CredentialType


class CredentialTypeTest(unittest.TestCase):
    def test_every_value_matches_the_supported_platform_labels(self):
        expected_labels = {
            "IDENTITY",
            "CLOUD_AWS",
            "CLOUD_AZURE",
            "CLOUD_GCP",
        }
        actual_labels = {member.value for member in CredentialType}
        self.assertEqual(actual_labels, expected_labels)

    def test_identity_wire_label(self):
        self.assertEqual(CredentialType.IDENTITY.value, "IDENTITY")
        self.assertEqual(CredentialType.IDENTITY, "IDENTITY")

    def test_package_re_exports_credential_type(self):
        self.assertIs(PublicCredentialType, CredentialType)

    def test_aws_wire_label(self):
        self.assertEqual(CredentialType.CLOUD_AWS.value, "CLOUD_AWS")
        self.assertEqual(CredentialType.CLOUD_AWS, "CLOUD_AWS")


if __name__ == "__main__":
    unittest.main()



