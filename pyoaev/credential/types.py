"""Credential reference types shared with the OpenAEV platform.

This enum is the Python mirror of the OpenAEV backend credential-type enum
used by credential secret references. Values must stay label-for-label in sync
with the platform so contracts can declare credential references without any
translation layer.
"""

from enum import Enum


class CredentialType(str, Enum):
    IDENTITY = "IDENTITY"
    CLOUD_AWS = "CLOUD_AWS"
    CLOUD_AZURE = "CLOUD_AZURE"
    CLOUD_GCP = "CLOUD_GCP"


class SecretType(str, Enum):
    """Mirror of the platform ``Secret.SECRET_TYPE`` enum, label for label."""

    USERNAME_PASSWORD = "USERNAME_PASSWORD"
    HASH = "HASH"
    AWS_ACCESS_KEY = "AWS_ACCESS_KEY"
    AWS_ASSUME_ROLE = "AWS_ASSUME_ROLE"
    AZURE_SERVICE_PRINCIPAL = "AZURE_SERVICE_PRINCIPAL"
    AZURE_MANAGED_IDENTITY = "AZURE_MANAGED_IDENTITY"
    GCP_SERVICE_ACCOUNT = "GCP_SERVICE_ACCOUNT"
    GCP_OAUTH2 = "GCP_OAUTH2"


class AwsSourceIdentityType(str, Enum):
    """Mirror of the platform ``AwsAssumeRoleSecret.AWS_SOURCE_IDENTITY_TYPE`` enum."""

    STATIC_ACCESS_KEY = "STATIC_ACCESS_KEY"
    INSTANCE_DEFAULT = "INSTANCE_DEFAULT"


class HashAlgorithm(str, Enum):
    """Mirror of the platform ``HashSecret.HASH_ALGORITHM`` enum."""

    SHA = "SHA"
    NTLM = "NTLM"
