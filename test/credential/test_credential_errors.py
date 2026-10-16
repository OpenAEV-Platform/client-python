import unittest

from pyoaev.credential import (
    CredentialErrorCode,
    CredentialResolutionError,
    CredentialType,
    credential_error_code_from_http,
    credential_error_guidance,
    credential_error_summary,
)
from pyoaev.exceptions import OpenAEVError


class CredentialErrorCodeTest(unittest.TestCase):
    def test_codes_are_a_closed_set(self):
        self.assertEqual(
            {code.value for code in CredentialErrorCode},
            {
                "CREDENTIAL_NOT_FOUND",
                "CREDENTIAL_INACTIVE",
                "CREDENTIAL_ACCESS_DENIED",
                "CREDENTIAL_INCOMPATIBLE",
                "CREDENTIAL_RESOLUTION_UNAVAILABLE",
            },
        )

    def test_injector_side_code_is_never_taken_from_the_platform(self):
        self.assertEqual(
            credential_error_code_from_http(400, "CREDENTIAL_INCOMPATIBLE"),
            CredentialErrorCode.CREDENTIAL_ACCESS_DENIED,
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
            (None, None),
        ):
            with self.subTest(response_code=response_code, message=message):
                self.assertEqual(
                    credential_error_code_from_http(response_code, message),
                    CredentialErrorCode.CREDENTIAL_ACCESS_DENIED,
                )

    def test_server_error_is_resolution_unavailable(self):
        for response_code in (500, 502, 503, 504):
            with self.subTest(response_code=response_code):
                self.assertEqual(
                    credential_error_code_from_http(response_code, "boom"),
                    CredentialErrorCode.CREDENTIAL_RESOLUTION_UNAVAILABLE,
                )

    def test_platform_code_wins_over_server_error(self):
        self.assertEqual(
            credential_error_code_from_http(500, "CREDENTIAL_INACTIVE"),
            CredentialErrorCode.CREDENTIAL_INACTIVE,
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

    def test_incompatible_message_identifies_the_expected_type(self):
        error = CredentialResolutionError(
            CredentialErrorCode.CREDENTIAL_INCOMPATIBLE,
            reference="ref-1",
            expected_type=CredentialType.CLOUD_AWS,
        )

        self.assertIs(error.expected_type, CredentialType.CLOUD_AWS)
        self.assertEqual(
            error.message,
            "The credential ref-1 is not compatible with this inject. Select a "
            "credential of type CLOUD_AWS on the inject, then run it again.",
        )

    def test_incompatible_message_without_expected_type(self):
        error = CredentialResolutionError(
            CredentialErrorCode.CREDENTIAL_INCOMPATIBLE, reference="ref-1"
        )

        self.assertIsNone(error.expected_type)
        self.assertEqual(
            error.message,
            "The credential ref-1 is not compatible with this inject. Select a "
            "credential of the type expected by the inject, then run it again.",
        )

    def test_expected_type_is_ignored_by_other_codes(self):
        error = CredentialResolutionError(
            CredentialErrorCode.CREDENTIAL_INACTIVE,
            reference="ref-1",
            expected_type=CredentialType.CLOUD_AWS,
        )

        self.assertNotIn("CLOUD_AWS", error.message)

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


class CredentialErrorMessagePartsTest(unittest.TestCase):
    def test_message_is_summary_then_guidance_for_every_code(self):
        for code in CredentialErrorCode:
            with self.subTest(code=code):
                error = CredentialResolutionError(code, reference="ref-1")

                self.assertEqual(error.message, f"{error.summary} {error.guidance}")
                self.assertEqual(error.summary, credential_error_summary(code, "ref-1"))
                self.assertEqual(error.guidance, credential_error_guidance(code))

    def test_not_found_message_is_unchanged(self):
        error = CredentialResolutionError(
            CredentialErrorCode.CREDENTIAL_NOT_FOUND, reference="ref-1"
        )

        self.assertEqual(
            error.message,
            "The credential configured on this inject (ref-1) no longer exists at "
            "the moment of execution. Select an existing credential on the inject, "
            "then run it again.",
        )

    def test_incompatible_guidance_names_the_expected_type(self):
        self.assertEqual(
            credential_error_guidance(
                CredentialErrorCode.CREDENTIAL_INCOMPATIBLE, CredentialType.CLOUD_GCP
            ),
            "Select a credential of type CLOUD_GCP on the inject, then run it again.",
        )

    def test_summary_without_reference_uses_the_sentinel(self):
        self.assertIn(
            "unknown reference",
            credential_error_summary(CredentialErrorCode.CREDENTIAL_INACTIVE),
        )

    def test_resolution_unavailable_mentions_the_platform(self):
        error = CredentialResolutionError(
            CredentialErrorCode.CREDENTIAL_RESOLUTION_UNAVAILABLE, reference="ref-1"
        )

        self.assertIn("ref-1", error.message)
        self.assertIn("platform", error.message)


if __name__ == "__main__":
    unittest.main()
