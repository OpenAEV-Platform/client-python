import configparser
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pyoaev.credential import (
    AwsAccessKeySecret,
    AwsAssumeRoleSecret,
    AwsSourceIdentityType,
    AzureManagedIdentitySecret,
    AzureServicePrincipalSecret,
    CredentialCleanupError,
    GcpOAuth2Secret,
    GcpServiceAccountSecret,
    HashAlgorithm,
    HashSecret,
    InvalidResolvedSecretError,
    SecretType,
    UnsupportedSecretTypeError,
    UsernamePasswordSecret,
    materialize,
)

SECRET = "super-secret-value"
GCP_KEY_JSON = b'{"type": "service_account", "private_key": "super-secret-value"}'

AWS_ACCESS_KEY = AwsAccessKeySecret(
    aws_access_key_id="AKIAEXAMPLE",
    aws_secret_access_key=SECRET,
    aws_default_region="eu-west-3",
    aws_session_token="session-token",
)
AWS_ASSUME_ROLE_STATIC = AwsAssumeRoleSecret(
    aws_role_arn="arn:aws:iam::123456789012:role/srt",
    aws_source_identity_type=AwsSourceIdentityType.STATIC_ACCESS_KEY,
    aws_default_region="us-east-1",
    aws_external_id="external-id",
    aws_source_profile_access_key_id="AKIASOURCE",
    aws_source_profile_secret_access_key=SECRET,
)
AWS_ASSUME_ROLE_INSTANCE = AwsAssumeRoleSecret(
    aws_role_arn="arn:aws:iam::123456789012:role/srt",
    aws_source_identity_type=AwsSourceIdentityType.INSTANCE_DEFAULT,
)
AZURE_SERVICE_PRINCIPAL = AzureServicePrincipalSecret(
    azure_environment="AzureCloud",
    azure_client_id="client-id",
    azure_client_secret=SECRET,
    azure_tenant_id="tenant-id",
    azure_subscription_id="subscription-id",
)
AZURE_MANAGED_IDENTITY = AzureManagedIdentitySecret(
    azure_environment="AzureUSGovernment",
    azure_client_id="client-id",
    azure_subscription_id="subscription-id",
)
GCP_SERVICE_ACCOUNT = GcpServiceAccountSecret(
    gcp_scope="googleapis.com",
    gcp_private_key_json=GCP_KEY_JSON,
    gcp_project_id="project-id",
)
GCP_OAUTH2 = GcpOAuth2Secret(
    gcp_scope="googleapis.com",
    gcp_oauth_client_id="client-id",
    gcp_oauth_client_secret=SECRET,
    gcp_oauth_refresh_token="refresh-token",
    gcp_project_id="project-id",
)

ALL_CLOUD_SECRETS = (
    AWS_ACCESS_KEY,
    AWS_ASSUME_ROLE_STATIC,
    AWS_ASSUME_ROLE_INSTANCE,
    AZURE_SERVICE_PRINCIPAL,
    AZURE_MANAGED_IDENTITY,
    GCP_SERVICE_ACCOUNT,
    GCP_OAUTH2,
)
SECRETS_WITH_FILES = (
    AWS_ASSUME_ROLE_STATIC,
    AWS_ASSUME_ROLE_INSTANCE,
    GCP_SERVICE_ACCOUNT,
    GCP_OAUTH2,
)


def _read_ini(path: str) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    return parser


