import base64
import unittest

from pyoaev.credential import (
    AwsAccessKeySecret,
    AwsAssumeRoleSecret,
    AwsSourceIdentityType,
    AzureManagedIdentitySecret,
    AzureServicePrincipalSecret,
    CredentialErrorCode,
    CredentialResolutionError,
    CredentialType,
    GcpOAuth2Secret,
    GcpServiceAccountSecret,
    HashAlgorithm,
    HashSecret,
    InvalidResolvedSecretError,
    SecretType,
    UnsupportedSecretTypeError,
    UsernamePasswordSecret,
    ensure_compatible,
    parse_resolved_secret,
)

REFERENCE = "credential-reference-id"
SECRET = "super-secret-value"
GCP_KEY_JSON = b'{"type": "service_account", "private_key": "super-secret-value"}'

PAYLOADS = {
    SecretType.USERNAME_PASSWORD: {
        "username": "alice",
        "password": SECRET,
    },
    SecretType.HASH: {
        "hash_algorithm": "NTLM",
        "hash": SECRET,
    },
    SecretType.AWS_ACCESS_KEY: {
        "aws_default_region": "eu-west-3",
        "aws_access_key_id": "AKIAEXAMPLE",
        "aws_secret_access_key": SECRET,
        "aws_session_token": SECRET,
    },
    SecretType.AWS_ASSUME_ROLE: {
        "aws_default_region": "us-east-1",
        "aws_role_arn": "arn:aws:iam::123456789012:role/srt",
        "aws_source_identity_type": "STATIC_ACCESS_KEY",
        "aws_external_id": "external-id",
        "aws_source_profile_access_key_id": "AKIASOURCE",
        "aws_source_profile_secret_access_key": SECRET,
    },
    SecretType.AZURE_SERVICE_PRINCIPAL: {
        "azure_environment": "AzureCloud",
        "azure_client_id": "client-id",
        "azure_client_secret": SECRET,
        "azure_tenant_id": "tenant-id",
        "azure_subscription_id": "subscription-id",
    },
    SecretType.AZURE_MANAGED_IDENTITY: {
        "azure_environment": "AzureChinaCloud",
        "azure_client_id": "client-id",
        "azure_subscription_id": "subscription-id",
    },
    SecretType.GCP_SERVICE_ACCOUNT: {
        "gcp_scope": "googleapis.com",
        "gcp_project_id": "project-id",
        "gcp_private_key_json": base64.b64encode(GCP_KEY_JSON).decode(),
    },
    SecretType.GCP_OAUTH2: {
        "gcp_scope": "googleapis.com",
        "gcp_project_id": "project-id",
        "gcp_oauth_client_id": "client-id",
        "gcp_oauth_client_secret": SECRET,
        "gcp_oauth_refresh_token": SECRET,
    },
}

EXPECTED_CREDENTIAL_TYPES = {
    SecretType.USERNAME_PASSWORD: CredentialType.IDENTITY,
    SecretType.HASH: CredentialType.IDENTITY,
    SecretType.AWS_ACCESS_KEY: CredentialType.CLOUD_AWS,
    SecretType.AWS_ASSUME_ROLE: CredentialType.CLOUD_AWS,
    SecretType.AZURE_SERVICE_PRINCIPAL: CredentialType.CLOUD_AZURE,
    SecretType.AZURE_MANAGED_IDENTITY: CredentialType.CLOUD_AZURE,
    SecretType.GCP_SERVICE_ACCOUNT: CredentialType.CLOUD_GCP,
    SecretType.GCP_OAUTH2: CredentialType.CLOUD_GCP,
}


def _parse(secret_type, **overrides):
    value = {**PAYLOADS[secret_type], **overrides}
    value = {key: item for key, item in value.items() if item is not None}
    return parse_resolved_secret(
        {"type": secret_type.value, "value": value}, reference=REFERENCE
    )


class SecretTypeTest(unittest.TestCase):
    def test_secret_type_mirrors_platform_labels(self):
        self.assertEqual(
            [secret_type.value for secret_type in SecretType],
            [
                "USERNAME_PASSWORD",
                "HASH",
                "AWS_ACCESS_KEY",
                "AWS_ASSUME_ROLE",
                "AZURE_SERVICE_PRINCIPAL",
                "AZURE_MANAGED_IDENTITY",
                "GCP_SERVICE_ACCOUNT",
                "GCP_OAUTH2",
            ],
        )


