"""Turn a resolved secret into the environment and files a cloud SDK expects.

``materialize`` is a context manager: the files it writes live in a private,
per-run temporary directory (``0700``, each file ``0600`` on POSIX) which is
removed on exit, even when the execution fails. Nothing is written to ``~/.aws``
or any other shared location.
"""

import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional

from pyoaev.credential.errors import (
    InvalidResolvedSecretError,
    UnsupportedSecretTypeError,
)
from pyoaev.credential.resolved import (
    AwsAccessKeySecret,
    AwsAssumeRoleSecret,
    AzureManagedIdentitySecret,
    AzureServicePrincipalSecret,
    GcpOAuth2Secret,
    GcpServiceAccountSecret,
    ResolvedSecret,
)
from pyoaev.credential.types import AwsSourceIdentityType, SecretType

AWS_SOURCE_PROFILE = "srt-source"
AWS_TARGET_PROFILE = "srt-target"

# Scheme and trailing slash are required by the Go SDK (stratus) and accepted
# by the Python SDK.
AZURE_AUTHORITY_HOSTS = {
    "AzureCloud": "https://login.microsoftonline.com/",
    "AzureChinaCloud": "https://login.chinacloudapi.cn/",
    "AzureUSGovernment": "https://login.microsoftonline.us/",
}


class CredentialCleanupError(RuntimeError):
    """Temporary credential files could not be removed."""

    def __init__(self) -> None:
        super().__init__("temporary credential cleanup failed")


@dataclass(frozen=True)
class MaterializedCredential:
    """Environment and files to apply to the process using the credential.

    ``secret_type`` lets callers pick the authentication mode (for example a
    CLI flag) without re-reading the secret.
    """

    secret_type: SecretType
    env: Dict[str, str] = field(repr=False)
    files: List[Path]


class _Workspace:
    """Private per-run directory, only created when a file must be written."""

    def __init__(self, temporary_root: Optional[Path]) -> None:
        self._temporary_root = temporary_root
        self.directory: Optional[Path] = None
        self.files: List[Path] = []

    def write(self, content: bytes, *, prefix: str, suffix: str = "") -> Path:
        if self.directory is None:
            # mkdtemp creates the directory 0700 on POSIX.
            self.directory = Path(
                tempfile.mkdtemp(prefix="openaev-credential-", dir=self._temporary_root)
            )
        # mkstemp creates the file 0600 on POSIX.
        descriptor, name = tempfile.mkstemp(
            prefix=prefix, suffix=suffix, dir=self.directory
        )
        path = Path(name)
        self.files.append(path)
        try:
            credential_file = os.fdopen(descriptor, "wb")
        except BaseException:
            # An open descriptor would prevent the removal on Windows.
            os.close(descriptor)
            raise
        with credential_file:
            credential_file.write(content)
        return path

    def cleanup(self) -> None:
        if self.directory is None:
            return
        shutil.rmtree(self.directory, ignore_errors=True)
        if self.directory.exists():
            raise CredentialCleanupError()


def _ini_value(value: str) -> str:
    # A line break would let a value inject keys or sections in the file.
    if "\n" in value or "\r" in value:
        raise InvalidResolvedSecretError()
    return value


def _ini(section: str, values: Dict[str, Optional[str]]) -> bytes:
    lines = [f"[{section}]"]
    lines += [f"{key} = {_ini_value(value)}" for key, value in values.items() if value]
    return ("\n".join(lines) + "\n").encode()


def _aws_region_env(region: Optional[str]) -> Dict[str, str]:
    if not region:
        return {}
    return {"AWS_REGION": region, "AWS_DEFAULT_REGION": region}


def _aws_access_key(
    secret: AwsAccessKeySecret, workspace: _Workspace
) -> Dict[str, str]:
    env = {
        **_aws_region_env(secret.aws_default_region),
        "AWS_ACCESS_KEY_ID": secret.aws_access_key_id,
        "AWS_SECRET_ACCESS_KEY": secret.aws_secret_access_key,
    }
    if secret.aws_session_token:
        env["AWS_SESSION_TOKEN"] = secret.aws_session_token
    return env


def _aws_assume_role(
    secret: AwsAssumeRoleSecret, workspace: _Workspace
) -> Dict[str, str]:
    env = {"AWS_PROFILE": AWS_TARGET_PROFILE}
    profile: Dict[str, Optional[str]] = {"role_arn": secret.aws_role_arn}
    if secret.aws_source_identity_type == AwsSourceIdentityType.INSTANCE_DEFAULT:
        profile["credential_source"] = "Ec2InstanceMetadata"
    else:
        credentials = workspace.write(
            _ini(
                AWS_SOURCE_PROFILE,
                {
                    "aws_access_key_id": secret.aws_source_profile_access_key_id,
                    "aws_secret_access_key": (
                        secret.aws_source_profile_secret_access_key
                    ),
                },
            ),
            prefix="aws-credentials-",
        )
        env["AWS_SHARED_CREDENTIALS_FILE"] = str(credentials)
        profile["source_profile"] = AWS_SOURCE_PROFILE
    profile["external_id"] = secret.aws_external_id
    profile["region"] = secret.aws_default_region
    config = workspace.write(
        _ini(f"profile {AWS_TARGET_PROFILE}", profile), prefix="aws-config-"
    )
    env["AWS_CONFIG_FILE"] = str(config)
    return env


