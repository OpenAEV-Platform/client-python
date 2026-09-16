"""Helpers centralizing how injectors declare credential-reference fields.

Injectors can call ``build_single_referenced_credential_element`` instead of
re-implementing provider-to-credential-type mapping in each project. This keeps
contract generation consistent across the Python ecosystem and aligns the
serialized contract payload with the OpenAEV platform's expected values.
"""

from typing import Optional

from pyoaev.contracts.contract_config import ContractReferencedCredential
from pyoaev.credential.types import CredentialType


_PROVIDER_TO_CREDENTIAL_TYPE = {
    "aws": CredentialType.CLOUD_AWS,
    "eks": CredentialType.CLOUD_AWS,
    "azure": CredentialType.CLOUD_AZURE,
    "gcp": CredentialType.CLOUD_GCP,
}


def _resolve_credential_type(provider_name: str) -> Optional[CredentialType]:
    normalized_provider = provider_name.casefold()
    return _PROVIDER_TO_CREDENTIAL_TYPE.get(normalized_provider)


def build_single_referenced_credential_element(
    provider_name: str,
) -> ContractReferencedCredential:
    """Build a credential-reference field for a provider-specific contract
    with multiple value at False.

    This is the centralized entry point injectors should use when they need the
    OpenAEV inject form to ask for one referenced credential. The helper keeps
    provider-to-``CredentialType`` mapping consistent across injector projects.
    """

    return ContractReferencedCredential(
        credential_reference_type=_resolve_credential_type(provider_name)
    )
