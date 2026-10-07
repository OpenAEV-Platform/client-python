"""Errors raised when an injector resolves a credential reference.

The platform resolution endpoint answers with a closed set of error codes.
Each code carries a fixed, human-readable message meant to be reported as is
in the inject execution trace. Messages only ever mention the credential
reference id, never a secret value, and the raw HTTP request and response
bodies are deliberately never kept on the error.
"""

from enum import Enum
from typing import Optional

from pyoaev.exceptions import OpenAEVError


class CredentialErrorCode(str, Enum):
    CREDENTIAL_NOT_FOUND = "CREDENTIAL_NOT_FOUND"
    CREDENTIAL_INACTIVE = "CREDENTIAL_INACTIVE"
    CREDENTIAL_ACCESS_DENIED = "CREDENTIAL_ACCESS_DENIED"


_CREDENTIAL_ERROR_MESSAGES = {
    CredentialErrorCode.CREDENTIAL_NOT_FOUND: (
        "The credential configured on this inject ({reference}) no longer exists "
        "at the moment of execution. Select an existing credential on the inject, "
        "then run it again."
    ),
    CredentialErrorCode.CREDENTIAL_INACTIVE: (
        "The credential {reference} is inactive at the moment of execution. "
        "Update or replace this credential, then run the inject again."
    ),
    CredentialErrorCode.CREDENTIAL_ACCESS_DENIED: (
        "This execution is not entitled to use the credential configured on this "
        "inject. Contact your Cloud platform administrator"
    ),
}


def credential_error_code_from_http(
    response_code: Optional[int], error_message: Optional[str]
) -> CredentialErrorCode:
    """Map a failed resolution call to its credential error code.

    The code sent by the platform in the response ``message`` wins. A 404
    without a known code (the inject itself does not exist) is reported as
    ``CREDENTIAL_NOT_FOUND``. Any other failure falls back to
    ``CREDENTIAL_ACCESS_DENIED`` so that nothing about the credential leaks.
    """
    if error_message:
        try:
            return CredentialErrorCode(error_message.strip())
        except ValueError:
            pass
    if response_code == 404:
        return CredentialErrorCode.CREDENTIAL_NOT_FOUND
    return CredentialErrorCode.CREDENTIAL_ACCESS_DENIED


class CredentialResolutionError(OpenAEVError):
    """A credential reference could not be resolved for the current execution.

    ``message`` holds the fixed human-readable message of ``code``. The HTTP
    response body is never stored, so it cannot surface in ``str()``.
    """

    def __init__(
        self,
        code: CredentialErrorCode,
        reference: Optional[str] = None,
        response_code: Optional[int] = None,
    ) -> None:
        self.code = CredentialErrorCode(code)
        self.reference = reference
        message = _CREDENTIAL_ERROR_MESSAGES[self.code].format(
            reference=reference or "unknown reference"
        )
        super().__init__(
            error_message=message, response_code=response_code, response_body=None
        )

    @property
    def message(self) -> str:
        return self.error_message

    def __str__(self) -> str:
        return f"{self.code.value}: {self.error_message}"


__all__ = [
    "CredentialErrorCode",
    "CredentialResolutionError",
    "credential_error_code_from_http",
]
