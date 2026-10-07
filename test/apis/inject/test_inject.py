import json
import logging
from typing import Any, Optional
from unittest import TestCase, main, mock
from uuid import UUID

import requests

from pyoaev import OpenAEV
from pyoaev.credential.errors import CredentialErrorCode, CredentialResolutionError

INJECT_ID = "inject-id"
ATTACHMENT_ID = "credential-reference-id"
AUTHORISATION = "authorisation-code"
TENANT_ID = UUID("2cffad3a-0001-4078-b0e2-ef74274022c3")
SECRET_VALUE = "super-secret-value"


def build_response(
    status_code: int,
    body: Optional[Any] = None,
    reason: str = "",
) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response.reason = reason
    if body is None:
        response._content = b""
    else:
        response._content = json.dumps(body).encode()
        response.headers["Content-Type"] = "application/json"
    return response


class TestResolveAttachmentSecret(TestCase):
    def _resolve(self, response, tenant_id=None):
        api_client = OpenAEV("url", "token", tenant_id=tenant_id)
        with mock.patch(
            "requests.Session.request", return_value=response
        ) as mock_request:
            try:
                result = api_client.inject.resolve_attachment_secret(
                    INJECT_ID, ATTACHMENT_ID, AUTHORISATION
                )
            except CredentialResolutionError as error:
                return mock_request, error
        return mock_request, result

    def _assert_resolution_error(
        self, response, expected_code: CredentialErrorCode
    ) -> CredentialResolutionError:
        _, error = self._resolve(response)

        self.assertIsInstance(error, CredentialResolutionError)
        self.assertEqual(error.code, expected_code)
        return error

    def test_success_returns_resolved_secret(self):
        payload = {
            "type": "AWS_ACCESS_KEY",
            "value": {"aws_access_key_id": "AKIA", "aws_secret_access_key": "s"},
        }

        mock_request, result = self._resolve(build_response(200, payload))

        self.assertEqual(result, payload)
        mock_request.assert_called_once()
        call = mock_request.call_args.kwargs
        self.assertEqual(call["method"], "post")
        self.assertEqual(call["url"], f"url/api/injects/{INJECT_ID}/attachment/secret")
        self.assertEqual(
            call["json"],
            {"attachment_id": ATTACHMENT_ID, "authorisation": AUTHORISATION},
        )

    def test_success_with_tenant_uses_tenant_route(self):
        payload = {"type": "AWS_ACCESS_KEY", "value": {}}

        mock_request, _ = self._resolve(
            build_response(200, payload), tenant_id=TENANT_ID
        )

        self.assertEqual(
            mock_request.call_args.kwargs["url"],
            f"url/api/tenants/{TENANT_ID}/injects/{INJECT_ID}/attachment/secret",
        )

    def test_404_credential_not_found(self):
        error = self._assert_resolution_error(
            build_response(404, {"message": "CREDENTIAL_NOT_FOUND"}, "Not Found"),
            CredentialErrorCode.CREDENTIAL_NOT_FOUND,
        )

        self.assertEqual(error.response_code, 404)
        self.assertEqual(error.reference, ATTACHMENT_ID)
        self.assertIn(ATTACHMENT_ID, error.message)

    def test_400_credential_inactive(self):
        error = self._assert_resolution_error(
            build_response(400, {"message": "CREDENTIAL_INACTIVE"}, "Bad Request"),
            CredentialErrorCode.CREDENTIAL_INACTIVE,
        )

        self.assertIn(ATTACHMENT_ID, error.message)
        self.assertIn("Update or replace this credential", error.message)

    def test_403_credential_access_denied(self):
        error = self._assert_resolution_error(
            build_response(403, {"message": "CREDENTIAL_ACCESS_DENIED"}, "Forbidden"),
            CredentialErrorCode.CREDENTIAL_ACCESS_DENIED,
        )

        self.assertNotIn(ATTACHMENT_ID, error.message)

    def test_404_with_empty_message_is_credential_not_found(self):
        self._assert_resolution_error(
            build_response(404, None, "Not Found"),
            CredentialErrorCode.CREDENTIAL_NOT_FOUND,
        )
        self._assert_resolution_error(
            build_response(404, {"message": ""}, "Not Found"),
            CredentialErrorCode.CREDENTIAL_NOT_FOUND,
        )

    def test_403_without_credential_code_is_access_denied(self):
        self._assert_resolution_error(
            build_response(403, {"message": "Access denied"}, "Forbidden"),
            CredentialErrorCode.CREDENTIAL_ACCESS_DENIED,
        )

    def test_unknown_failures_fall_back_to_access_denied(self):
        for response in (
            build_response(401, {"message": "Unauthorized"}, "Unauthorized"),
            build_response(400, {"message": "attachment_id: must not be blank"}),
            build_response(500, {"message": "boom"}, "Internal Server Error"),
            build_response(502, None, "Bad Gateway"),
        ):
            with self.subTest(status_code=response.status_code):
                self._assert_resolution_error(
                    response, CredentialErrorCode.CREDENTIAL_ACCESS_DENIED
                )

    def test_non_json_success_is_access_denied(self):
        response = requests.Response()
        response.status_code = 200
        response._content = b"not json"
        response.headers["Content-Type"] = "text/plain"

        self._assert_resolution_error(
            response, CredentialErrorCode.CREDENTIAL_ACCESS_DENIED
        )

    def test_network_error_is_access_denied(self):
        api_client = OpenAEV("url", "token")
        with mock.patch(
            "requests.Session.request",
            side_effect=requests.ConnectionError("connection refused"),
        ):
            with self.assertRaises(CredentialResolutionError) as context:
                api_client.inject.resolve_attachment_secret(
                    INJECT_ID, ATTACHMENT_ID, AUTHORISATION
                )

        self.assertEqual(
            context.exception.code, CredentialErrorCode.CREDENTIAL_ACCESS_DENIED
        )

    def test_error_never_exposes_response_body(self):
        body = {"message": "CREDENTIAL_INACTIVE", "detail": SECRET_VALUE}

        error = self._assert_resolution_error(
            build_response(400, body, "Bad Request"),
            CredentialErrorCode.CREDENTIAL_INACTIVE,
        )

        self.assertIsNone(error.response_body)
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)
        self.assertNotIn(SECRET_VALUE, str(error))
        self.assertNotIn(SECRET_VALUE, repr(error))
        self.assertNotIn(AUTHORISATION, str(error))

    def test_request_and_response_bodies_are_never_logged(self):
        payload = {"type": "AWS_ACCESS_KEY", "value": {"secret": SECRET_VALUE}}
        records = []
        handler = logging.Handler(level=logging.DEBUG)
        handler.emit = records.append
        root_logger = logging.getLogger()
        previous_level = root_logger.level
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.DEBUG)
        try:
            self._resolve(build_response(200, payload))
            self._resolve(build_response(403, {"message": SECRET_VALUE}))
        finally:
            root_logger.removeHandler(handler)
            root_logger.setLevel(previous_level)

        for record in records:
            message = record.getMessage()
            self.assertNotIn(SECRET_VALUE, message)
            self.assertNotIn(AUTHORISATION, message)


if __name__ == "__main__":
    main()
