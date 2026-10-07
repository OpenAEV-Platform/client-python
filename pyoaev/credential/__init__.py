from .errors import (
    CredentialErrorCode,
    CredentialResolutionError,
    credential_error_code_from_http,
)
from .types import CredentialType


def build_single_referenced_credential_element(provider_name: str):
    from .utils import (
        build_single_referenced_credential_element as _build_single_referenced_credential_element,
    )

    return _build_single_referenced_credential_element(provider_name)


__all__ = [
    "CredentialErrorCode",
    "CredentialResolutionError",
    "CredentialType",
    "credential_error_code_from_http",
    "build_single_referenced_credential_element",
]
