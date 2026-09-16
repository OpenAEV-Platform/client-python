import json
import unittest

from pyoaev import utils
from pyoaev.contracts.contract_config import ContractReferencedCredential
from pyoaev.credential import (
    build_single_referenced_credential_element as public_build_single_referenced_credential_element,
)
from pyoaev.credential.types import CredentialType
from pyoaev.credential.utils import build_single_referenced_credential_element


def _serialize(field):
    return json.loads(json.dumps(field, cls=utils.EnhancedJSONEncoder))


class CredentialUtilsTest(unittest.TestCase):
    def test_aws_provider_maps_to_aws_credential_reference(self):
        field = build_single_referenced_credential_element("aws")

        self.assertIsInstance(field, ContractReferencedCredential)
        self.assertEqual(field.credential_reference_type, CredentialType.CLOUD_AWS)

    def test_eks_provider_maps_to_aws_credential_reference(self):
        field = build_single_referenced_credential_element("eks")

        self.assertEqual(field.credential_reference_type, CredentialType.CLOUD_AWS)

    def test_azure_provider_maps_to_azure_credential_reference(self):
        field = build_single_referenced_credential_element("azure")

        self.assertEqual(field.credential_reference_type, CredentialType.CLOUD_AZURE)

    def test_gcp_provider_maps_to_gcp_credential_reference(self):
        field = build_single_referenced_credential_element("gcp")

        self.assertEqual(field.credential_reference_type, CredentialType.CLOUD_GCP)

    def test_provider_mapping_is_case_insensitive(self):
        field = build_single_referenced_credential_element("AWS")

        self.assertEqual(field.credential_reference_type, CredentialType.CLOUD_AWS)

    def test_package_public_helper_builds_the_same_field(self):
        field = public_build_single_referenced_credential_element("azure")

        self.assertIsInstance(field, ContractReferencedCredential)
        self.assertEqual(field.credential_reference_type, CredentialType.CLOUD_AZURE)
        self.assertEqual(_serialize(field)["credential_reference_type"], "CLOUD_AZURE")

    def test_unknown_provider_leaves_credential_type_empty(self):
        field = build_single_referenced_credential_element("openstack")

        self.assertIsNone(field.credential_reference_type)
        self.assertIsNone(_serialize(field)["credential_reference_type"])


if __name__ == "__main__":
    unittest.main()