class MaterializerTestCase(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.root = Path(temporary_directory.name)

    def materialize(self, resolved):
        return materialize(resolved, temporary_root=self.root)

    def assert_root_is_empty(self):
        self.assertEqual(list(self.root.iterdir()), [])


class AwsMaterializerTest(MaterializerTestCase):
    def test_access_key(self):
        with self.materialize(AWS_ACCESS_KEY) as credential:
            self.assertEqual(credential.secret_type, SecretType.AWS_ACCESS_KEY)
            self.assertEqual(
                credential.env,
                {
                    "AWS_REGION": "eu-west-3",
                    "AWS_DEFAULT_REGION": "eu-west-3",
                    "AWS_ACCESS_KEY_ID": "AKIAEXAMPLE",
                    "AWS_SECRET_ACCESS_KEY": SECRET,
                    "AWS_SESSION_TOKEN": "session-token",
                },
            )
            self.assertEqual(credential.files, [])
            self.assert_root_is_empty()

    def test_access_key_without_region_nor_session_token(self):
        resolved = AwsAccessKeySecret(
            aws_access_key_id="AKIAEXAMPLE", aws_secret_access_key=SECRET
        )

        with self.materialize(resolved) as credential:
            self.assertEqual(
                credential.env,
                {
                    "AWS_ACCESS_KEY_ID": "AKIAEXAMPLE",
                    "AWS_SECRET_ACCESS_KEY": SECRET,
                },
            )

    def test_assume_role_with_static_access_key(self):
        with self.materialize(AWS_ASSUME_ROLE_STATIC) as credential:
            env = credential.env
            self.assertEqual(credential.secret_type, SecretType.AWS_ASSUME_ROLE)
            self.assertEqual(
                set(env),
                {"AWS_PROFILE", "AWS_SHARED_CREDENTIALS_FILE", "AWS_CONFIG_FILE"},
            )
            self.assertEqual(env["AWS_PROFILE"], "srt-target")
            self.assertEqual(
                credential.files,
                [
                    Path(env["AWS_SHARED_CREDENTIALS_FILE"]),
                    Path(env["AWS_CONFIG_FILE"]),
                ],
            )

            credentials = _read_ini(env["AWS_SHARED_CREDENTIALS_FILE"])
            self.assertEqual(credentials.sections(), ["srt-source"])
            self.assertEqual(
                dict(credentials["srt-source"]),
                {
                    "aws_access_key_id": "AKIASOURCE",
                    "aws_secret_access_key": SECRET,
                },
            )

            config = _read_ini(env["AWS_CONFIG_FILE"])
            self.assertEqual(config.sections(), ["profile srt-target"])
            self.assertEqual(
                dict(config["profile srt-target"]),
                {
                    "role_arn": "arn:aws:iam::123456789012:role/srt",
                    "source_profile": "srt-source",
                    "external_id": "external-id",
                    "region": "us-east-1",
                },
            )

    def test_assume_role_with_instance_default(self):
        with self.materialize(AWS_ASSUME_ROLE_INSTANCE) as credential:
            env = credential.env
            self.assertEqual(set(env), {"AWS_PROFILE", "AWS_CONFIG_FILE"})
            self.assertEqual(credential.files, [Path(env["AWS_CONFIG_FILE"])])

            config = _read_ini(env["AWS_CONFIG_FILE"])
            self.assertEqual(
                dict(config["profile srt-target"]),
                {
                    "role_arn": "arn:aws:iam::123456789012:role/srt",
                    "credential_source": "Ec2InstanceMetadata",
                },
            )

    def test_line_break_in_a_file_value_is_rejected(self):
        resolved = AwsAssumeRoleSecret(
            aws_role_arn="arn:aws:iam::123456789012:role/srt\n[profile other]",
            aws_source_identity_type=AwsSourceIdentityType.INSTANCE_DEFAULT,
        )

        with self.assertRaises(InvalidResolvedSecretError):
            with self.materialize(resolved):
                self.fail("must not be reached")

        self.assert_root_is_empty()


class AzureMaterializerTest(MaterializerTestCase):
    def test_service_principal(self):
        with self.materialize(AZURE_SERVICE_PRINCIPAL) as credential:
            self.assertEqual(credential.secret_type, SecretType.AZURE_SERVICE_PRINCIPAL)
            self.assertEqual(
                credential.env,
                {
                    "AZURE_CLIENT_ID": "client-id",
                    "AZURE_CLIENT_SECRET": SECRET,
                    "AZURE_TENANT_ID": "tenant-id",
                    "AZURE_SUBSCRIPTION_ID": "subscription-id",
                    "AZURE_AUTHORITY_HOST": "https://login.microsoftonline.com/",
                },
            )
            self.assertEqual(credential.files, [])

    def test_managed_identity(self):
        with self.materialize(AZURE_MANAGED_IDENTITY) as credential:
            self.assertEqual(credential.secret_type, SecretType.AZURE_MANAGED_IDENTITY)
            self.assertEqual(
                credential.env,
                {
                    "AZURE_CLIENT_ID": "client-id",
                    "AZURE_SUBSCRIPTION_ID": "subscription-id",
                    "AZURE_AUTHORITY_HOST": "https://login.microsoftonline.us/",
                },
            )

    def test_system_assigned_managed_identity(self):
        resolved = AzureManagedIdentitySecret(azure_environment="AzureChinaCloud")

        with self.materialize(resolved) as credential:
            self.assertEqual(
                credential.env,
                {"AZURE_AUTHORITY_HOST": "https://login.chinacloudapi.cn/"},
            )

    def test_unknown_environment_is_rejected(self):
        resolved = AzureManagedIdentitySecret(azure_environment="AzureGermanCloud")

        with self.assertRaises(InvalidResolvedSecretError):
            with self.materialize(resolved):
                self.fail("must not be reached")


class GcpMaterializerTest(MaterializerTestCase):
    def test_service_account(self):
        with self.materialize(GCP_SERVICE_ACCOUNT) as credential:
            env = credential.env
            self.assertEqual(credential.secret_type, SecretType.GCP_SERVICE_ACCOUNT)
            self.assertEqual(
                set(env),
                {
                    "GOOGLE_APPLICATION_CREDENTIALS",
                    "GOOGLE_PROJECT",
                    "GOOGLE_CLOUD_UNIVERSE_DOMAIN",
                },
            )
            self.assertEqual(env["GOOGLE_PROJECT"], "project-id")
            self.assertEqual(env["GOOGLE_CLOUD_UNIVERSE_DOMAIN"], "googleapis.com")
            credentials_file = Path(env["GOOGLE_APPLICATION_CREDENTIALS"])
            self.assertEqual(credential.files, [credentials_file])
            self.assertEqual(credentials_file.suffix, ".json")
            self.assertEqual(credentials_file.read_bytes(), GCP_KEY_JSON)

    def test_oauth2(self):
        with self.materialize(GCP_OAUTH2) as credential:
            env = credential.env
            self.assertEqual(credential.secret_type, SecretType.GCP_OAUTH2)
            self.assertEqual(env["GOOGLE_PROJECT"], "project-id")
            self.assertEqual(env["GOOGLE_CLOUD_UNIVERSE_DOMAIN"], "googleapis.com")
            credentials_file = Path(env["GOOGLE_APPLICATION_CREDENTIALS"])
            self.assertEqual(credential.files, [credentials_file])
            self.assertEqual(
                json.loads(credentials_file.read_text(encoding="utf-8")),
                {
                    "type": "authorized_user",
                    "client_id": "client-id",
                    "client_secret": SECRET,
                    "refresh_token": "refresh-token",
                    "universe_domain": "googleapis.com",
                },
            )

    def test_without_project_id(self):
        resolved = GcpOAuth2Secret(
            gcp_scope="googleapis.com",
            gcp_oauth_client_id="client-id",
            gcp_oauth_client_secret=SECRET,
            gcp_oauth_refresh_token="refresh-token",
        )

        with self.materialize(resolved) as credential:
            self.assertNotIn("GOOGLE_PROJECT", credential.env)


class MaterializerLifecycleTest(MaterializerTestCase):
    def test_identity_secrets_are_not_supported(self):
        for resolved in (
            UsernamePasswordSecret("alice", SECRET),
            HashSecret(HashAlgorithm.NTLM, SECRET),
        ):
            with self.subTest(secret_type=resolved.secret_type):
                with self.assertRaises(UnsupportedSecretTypeError):
                    with self.materialize(resolved):
                        self.fail("must not be reached")

    def test_files_are_written_in_a_private_directory_under_the_root(self):
        for resolved in SECRETS_WITH_FILES:
            with self.subTest(secret_type=resolved.secret_type):
                with self.materialize(resolved) as credential:
                    directories = list(self.root.iterdir())
                    self.assertEqual(len(directories), 1)
                    for path in credential.files:
                        self.assertEqual(path.parent, directories[0])

    @unittest.skipIf(os.name == "nt", "POSIX permissions only")
    def test_posix_permissions(self):
        for resolved in SECRETS_WITH_FILES:
            with self.subTest(secret_type=resolved.secret_type):
                with self.materialize(resolved) as credential:
                    directory = credential.files[0].parent
                    self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
                    for path in credential.files:
                        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_cleanup_on_success(self):
        for resolved in ALL_CLOUD_SECRETS:
            with self.subTest(secret_type=resolved.secret_type):
                with self.materialize(resolved) as credential:
                    files = credential.files

                for path in files:
                    self.assertFalse(path.exists())
                self.assert_root_is_empty()

    def test_cleanup_on_exception(self):
        for resolved in ALL_CLOUD_SECRETS:
            with self.subTest(secret_type=resolved.secret_type):
                with self.assertRaises(RuntimeError):
                    with self.materialize(resolved) as credential:
                        files = credential.files
                        raise RuntimeError("execution failed")

                for path in files:
                    self.assertFalse(path.exists())
                self.assert_root_is_empty()

    def test_cleanup_when_a_write_fails(self):
        with mock.patch(
            "pyoaev.credential.materializer.os.fdopen", side_effect=OSError("disk full")
        ):
            with self.assertRaises(OSError):
                with self.materialize(GCP_SERVICE_ACCOUNT):
                    self.fail("must not be reached")

        self.assert_root_is_empty()

    def test_cleanup_failure_is_reported_without_details(self):
        with mock.patch("pyoaev.credential.materializer.shutil.rmtree"):
            with self.assertRaises(CredentialCleanupError) as context:
                with self.materialize(GCP_SERVICE_ACCOUNT) as credential:
                    directory = credential.files[0].parent

        self.assertEqual(str(context.exception), "temporary credential cleanup failed")
        # Remove what the mocked cleanup left behind.
        for path in directory.iterdir():
            path.unlink()
        directory.rmdir()

    def test_repr_never_exposes_secret_material(self):
        for resolved in ALL_CLOUD_SECRETS:
            with self.subTest(secret_type=resolved.secret_type):
                with self.materialize(resolved) as credential:
                    self.assertNotIn(SECRET, repr(credential))


if __name__ == "__main__":
    unittest.main()