def _azure_authority_host(environment: str) -> str:
    try:
        return AZURE_AUTHORITY_HOSTS[environment]
    except KeyError:
        raise InvalidResolvedSecretError() from None


def _azure_service_principal(
    secret: AzureServicePrincipalSecret, workspace: _Workspace
) -> Dict[str, str]:
    env = {
        "AZURE_CLIENT_ID": secret.azure_client_id,
        "AZURE_CLIENT_SECRET": secret.azure_client_secret,
        "AZURE_TENANT_ID": secret.azure_tenant_id,
        "AZURE_AUTHORITY_HOST": _azure_authority_host(secret.azure_environment),
    }
    if secret.azure_subscription_id:
        env["AZURE_SUBSCRIPTION_ID"] = secret.azure_subscription_id
    return env


def _azure_managed_identity(
    secret: AzureManagedIdentitySecret, workspace: _Workspace
) -> Dict[str, str]:
    env = {"AZURE_AUTHORITY_HOST": _azure_authority_host(secret.azure_environment)}
    # Without a client id, the system-assigned identity is used.
    if secret.azure_client_id:
        env["AZURE_CLIENT_ID"] = secret.azure_client_id
    if secret.azure_subscription_id:
        env["AZURE_SUBSCRIPTION_ID"] = secret.azure_subscription_id
    return env


def _gcp_env(
    credentials_file: Path, scope: str, project_id: Optional[str]
) -> Dict[str, str]:
    env = {
        "GOOGLE_APPLICATION_CREDENTIALS": str(credentials_file),
        "GOOGLE_CLOUD_UNIVERSE_DOMAIN": scope,
    }
    if project_id:
        env["GOOGLE_PROJECT"] = project_id
    return env


def _gcp_service_account(
    secret: GcpServiceAccountSecret, workspace: _Workspace
) -> Dict[str, str]:
    credentials_file = workspace.write(
        secret.gcp_private_key_json, prefix="gcp-credentials-", suffix=".json"
    )
    return _gcp_env(credentials_file, secret.gcp_scope, secret.gcp_project_id)


def _gcp_oauth2(secret: GcpOAuth2Secret, workspace: _Workspace) -> Dict[str, str]:
    authorized_user = {
        "type": "authorized_user",
        "client_id": secret.gcp_oauth_client_id,
        "client_secret": secret.gcp_oauth_client_secret,
        "refresh_token": secret.gcp_oauth_refresh_token,
        "universe_domain": secret.gcp_scope,
    }
    credentials_file = workspace.write(
        json.dumps(authorized_user).encode(),
        prefix="gcp-credentials-",
        suffix=".json",
    )
    return _gcp_env(credentials_file, secret.gcp_scope, secret.gcp_project_id)


_MATERIALIZERS: Dict[SecretType, Callable[..., Dict[str, str]]] = {
    SecretType.AWS_ACCESS_KEY: _aws_access_key,
    SecretType.AWS_ASSUME_ROLE: _aws_assume_role,
    SecretType.AZURE_SERVICE_PRINCIPAL: _azure_service_principal,
    SecretType.AZURE_MANAGED_IDENTITY: _azure_managed_identity,
    SecretType.GCP_SERVICE_ACCOUNT: _gcp_service_account,
    SecretType.GCP_OAUTH2: _gcp_oauth2,
}


@contextmanager
def materialize(
    resolved: ResolvedSecret, temporary_root: Optional[Path] = None
) -> Iterator[MaterializedCredential]:
    """Materialize ``resolved`` for the duration of the ``with`` block.

    Args:
        resolved: the secret returned by ``resolve_inject_credential``.
        temporary_root: parent of the private directory, the system temporary
            directory when omitted.

    Raises:
        UnsupportedSecretTypeError: the secret type is not a cloud credential
            (``USERNAME_PASSWORD``, ``HASH``).
        InvalidResolvedSecretError: a value cannot be materialized safely.
        CredentialCleanupError: the temporary files could not be removed.
    """
    materializer = _MATERIALIZERS.get(resolved.secret_type)
    if materializer is None:
        raise UnsupportedSecretTypeError(resolved.secret_type.value)
    workspace = _Workspace(temporary_root)
    try:
        env = materializer(resolved, workspace)
        yield MaterializedCredential(
            secret_type=resolved.secret_type, env=env, files=list(workspace.files)
        )
    finally:
        workspace.cleanup()


__all__ = [
    "AZURE_AUTHORITY_HOSTS",
    "CredentialCleanupError",
    "MaterializedCredential",
    "materialize",
]
