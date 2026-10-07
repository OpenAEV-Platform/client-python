import json
import unittest
from unittest import mock

import requests

from pyoaev import OpenAEV
from pyoaev.credential import (
    AwsAccessKeySecret,
    CredentialAttachment,
    CredentialErrorCode,
    CredentialResolutionError,
    CredentialType,
    get_credential_attachment,
    resolve_inject_credential,
)

INJECT_ID = "inject-id"
REFERENCE = "credential-reference-id"
AUTHORISATION_CODE = "authorisation-code"
SECRET = "super-secret-value"

AWS_PAYLOAD = {
    "type": "AWS_ACCESS_KEY",
    "value": {
        "aws_default_region": "eu-west-3",
        "aws_access_key_id": "AKIAEXAMPLE",
        "aws_secret_access_key": SECRET,
    },
}


def _message(attachments=mock.sentinel.missing):
    data = {"injection": {"inject_id": INJECT_ID, "inject_content": {}}}
    if attachments is not mock.sentinel.missing:
        data["attachments"] = attachments
    return data


def _attachments(references=(REFERENCE,), authorisation_code=AUTHORISATION_CODE):
    return {
        "credential_references": list(references),
        "authorisation_code": authorisation_code,
    }


class GetCredentialAttachmentTest(unittest.TestCase):
    def test_no_attachments_is_legacy_path(self):
        self.assertIsNone(get_credential_attachment(_message()))

    def test_null_attachments_is_legacy_path(self):
        self.assertIsNone(get_credential_attachment(_message(None)))

    def test_empty_references_is_legacy_path(self):
        self.assertIsNone(get_credential_attachment(_message(_attachments([]))))

    def test_null_references_is_legacy_path(self):
        self.assertIsNone(
            get_credential_attachment(
                _message({"credential_references": None, "authorisation_code": "c"})
            )
        )

    def test_single_reference(self):
        attachment = get_credential_attachment(_message(_attachments()))

        self.assertEqual(
            attachment, CredentialAttachment(REFERENCE, AUTHORISATION_CODE)
        )

    def test_several_references_uses_the_first_one(self):
        attachment = get_credential_attachment(
            _message(_attachments([REFERENCE, "second-reference"]))
        )

        self.assertEqual(attachment.reference, REFERENCE)

    def test_missing_authorisation_code_is_access_denied(self):
        for authorisation_code in (None, "", "  "):
            with self.subTest(authorisation_code=authorisation_code):
                with self.assertRaises(CredentialResolutionError) as context:
                    get_credential_attachment(
                        _message(_attachments(authorisation_code=authorisation_code))
                    )

                self.assertEqual(
                    context.exception.code,
                    CredentialErrorCode.CREDENTIAL_ACCESS_DENIED,
                )
                self.assertEqual(context.exception.reference, REFERENCE)

    def test_authorisation_code_key_absent_is_access_denied(self):
        with self.assertRaises(CredentialResolutionError) as context:
            get_credential_attachment(_message({"credential_references": [REFERENCE]}))

        self.assertEqual(
            context.exception.code, CredentialErrorCode.CREDENTIAL_ACCESS_DENIED
        )

    def test_malformed_attachments_is_access_denied(self):
        for attachments in (
            "not a dict",
            ["not", "a", "dict"],
            _attachments(references=[None]),
            _attachments(references=[""]),
            {"credential_references": REFERENCE, "authorisation_code": "c"},
        ):
            with self.subTest(attachments=attachments):
                with self.assertRaises(CredentialResolutionError) as context:
                    get_credential_attachment(_message(attachments))

                self.assertEqual(
                    context.exception.code,
                    CredentialErrorCode.CREDENTIAL_ACCESS_DENIED,
                )

    def test_repr_never_exposes_the_authorisation_code(self):
        attachment = get_credential_attachment(_message(_attachments()))

        self.assertNotIn(AUTHORISATION_CODE, repr(attachment))
        self.assertNotIn(AUTHORISATION_CODE, str(attachment))


class ResolveInjectCredentialTest(unittest.TestCase):
    def setUp(self):
        self.api = mock.MagicMock()
        self.api.inject.resolve_attachment_secret.return_value = AWS_PAYLOAD

    def test_no_reference_sends_no_resolution_request(self):
        for data in (_message(), _message(None), _message(_attachments([]))):
            with self.subTest(data=data):
                self.assertIsNone(
                    resolve_inject_credential(
                        self.api, INJECT_ID, data, CredentialType.CLOUD_AWS
                    )
                )

        self.api.inject.resolve_attachment_secret.assert_not_called()

    def test_reference_is_resolved_parsed_and_checked(self):
        resolved = resolve_inject_credential(
            self.api, INJECT_ID, _message(_attachments()), CredentialType.CLOUD_AWS
        )

        self.api.inject.resolve_attachment_secret.assert_called_once_with(
            INJECT_ID, REFERENCE, AUTHORISATION_CODE
        )
        self.assertIsInstance(resolved, AwsAccessKeySecret)
        self.assertEqual(resolved.aws_secret_access_key, SECRET)

    def test_expected_type_can_be_a_provider_name(self):
        resolved = resolve_inject_credential(
            self.api, INJECT_ID, _message(_attachments()), "aws"
        )

        self.assertIsInstance(resolved, AwsAccessKeySecret)

    def test_incompatible_credential(self):
        with self.assertRaises(CredentialResolutionError) as context:
            resolve_inject_credential(
                self.api, INJECT_ID, _message(_attachments()), CredentialType.CLOUD_GCP
            )

        self.assertEqual(
            context.exception.code, CredentialErrorCode.CREDENTIAL_INCOMPATIBLE
        )
        self.assertEqual(context.exception.reference, REFERENCE)

    def test_missing_authorisation_code_sends_no_resolution_request(self):
        with self.assertRaises(CredentialResolutionError):
            resolve_inject_credential(
                self.api,
                INJECT_ID,
                _message(_attachments(authorisation_code=None)),
                CredentialType.CLOUD_AWS,
            )

        self.api.inject.resolve_attachment_secret.assert_not_called()

    def test_platform_error_is_propagated(self):
        self.api.inject.resolve_attachment_secret.side_effect = (
            CredentialResolutionError(
                CredentialErrorCode.CREDENTIAL_INACTIVE, REFERENCE, 400
            )
        )

        with self.assertRaises(CredentialResolutionError) as context:
            resolve_inject_credential(
                self.api, INJECT_ID, _message(_attachments()), CredentialType.CLOUD_AWS
            )

        self.assertEqual(
            context.exception.code, CredentialErrorCode.CREDENTIAL_INACTIVE
        )

    def test_end_to_end_with_the_openaev_client(self):
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(AWS_PAYLOAD).encode()
        response.headers["Content-Type"] = "application/json"
        api = OpenAEV("url", "token")

        with mock.patch(
            "requests.Session.request", return_value=response
        ) as mock_request:
            resolved = resolve_inject_credential(
                api, INJECT_ID, _message(_attachments()), CredentialType.CLOUD_AWS
            )

        call = mock_request.call_args.kwargs
        self.assertEqual(call["url"], f"url/api/injects/{INJECT_ID}/attachment/secret")
        self.assertEqual(
            call["json"],
            {"attachment_id": REFERENCE, "authorisation": AUTHORISATION_CODE},
        )
        self.assertEqual(resolved.aws_access_key_id, "AKIAEXAMPLE")


if __name__ == "__main__":
    unittest.main()
