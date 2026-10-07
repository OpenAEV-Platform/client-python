import unittest

from pyoaev.credential import (
    CredentialErrorCode,
    CredentialResolutionError,
    credential_error_code_from_http,
)
from pyoaev.exceptions import OpenAEVError


class CredentialErrorCodeTest(unittest.TestCase):
    def test_codes_are_the_closed_platform_set(self):
        self.assertEqual(
            {code.value for code in CredentialErrorCode},
            {
                "CREDENTIAL_NOT_FOUND",
                "CREDENTIAL_INACTIVE",
                "CREDENTIAL_ACCESS_DENIED",
            },
        )

    def test_platform_code_in_message_wins(self):
        self.assertEqual(
            credential_error_code_from_http(404, "CREDENTIAL_NOT_FOUND"),
            CredentialErrorCode.CREDENTIAL_NOT_FOUND,
        )
        self.assertEqual(
            credential_error_code_from_http(400, "CREDENTIAL_INACTIVE"),
            CredentialErrorCode.CREDENTIAL_INACTIVE,
        )
        self.assertEqual(
            credential_error_code_from_http(403, "CREDENTIAL_ACCESS_DENIED"),
            CredentialErrorCode.CREDENTIAL_ACCESS_DENIED,
        )

    def test_404_without_code_is_not_found(self):
        self.assertEqual(
            credential_error_code_from_http(404, None),
            CredentialErrorCode.CREDENTIAL_NOT_FOUND,
        )
        self.assertEqual(
            credential_error_code_from_http(404, "Not Found"),
            CredentialErrorCode.CREDENTIAL_NOT_FOUND,
        )

    def test_unknown_failure_falls_back_to_access_denied(self):
        for response_code, message in (
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (403, None),
            (500, "boom"),
            (None, None),
        ):
            with self.subTest(response_code=response_code, message=message):
                self.assertEqual(
                    credential_error_code_from_http(response_code, message),
                    CredentialErrorCode.CREDENTIAL_ACCESS_DENIED,
                )


class CredentialResolutionErrorTest(unittest.TestCase):
    def test_not_found_message_identifies_the_reference(self):
        error = CredentialResolutionError(
            CredentialErrorCode.CREDENTIAL_NOT_FOUND, reference="ref-1"
        )

        self.assertEqual(
            error.message,
            "The credential configured on this inject (ref-1) no longer exists at "
            "the moment of execution. Select an existing credential on the inject, "
            "then run it again.",
        )

    def test_inactive_message_identifies_the_reference(self):
        error = CredentialResolutionError(
            CredentialErrorCode.CREDENTIAL_INACTIVE, reference="ref-1"
        )

        self.assertEqual(
            error.message,
            "The credential ref-1 is inactive at the moment of execution. Update or "
            "replace this credential, then run the inject again.",
        )

    def test_access_denied_message_discloses_nothing(self):
        error = CredentialResolutionError(
            CredentialErrorCode.CREDENTIAL_ACCESS_DENIED, reference="ref-1"
        )

        self.assertEqual(
            error.message,
            "This execution is not entitled to use the credential configured on this "
            "inject. Contact your Cloud platform administrator",
        )

    def test_str_carries_the_code_and_the_message(self):
        error = CredentialResolutionError(
            CredentialErrorCode.CREDENTIAL_INACTIVE,
            reference="ref-1",
            response_code=400,
        )

        self.assertEqual(str(error), f"CREDENTIAL_INACTIVE: {error.message}")
        self.assertEqual(error.response_code, 400)
        self.assertIsNone(error.response_body)

    def test_accepts_code_as_string(self):
        error = CredentialResolutionError("CREDENTIAL_INACTIVE", reference="ref-1")

        self.assertIs(error.code, CredentialErrorCode.CREDENTIAL_INACTIVE)

    def test_is_an_openaev_error(self):
        error = CredentialResolutionError(CredentialErrorCode.CREDENTIAL_NOT_FOUND)

        self.assertIsInstance(error, OpenAEVError)


if __name__ == "__main__":
    unittest.main()