class ParseResolvedSecretTest(unittest.TestCase):
    def test_username_password(self):
        resolved = _parse(SecretType.USERNAME_PASSWORD)

        self.assertEqual(resolved, UsernamePasswordSecret("alice", SECRET))

    def test_hash(self):
        resolved = _parse(SecretType.HASH)

        self.assertEqual(resolved, HashSecret(HashAlgorithm.NTLM, SECRET))

    def test_aws_access_key(self):
        resolved = _parse(SecretType.AWS_ACCESS_KEY)

        self.assertEqual(
            resolved,
            AwsAccessKeySecret(
                aws_access_key_id="AKIAEXAMPLE",
                aws_secret_access_key=SECRET,
                aws_default_region="eu-west-3",
                aws_session_token=SECRET,
            ),
        )

    def test_aws_access_key_optional_fields_default_to_none(self):
        resolved = _parse(
            SecretType.AWS_ACCESS_KEY, aws_default_region=None, aws_session_token=None
        )

        self.assertIsNone(resolved.aws_default_region)
        self.assertIsNone(resolved.aws_session_token)

    def test_aws_assume_role_with_static_access_key(self):
        resolved = _parse(SecretType.AWS_ASSUME_ROLE)

        self.assertEqual(
            resolved,
            AwsAssumeRoleSecret(
                aws_role_arn="arn:aws:iam::123456789012:role/srt",
                aws_source_identity_type=AwsSourceIdentityType.STATIC_ACCESS_KEY,
                aws_default_region="us-east-1",
                aws_external_id="external-id",
                aws_source_profile_access_key_id="AKIASOURCE",
                aws_source_profile_secret_access_key=SECRET,
            ),
        )

    def test_aws_assume_role_with_instance_default_needs_no_source_keys(self):
        resolved = _parse(
            SecretType.AWS_ASSUME_ROLE,
            aws_source_identity_type="INSTANCE_DEFAULT",
            aws_external_id=None,
            aws_source_profile_access_key_id=None,
            aws_source_profile_secret_access_key=None,
        )

        self.assertEqual(
            resolved.aws_source_identity_type, AwsSourceIdentityType.INSTANCE_DEFAULT
        )
        self.assertIsNone(resolved.aws_source_profile_access_key_id)
        self.assertIsNone(resolved.aws_source_profile_secret_access_key)

    def test_aws_assume_role_with_static_access_key_requires_source_keys(self):
        with self.assertRaises(InvalidResolvedSecretError):
            _parse(
                SecretType.AWS_ASSUME_ROLE, aws_source_profile_secret_access_key=None
            )

    def test_azure_service_principal(self):
        resolved = _parse(SecretType.AZURE_SERVICE_PRINCIPAL)

        self.assertEqual(
            resolved,
            AzureServicePrincipalSecret(
                azure_environment="AzureCloud",
                azure_client_id="client-id",
                azure_client_secret=SECRET,
                azure_tenant_id="tenant-id",
                azure_subscription_id="subscription-id",
            ),
        )

    def test_azure_managed_identity(self):
        resolved = _parse(SecretType.AZURE_MANAGED_IDENTITY)

        self.assertEqual(
            resolved,
            AzureManagedIdentitySecret(
                azure_environment="AzureChinaCloud",
                azure_client_id="client-id",
                azure_subscription_id="subscription-id",
            ),
        )

    def test_azure_managed_identity_without_client_id(self):
        resolved = _parse(SecretType.AZURE_MANAGED_IDENTITY, azure_client_id=None)

        self.assertIsNone(resolved.azure_client_id)

    def test_gcp_service_account_decodes_the_private_key_json(self):
        resolved = _parse(SecretType.GCP_SERVICE_ACCOUNT)

        self.assertEqual(
            resolved,
            GcpServiceAccountSecret(
                gcp_scope="googleapis.com",
                gcp_private_key_json=GCP_KEY_JSON,
                gcp_project_id="project-id",
            ),
        )

    def test_gcp_service_account_with_invalid_base64(self):
        with self.assertRaises(InvalidResolvedSecretError):
            _parse(SecretType.GCP_SERVICE_ACCOUNT, gcp_private_key_json="not base64!")

    def test_gcp_oauth2(self):
        resolved = _parse(SecretType.GCP_OAUTH2)

        self.assertEqual(
            resolved,
            GcpOAuth2Secret(
                gcp_scope="googleapis.com",
                gcp_oauth_client_id="client-id",
                gcp_oauth_client_secret=SECRET,
                gcp_oauth_refresh_token=SECRET,
                gcp_project_id="project-id",
            ),
        )

    def test_every_type_exposes_its_secret_and_credential_type(self):
        for secret_type, credential_type in EXPECTED_CREDENTIAL_TYPES.items():
            with self.subTest(secret_type=secret_type):
                resolved = _parse(secret_type)

                self.assertIs(resolved.secret_type, secret_type)
                self.assertIs(resolved.credential_type, credential_type)

    def test_repr_and_str_never_expose_secret_material(self):
        for secret_type in SecretType:
            with self.subTest(secret_type=secret_type):
                resolved = _parse(secret_type)

                self.assertNotIn(SECRET, repr(resolved))
                self.assertNotIn(SECRET, str(resolved))

    def test_resolved_secret_is_frozen(self):
        resolved = _parse(SecretType.AWS_ACCESS_KEY)

        with self.assertRaises(AttributeError):
            resolved.aws_secret_access_key = "other"

    def test_unknown_extra_keys_are_ignored(self):
        resolved = _parse(SecretType.USERNAME_PASSWORD, domain="corp")

        self.assertEqual(resolved, UsernamePasswordSecret("alice", SECRET))

    def test_missing_required_key(self):
        for secret_type, key in (
            (SecretType.AWS_ACCESS_KEY, "aws_secret_access_key"),
            (SecretType.AWS_ASSUME_ROLE, "aws_role_arn"),
            (SecretType.AZURE_SERVICE_PRINCIPAL, "azure_tenant_id"),
            (SecretType.AZURE_MANAGED_IDENTITY, "azure_environment"),
            (SecretType.GCP_SERVICE_ACCOUNT, "gcp_private_key_json"),
            (SecretType.GCP_OAUTH2, "gcp_oauth_refresh_token"),
        ):
            with self.subTest(secret_type=secret_type, key=key):
                with self.assertRaises(InvalidResolvedSecretError) as context:
                    _parse(secret_type, **{key: None})

                self.assertEqual(
                    context.exception.code,
                    CredentialErrorCode.CREDENTIAL_ACCESS_DENIED,
                )

    def test_empty_required_value_is_missing(self):
        with self.assertRaises(InvalidResolvedSecretError):
            _parse(SecretType.AWS_ACCESS_KEY, aws_access_key_id="")

    def test_non_string_value(self):
        with self.assertRaises(InvalidResolvedSecretError):
            _parse(SecretType.AWS_ACCESS_KEY, aws_access_key_id=123)

    def test_unknown_enum_value(self):
        with self.assertRaises(InvalidResolvedSecretError):
            _parse(SecretType.AWS_ASSUME_ROLE, aws_source_identity_type="FEDERATED")

    def test_invalid_error_never_exposes_secret_material(self):
        with self.assertRaises(InvalidResolvedSecretError) as context:
            _parse(SecretType.GCP_SERVICE_ACCOUNT, gcp_private_key_json=SECRET)

        error = context.exception
        self.assertEqual(error.reference, REFERENCE)
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)
        self.assertNotIn(SECRET, str(error))

    def test_payload_is_not_a_dict(self):
        for payload in (None, [], "AWS_ACCESS_KEY"):
            with self.subTest(payload=payload):
                with self.assertRaises(InvalidResolvedSecretError):
                    parse_resolved_secret(payload)

    def test_value_is_not_a_dict(self):
        for value in (None, [], "secret"):
            with self.subTest(value=value):
                with self.assertRaises(InvalidResolvedSecretError):
                    parse_resolved_secret({"type": "AWS_ACCESS_KEY", "value": value})

    def test_unknown_type(self):
        with self.assertRaises(UnsupportedSecretTypeError) as context:
            parse_resolved_secret(
                {"type": "KERBEROS_TICKET", "value": {}}, reference=REFERENCE
            )

        error = context.exception
        self.assertEqual(error.secret_type, "KERBEROS_TICKET")
        self.assertEqual(error.code, CredentialErrorCode.CREDENTIAL_INCOMPATIBLE)
        self.assertIn(REFERENCE, error.message)

    def test_missing_type(self):
        with self.assertRaises(UnsupportedSecretTypeError) as context:
            parse_resolved_secret({"value": {}})

        self.assertIsNone(context.exception.secret_type)


