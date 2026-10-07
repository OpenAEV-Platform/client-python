"""Read the credential attachment of an inject job and resolve it.

The platform adds an ``attachments`` object to the job message when the inject
carries a credential reference::

    {"credential_references": ["<reference id>"], "authorisation_code": "<code>"}

``attachments`` is ``null`` when the inject has no reference: the injector then
keeps its legacy credential fields and no resolution request is sent.

``resolve_inject_credential`` is the single entry point injectors call.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from pyoaev.credential.errors import CredentialErrorCode, CredentialResolutionError
from pyoaev.credential.resolved import (
    ResolvedSecret,
    ensure_compatible,
    parse_resolved_secret,
)
from pyoaev.credential.types import CredentialType

if TYPE_CHECKING:
    from pyoaev.client import OpenAEV


@dataclass(frozen=True)
class CredentialAttachment:
    reference: str
    # Only valid for the current job, but still a bearer token: keep it out of logs.
    authorisation_code: str = field(repr=False)


def _is_filled_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def get_credential_attachment(data: Dict[str, Any]) -> Optional[CredentialAttachment]:
    """Return the credential attachment of a job message, if any.

    Only the first credential reference is used.

    Returns:
        ``None`` when ``attachments`` is missing, ``null`` or has no reference,
        meaning the injector must use its legacy credential fields.

    Raises:
        CredentialResolutionError: ``CREDENTIAL_ACCESS_DENIED`` when a reference
            is present without an authorisation code, or when the attachment
            is malformed.
    """
    attachments = data.get("attachments")
    if attachments is None:
        return None
    if not isinstance(attachments, dict):
        raise CredentialResolutionError(CredentialErrorCode.CREDENTIAL_ACCESS_DENIED)

    references = attachments.get("credential_references")
    if not references:
        return None
    if not isinstance(references, list) or not _is_filled_string(references[0]):
        raise CredentialResolutionError(CredentialErrorCode.CREDENTIAL_ACCESS_DENIED)
    reference = references[0]

    authorisation_code = attachments.get("authorisation_code")
    if not _is_filled_string(authorisation_code):
        raise CredentialResolutionError(
            CredentialErrorCode.CREDENTIAL_ACCESS_DENIED, reference
        )
    return CredentialAttachment(reference, authorisation_code)


def resolve_inject_credential(
    api: "OpenAEV",
    inject_id: str,
    data: Dict[str, Any],
    expected_type: Union[CredentialType, str],
) -> Optional[ResolvedSecret]:
    """Resolve the credential attached to an inject job, just in time.

    Must be called after ``execution_reception`` and before
    ``execution_callback``, while the inject is in progress.

    Args:
        api: the OpenAEV client of the injector.
        inject_id: the id of the inject being executed.
        data: the job message received by the injector.
        expected_type: the credential type declared on the contract field,
            or the provider name it was declared from (see ``ensure_compatible``).

    Returns:
        ``None`` when the job carries no credential reference (legacy path),
        otherwise the resolved secret, checked against ``expected_type``.

    Raises:
        CredentialResolutionError: with the code to report in the trace.
    """
    attachment = get_credential_attachment(data)
    if attachment is None:
        return None
    payload = api.inject.resolve_attachment_secret(
        inject_id, attachment.reference, attachment.authorisation_code
    )
    resolved = parse_resolved_secret(payload, reference=attachment.reference)
    return ensure_compatible(resolved, expected_type, reference=attachment.reference)


__all__ = [
    "CredentialAttachment",
    "get_credential_attachment",
    "resolve_inject_credential",
]
