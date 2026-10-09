from .attachment import (
    CredentialAttachment,
    get_credential_attachment,
    resolve_inject_credential,
)
from .errors import (
    CredentialErrorCode,
    CredentialResolutionError,
    InvalidResolvedSecretError,
    UnsupportedSecretTypeError,
    credential_error_code_from_http,
)
from .materializer import CredentialCleanupError, MaterializedCredential, materialize
from .resolved import (
    AwsAccessKeySecret,
    AwsAssumeRoleSecret,
    AzureManagedIdentitySecret,
    AzureServicePrincipalSecret,
    GcpOAuth2Secret,
    GcpServiceAccountSecret,
    HashSecret,
    ResolvedSecret,
    UsernamePasswordSecret,
    ensure_compatible,
    parse_resolved_secret,
)
from .types import AwsSourceIdentityType, CredentialType, HashAlgorithm, SecretType


def build_single_referenced_credential_element(provider_name: str):
    from .utils import (
        build_single_referenced_credential_element as _build_single_referenced_credential_element,
    )

    return _build_single_referenced_credential_element(provider_name)


__all__ = [
    "AwsAccessKeySecret",
    "AwsAssumeRoleSecret",
    "AwsSourceIdentityType",
    "AzureManagedIdentitySecret",
    "AzureServicePrincipalSecret",
    "CredentialAttachment",
    "CredentialCleanupError",
    "CredentialErrorCode",
    "CredentialResolutionError",
    "CredentialType",
    "GcpOAuth2Secret",
    "GcpServiceAccountSecret",
    "HashAlgorithm",
    "HashSecret",
    "InvalidResolvedSecretError",
    "MaterializedCredential",
    "ResolvedSecret",
    "SecretType",
    "UnsupportedSecretTypeError",
    "UsernamePasswordSecret",
    "credential_error_code_from_http",
    "build_single_referenced_credential_element",
    "ensure_compatible",
    "get_credential_attachment",
    "materialize",
    "parse_resolved_secret",
    "resolve_inject_credential",
]