class EnsureCompatibleTest(unittest.TestCase):
    def test_matching_credential_type_returns_the_secret(self):
        for secret_type, credential_type in EXPECTED_CREDENTIAL_TYPES.items():
            with self.subTest(secret_type=secret_type):
                resolved = _parse(secret_type)

                self.assertIs(ensure_compatible(resolved, credential_type), resolved)

    def test_mismatching_credential_type_is_incompatible(self):
        for secret_type, credential_type in EXPECTED_CREDENTIAL_TYPES.items():
            for expected in CredentialType:
                if expected == credential_type:
                    continue
                with self.subTest(secret_type=secret_type, expected=expected):
                    with self.assertRaises(CredentialResolutionError) as context:
                        ensure_compatible(
                            _parse(secret_type), expected, reference=REFERENCE
                        )

                    error = context.exception
                    self.assertEqual(
                        error.code, CredentialErrorCode.CREDENTIAL_INCOMPATIBLE
                    )
                    self.assertIn(REFERENCE, error.message)
                    self.assertNotIn(SECRET, str(error))

    def test_provider_name_uses_the_contract_mapping(self):
        for provider, secret_type in (
            ("aws", SecretType.AWS_ACCESS_KEY),
            ("eks", SecretType.AWS_ASSUME_ROLE),
            ("AZURE", SecretType.AZURE_SERVICE_PRINCIPAL),
            ("gcp", SecretType.GCP_OAUTH2),
        ):
            with self.subTest(provider=provider):
                resolved = _parse(secret_type)

                self.assertIs(ensure_compatible(resolved, provider), resolved)

    def test_provider_name_mismatch_is_incompatible(self):
        with self.assertRaises(CredentialResolutionError) as context:
            ensure_compatible(_parse(SecretType.GCP_SERVICE_ACCOUNT), "aws")

        self.assertEqual(
            context.exception.code, CredentialErrorCode.CREDENTIAL_INCOMPATIBLE
        )

    def test_unknown_provider_name_is_a_programming_error(self):
        with self.assertRaises(ValueError):
            ensure_compatible(_parse(SecretType.AWS_ACCESS_KEY), "kubernetes")


if __name__ == "__main__":
    unittest.main()
