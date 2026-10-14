"""Credential-reference fields: provider-to-credential-type mapping.

Injectors call ``build_single_referenced_credential_element`` instead of
re-implementing the provider-to-credential-type mapping in each project. This
keeps contract generation consistent across the Python ecosystem and aligns the
serialized contract payload with the OpenAEV platform's expected values.
"""

from typing import Optional

from xtm_oaev_sdk.seam.contracts import ContractReferencedCredential, CredentialType

__all__ = ["CredentialReferences"]

_PROVIDER_TO_CREDENTIAL_TYPE = {
    "aws": CredentialType.CLOUD_AWS,
    "eks": CredentialType.CLOUD_AWS,
    "azure": CredentialType.CLOUD_AZURE,
    "gcp": CredentialType.CLOUD_GCP,
}


class CredentialReferences:
    """Implements ``ContractCredentialsPort``."""

    def build_single_referenced_credential_element(
        self, provider_name: str
    ) -> ContractReferencedCredential:
        return ContractReferencedCredential(
            credential_reference_type=self._resolve_credential_type(provider_name),
            multiple=False,
        )

    @staticmethod
    def _resolve_credential_type(provider_name: str) -> Optional[CredentialType]:
        normalized_provider = provider_name.casefold()
        return _PROVIDER_TO_CREDENTIAL_TYPE.get(normalized_provider)
