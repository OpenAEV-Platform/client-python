"""Errors raised when an injector resolves a credential reference.

The platform resolution endpoint answers with a closed set of error codes.
``CREDENTIAL_INCOMPATIBLE`` is detected by the injector itself, when the
resolved credential does not satisfy the contract field. Each code carries a fixed, human-readable message meant to be reported as is
in the inject execution trace. Messages only ever mention the credential
reference id, never a secret value, and the raw HTTP request and response
bodies are deliberately never kept on the error.
"""

from enum import Enum
from typing import Optional

from pyoaev.credential.types import CredentialType
from pyoaev.exceptions import OpenAEVError


class CredentialErrorCode(str, Enum):
    CREDENTIAL_NOT_FOUND = "CREDENTIAL_NOT_FOUND"
    CREDENTIAL_INACTIVE = "CREDENTIAL_INACTIVE"
    CREDENTIAL_ACCESS_DENIED = "CREDENTIAL_ACCESS_DENIED"
    CREDENTIAL_INCOMPATIBLE = "CREDENTIAL_INCOMPATIBLE"


_PLATFORM_CREDENTIAL_ERROR_CODES = {
    CredentialErrorCode.CREDENTIAL_NOT_FOUND,
    CredentialErrorCode.CREDENTIAL_INACTIVE,
    CredentialErrorCode.CREDENTIAL_ACCESS_DENIED,
}


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
    CredentialErrorCode.CREDENTIAL_INCOMPATIBLE: (
        "The credential {reference} is not compatible with this inject. Select a "
        "credential of type {type} on the inject, then run it again."
    ),
}

# Used when the expected credential type is not known where the error is raised
# (for example an unknown secret type returned by the platform).
_CREDENTIAL_INCOMPATIBLE_UNKNOWN_TYPE_MESSAGE = (
    "The credential {reference} is not compatible with this inject. Select a "
    "credential of the type expected by the inject, then run it again."
)


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
            code = CredentialErrorCode(error_message.strip())
        except ValueError:
            code = None
        if code in _PLATFORM_CREDENTIAL_ERROR_CODES:
            return code
    if response_code == 404:
        return CredentialErrorCode.CREDENTIAL_NOT_FOUND
    return CredentialErrorCode.CREDENTIAL_ACCESS_DENIED


class CredentialResolutionError(OpenAEVError):
    """A credential reference could not be resolved for the current execution.

    ``message`` holds the fixed human-readable message of ``code``. The HTTP
    response body is never stored, so it cannot surface in ``str()``.
    ``expected_type`` is the credential type the inject expects, only used by
    the ``CREDENTIAL_INCOMPATIBLE`` message.
    """

    def __init__(
        self,
        code: CredentialErrorCode,
        reference: Optional[str] = None,
        response_code: Optional[int] = None,
        expected_type: Optional[CredentialType] = None,
    ) -> None:
        self.code = CredentialErrorCode(code)
        self.reference = reference
        self.expected_type = (
            CredentialType(expected_type) if expected_type is not None else None
        )
        template = _CREDENTIAL_ERROR_MESSAGES[self.code]
        if (
            self.code == CredentialErrorCode.CREDENTIAL_INCOMPATIBLE
            and self.expected_type is None
        ):
            template = _CREDENTIAL_INCOMPATIBLE_UNKNOWN_TYPE_MESSAGE
        message = template.format(
            reference=reference or "unknown reference",
            type=self.expected_type.value if self.expected_type else None,
        )
        super().__init__(
            error_message=message, response_code=response_code, response_body=None
        )

    @property
    def message(self) -> str:
        return self.error_message

    def __str__(self) -> str:
        return f"{self.code.value}: {self.error_message}"


class UnsupportedSecretTypeError(CredentialResolutionError):
    """The platform resolved a secret type this client does not know."""

    def __init__(
        self, secret_type: Optional[str] = None, reference: Optional[str] = None
    ) -> None:
        self.secret_type = secret_type
        super().__init__(CredentialErrorCode.CREDENTIAL_INCOMPATIBLE, reference)


class InvalidResolvedSecretError(CredentialResolutionError):
    """The resolved secret payload does not match its declared type.

    Reported as ``CREDENTIAL_ACCESS_DENIED``, like any unexpected failure, so
    that nothing about the payload leaks in the trace.
    """

    def __init__(self, reference: Optional[str] = None) -> None:
        super().__init__(CredentialErrorCode.CREDENTIAL_ACCESS_DENIED, reference)


__all__ = [
    "CredentialErrorCode",
    "CredentialResolutionError",
    "InvalidResolvedSecretError",
    "UnsupportedSecretTypeError",
    "credential_error_code_from_http",
]
