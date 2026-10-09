"""Typed secrets resolved from a credential reference at execution time.

``parse_resolved_secret`` turns the payload returned by the platform resolution
endpoint into one frozen dataclass per ``SecretType``. Secret material is
excluded from ``repr``/``str`` so a resolved secret can never end up in a log
line by accident.

``ensure_compatible`` is the injector-side check that the resolved secret
satisfies the credential type declared on the contract field.
"""

import base64
from dataclasses import MISSING, dataclass, field, fields
from typing import Any, ClassVar, Dict, Optional, Type, TypeVar, Union

from pyoaev.credential.errors import (
    CredentialErrorCode,
    CredentialResolutionError,
    InvalidResolvedSecretError,
    UnsupportedSecretTypeError,
)
from pyoaev.credential.types import (
    AwsSourceIdentityType,
    CredentialType,
    HashAlgorithm,
    SecretType,
)

_SECRET_TYPE_TO_CREDENTIAL_TYPE = {
    SecretType.USERNAME_PASSWORD: CredentialType.IDENTITY,
    SecretType.HASH: CredentialType.IDENTITY,
    SecretType.AWS_ACCESS_KEY: CredentialType.CLOUD_AWS,
    SecretType.AWS_ASSUME_ROLE: CredentialType.CLOUD_AWS,
    SecretType.AZURE_SERVICE_PRINCIPAL: CredentialType.CLOUD_AZURE,
    SecretType.AZURE_MANAGED_IDENTITY: CredentialType.CLOUD_AZURE,
    SecretType.GCP_SERVICE_ACCOUNT: CredentialType.CLOUD_GCP,
    SecretType.GCP_OAUTH2: CredentialType.CLOUD_GCP,
}


def _secret(**kwargs: Any) -> Any:
    """A field holding secret material: hidden from ``repr``/``str``."""
    return field(repr=False, **kwargs)


def _parsed_with(parser, **kwargs: Any) -> Any:
    """A field whose raw string value is converted by ``parser``."""
    return field(metadata={"parser": parser}, **kwargs)


def _decode_base64(value: str) -> bytes:
    return base64.b64decode(value, validate=True)


@dataclass(frozen=True)
class ResolvedSecret:
    secret_type: ClassVar[SecretType]

    @property
    def credential_type(self) -> CredentialType:
        return _SECRET_TYPE_TO_CREDENTIAL_TYPE[self.secret_type]


@dataclass(frozen=True)
class UsernamePasswordSecret(ResolvedSecret):
    secret_type: ClassVar[SecretType] = SecretType.USERNAME_PASSWORD

    username: str
    password: str = _secret()


@dataclass(frozen=True)
class HashSecret(ResolvedSecret):
    secret_type: ClassVar[SecretType] = SecretType.HASH

    hash_algorithm: HashAlgorithm = _parsed_with(HashAlgorithm)
    hash: str = _secret()


@dataclass(frozen=True)
class AwsAccessKeySecret(ResolvedSecret):
    secret_type: ClassVar[SecretType] = SecretType.AWS_ACCESS_KEY

    aws_access_key_id: str = _secret()
    aws_secret_access_key: str = _secret()
    aws_default_region: Optional[str] = None
    aws_session_token: Optional[str] = _secret(default=None)


@dataclass(frozen=True)
class AwsAssumeRoleSecret(ResolvedSecret):
    secret_type: ClassVar[SecretType] = SecretType.AWS_ASSUME_ROLE

    aws_role_arn: str
    aws_source_identity_type: AwsSourceIdentityType = _parsed_with(
        AwsSourceIdentityType
    )
    aws_default_region: Optional[str] = None
    aws_external_id: Optional[str] = _secret(default=None)
    aws_source_profile_access_key_id: Optional[str] = _secret(default=None)
    aws_source_profile_secret_access_key: Optional[str] = _secret(default=None)

    def __post_init__(self) -> None:
        # A static source identity cannot assume the role without its keys.
        if self.aws_source_identity_type == AwsSourceIdentityType.STATIC_ACCESS_KEY:
            if not (
                self.aws_source_profile_access_key_id
                and self.aws_source_profile_secret_access_key
            ):
                raise ValueError("Missing source profile keys")


@dataclass(frozen=True)
class AzureServicePrincipalSecret(ResolvedSecret):
    secret_type: ClassVar[SecretType] = SecretType.AZURE_SERVICE_PRINCIPAL

    azure_environment: str
    azure_client_id: str
    azure_client_secret: str = _secret()
    azure_tenant_id: str
    azure_subscription_id: Optional[str] = None


@dataclass(frozen=True)
class AzureManagedIdentitySecret(ResolvedSecret):
    secret_type: ClassVar[SecretType] = SecretType.AZURE_MANAGED_IDENTITY

    azure_environment: str
    azure_client_id: Optional[str] = None
    azure_subscription_id: Optional[str] = None


