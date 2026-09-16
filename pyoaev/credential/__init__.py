from .types import CredentialType


def build_single_referenced_credential_element(provider_name: str):
    from .utils import (
        build_single_referenced_credential_element as _build_single_referenced_credential_element,
    )

    return _build_single_referenced_credential_element(provider_name)

__all__ = [
    "CredentialType",
    "build_single_referenced_credential_element",
]


