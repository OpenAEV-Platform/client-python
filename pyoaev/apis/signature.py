"""Signature callback API — transport layer for compiled signature payloads."""

import logging
import time
from typing import Any

from pydantic import ValidationError

from pyoaev import exceptions as exc
from pyoaev.base import RESTManager, RESTObject
from pyoaev.exceptions import SignatureTransmissionError
from pyoaev.signatures.models import (
    ExecutionDetails,
    SignatureCallbackPayload,
    SignatureOutputStructure,
)


class Signature(RESTObject):
    """REST object placeholder for signature callback responses."""

    _id_attr = None


class SignatureApiManager(RESTManager):
    """Manage signature callback transport to the OpenAEV backend.

    Handles payload validation and retry with exponential backoff.
    """

    _path = "/injects"
    _obj_cls = Signature

    DEFAULT_MAX_PAYLOAD_SIZE = 1_048_576  # 1 MiB
    MAX_RETRIES = 3
    RETRY_DELAYS = (1, 2, 4)

    def __init__(self, openaev: "Any", parent: "Any" = None) -> None:
        """Initialize the signature API manager.

        Args:
            openaev: The OpenAEV client instance.
            parent: Optional parent REST object for nested managers.
        """
        super().__init__(openaev, parent)
        self._max_payload_size = self.DEFAULT_MAX_PAYLOAD_SIZE
        self._logger = logging.getLogger(__name__)

    @property
    def max_payload_size(self) -> int:
        """Maximum payload size in bytes before auto-chunking triggers."""
        return self._max_payload_size

    @max_payload_size.setter
    def max_payload_size(self, value: int) -> None:
        self._max_payload_size = value

    @property
    def logger(self) -> logging.Logger:
        """Logger instance used for transmission diagnostics."""
        return self._logger

    @logger.setter
    def logger(self, value: logging.Logger) -> None:
        self._logger = value

    def send_signatures(
        self,
        inject_id: str,
        signatures: SignatureOutputStructure,
        execution_details: ExecutionDetails,
    ) -> None:
        """Send compiled signatures to the inject callback endpoint.

        Auto-chunks payloads exceeding max_payload_size and retries on 5xx errors.

        Args:
            inject_id: Inject UUID.
            signatures: Full signatures dict (canonical or flat, grouped on the fly).
            execution_details:

        Raises:
            SignatureTransmissionError: Validation failed, 4xx hit, or retries exhausted.
        """
        self._logger.debug(
            "send_signatures inject_id=%s, execution_status=%s, execution_action=%s",
            inject_id,
            execution_details.execution_status,
            execution_details.execution_action,
        )
        signatures = signatures.normalize_signature_payload()
        payload = self._build_callback_payload(
            signatures=signatures, execution_details=execution_details
        )

        self._send_with_retry(inject_id, payload)

    def _build_callback_payload(
        self,
        signatures: SignatureOutputStructure,
        execution_details: ExecutionDetails,
    ) -> dict[str, Any]:
        """Validate and wrap signatures in the strict callback envelope.

        Args:
            signatures: The inner signatures body, already normalised.
            execution_details: The execution metadata to be stored next to the signatures in the payload.

        Returns:
            The validated dict ready for wire transmission.

        Raises:
            SignatureTransmissionError: Envelope failed Pydantic validation.
        """
        try:
            envelope = SignatureCallbackPayload.build_from_models(
                signatures, execution_details
            )
        except ValidationError as ve:
            raise SignatureTransmissionError(
                error_message=f"Invalid signatures payload: {ve}",
            ) from ve
        return envelope.model_dump(mode="json", exclude_none=True)

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def callback(
        self, inject_id: str, data: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Post signature payload to the inject callback endpoint.

        Args:
            inject_id: Inject UUID.
            data: Validated payload dict to send.
            **kwargs: Additional arguments forwarded to http_post.

        Returns:
            The parsed response from the backend.
        """
        path = f"{self.path}/execution/callback/{inject_id}"
        result = self.openaev.http_post(path, post_data=data, **kwargs)
        return result

    def _send_with_retry(
        self, inject_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Retry callback() with exponential backoff on 5xx, immediate raise on 4xx.

        Args:
            inject_id: Inject UUID for the callback path.
            payload: Validated payload dict to send.

        Returns:
            The successful response from callback().

        Raises:
            SignatureTransmissionError: 4xx error or all retries exhausted.
        """
        from pyoaev.exceptions import OpenAEVError

        last_error: Exception | None = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                return self.callback(inject_id, payload)
            except OpenAEVError as ex:
                status = ex.response_code
                if status and 400 <= status < 500:
                    body_str = ""
                    if ex.response_body:
                        body_str = ex.response_body.decode(errors="replace")
                    self._logger.error(
                        "Client error %d sending signatures: %s",
                        status,
                        body_str or ex.error_message,
                    )
                    raise SignatureTransmissionError(
                        error_message=f"Client error {status}: {ex.error_message}",
                        response_code=status,
                        response_body=ex.response_body,
                    ) from ex

                last_error = ex
                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_DELAYS[attempt]
                    self._logger.warning(
                        "Retry %d/%d after %ds (HTTP %s): %s",
                        attempt + 1,
                        self.MAX_RETRIES,
                        delay,
                        status,
                        ex.error_message,
                    )
                    time.sleep(delay)

        raise SignatureTransmissionError(
            error_message=f"All {self.MAX_RETRIES} retries exhausted",
            response_code=getattr(last_error, "response_code", None),
            response_body=getattr(last_error, "response_body", None),
        )