@dataclass(frozen=True)
class GcpServiceAccountSecret(ResolvedSecret):
    secret_type: ClassVar[SecretType] = SecretType.GCP_SERVICE_ACCOUNT

    gcp_scope: str
    # Java ``byte[]``, sent base64 encoded by the platform.
    gcp_private_key_json: bytes = _parsed_with(_decode_base64, repr=False)
    gcp_project_id: Optional[str] = None


@dataclass(frozen=True)
class GcpOAuth2Secret(ResolvedSecret):
    secret_type: ClassVar[SecretType] = SecretType.GCP_OAUTH2

    gcp_scope: str
    gcp_oauth_client_id: str
    gcp_oauth_client_secret: str = _secret()
    gcp_oauth_refresh_token: str = _secret()
    gcp_project_id: Optional[str] = None


_RESOLVED_SECRET_CLASSES: Dict[SecretType, Type[ResolvedSecret]] = {
    cls.secret_type: cls
    for cls in (
        UsernamePasswordSecret,
        HashSecret,
        AwsAccessKeySecret,
        AwsAssumeRoleSecret,
        AzureServicePrincipalSecret,
        AzureManagedIdentitySecret,
        GcpServiceAccountSecret,
        GcpOAuth2Secret,
    )
}

_R = TypeVar("_R", bound=ResolvedSecret)


def _build(cls: Type[_R], value: Dict[str, Any]) -> _R:
    kwargs: Dict[str, Any] = {}
    for secret_field in fields(cls):
        raw = value.get(secret_field.name)
        # The platform omits null fields; an empty string is as good as absent.
        if raw is None or raw == "":
            if secret_field.default is MISSING:
                raise ValueError(f"Missing required field {secret_field.name}")
            continue
        if not isinstance(raw, str):
            raise ValueError(f"Unexpected value type for {secret_field.name}")
        parser = secret_field.metadata.get("parser")
        kwargs[secret_field.name] = parser(raw) if parser else raw
    return cls(**kwargs)


def parse_resolved_secret(
    payload: Any, reference: Optional[str] = None
) -> ResolvedSecret:
    """Build the typed secret from a resolution endpoint payload.

    Raises:
        UnsupportedSecretTypeError: the ``type`` is not a known ``SecretType``.
        InvalidResolvedSecretError: the payload does not match its ``type``
            (missing required key, wrong value type, invalid base64...).
    """
    if not isinstance(payload, dict):
        raise InvalidResolvedSecretError(reference)
    raw_type = payload.get("type")
    try:
        secret_type = SecretType(raw_type)
    except ValueError:
        raise UnsupportedSecretTypeError(
            raw_type if isinstance(raw_type, str) else None, reference
        ) from None

    value = payload.get("value")
    if not isinstance(value, dict):
        raise InvalidResolvedSecretError(reference)
    error: Optional[CredentialResolutionError] = None
    # Raised outside of the except block so that the original error, which may
    # quote a secret value, is not chained to it.
    try:
        return _build(_RESOLVED_SECRET_CLASSES[secret_type], value)
    except (ValueError, TypeError):
        error = InvalidResolvedSecretError(reference)
    raise error


def ensure_compatible(
    resolved: _R,
    expected: Union[CredentialType, str],
    reference: Optional[str] = None,
) -> _R:
    """Check that ``resolved`` satisfies the credential type of the contract.

    ``expected`` is either a ``CredentialType`` or a provider name (``aws``,
    ``eks``, ``azure``, ``gcp``), mapped with the same table as the one used to
    declare the contract field.

    Raises:
        CredentialResolutionError: ``CREDENTIAL_INCOMPATIBLE`` on mismatch.
        ValueError: ``expected`` is a provider name with no credential type.
    """
    # Imported here: utils depends on contracts, which import this package.
    from pyoaev.credential.utils import _resolve_credential_type

    if isinstance(expected, CredentialType):
        expected_type = expected
    else:
        expected_type = _resolve_credential_type(expected)
        if expected_type is None:
            raise ValueError(f"No credential type is mapped to provider {expected!r}")

    if resolved.credential_type != expected_type:
        raise CredentialResolutionError(
            CredentialErrorCode.CREDENTIAL_INCOMPATIBLE,
            reference,
            expected_type=expected_type,
        )
    return resolved


__all__ = [
    "AwsAccessKeySecret",
    "AwsAssumeRoleSecret",
    "AzureManagedIdentitySecret",
    "AzureServicePrincipalSecret",
    "GcpOAuth2Secret",
    "GcpServiceAccountSecret",
    "HashSecret",
    "ResolvedSecret",
    "UsernamePasswordSecret",
    "ensure_compatible",
    "parse_resolved_secret",
]
