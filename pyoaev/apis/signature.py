"""Signature callback API — transport layer for compiled signature payloads."""

import json
import logging
import time
from typing import Any

from pydantic import ValidationError

from pyoaev import exceptions as exc
from pyoaev.base import RESTManager, RESTObject
from pyoaev.exceptions import SignatureTransmissionError
from pyoaev.signatures.models import SignatureCallbackPayload


class Signature(RESTObject):
    """REST object placeholder for signature callback responses."""

    _id_attr = None


class SignatureApiManager(RESTManager):
    """Manage signature callback transport to the OpenAEV backend.

    Handles payload validation, auto-chunking, and retry with exponential backoff.
    """

    _path = "/injects"
    _obj_cls = Signature

    DEFAULT_MAX_PAYLOAD_SIZE = 1_048_576  # 1 MiB
    MAX_RETRIES = 3
    RETRY_DELAYS = (1, 2, 4)

    _CHUNK_METADATA_RESERVE = len(
        ',"chunk_index":99999,"total_chunks":99999,"phase":"execution_complete_extended"'
    )

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
        phase: str,
        signatures: dict[str, Any],
    ) -> None:
        """Send compiled signatures to the inject callback endpoint.

        Auto-chunks payloads exceeding max_payload_size and retries on 5xx errors.

        Args:
            inject_id: Inject UUID.
            phase: Execution phase (e.g. 'execution_complete').
            signatures: Full signatures dict (canonical or flat, grouped on the fly).

        Raises:
            SignatureTransmissionError: Validation failed, 4xx hit, or retries exhausted.
        """
        self._logger.debug("send_signatures inject_id=%s phase=%s", inject_id, phase)
        signatures = self._normalize_signature_payload(signatures)
        payload = self._build_callback_payload(signatures, phase=phase)

        serialized = json.dumps(payload, separators=(",", ":")).encode()

        if len(serialized) <= self._max_payload_size:
            self._send_with_retry(inject_id, payload)
        else:
            self._send_chunked(inject_id, payload["expectation_signature"], phase=phase)

    def _build_callback_payload(
        self,
        signatures: dict[str, Any],
        *,
        phase: str | None = None,
        chunk_index: int | None = None,
        total_chunks: int | None = None,
    ) -> dict[str, Any]:
        """Validate and wrap signatures in the strict callback envelope.

        Args:
            signatures: The inner signatures body, already normalised.
            phase: Execution phase string (e.g. 'execution_complete').
            chunk_index: 0-based index when chunking, None for single POSTs.
            total_chunks: Chunk count when chunking, None for single POSTs.

        Returns:
            The validated dict ready for wire transmission.

        Raises:
            SignatureTransmissionError: Envelope failed Pydantic validation.
        """
        try:
            envelope = SignatureCallbackPayload.model_validate(
                {
                    "expectation_signature": signatures,
                    "phase": phase,
                    "chunk_index": chunk_index,
                    "total_chunks": total_chunks,
                }
            )
        except ValidationError as ve:
            raise SignatureTransmissionError(
                error_message=f"Invalid signatures payload: {ve}",
            ) from ve
        return envelope.model_dump(mode="json", exclude_none=True)

    def _normalize_signature_payload(
        self, signatures: dict[str, Any]
    ) -> dict[str, Any]:
        """Regroup signature_values by expectation_type within each target.

        Accepts flat or pre-grouped input and returns canonical grouped form.

        Args:
            signatures: Raw signatures dict with any mix of flat and grouped entries.

        Returns:
            New dict where every signature_values list is in canonical grouped form.
        """
        targets = signatures.get("targets")
        if not targets:
            return signatures

        normalized_targets: list[dict[str, Any]] = []
        for target in targets:
            sig_values = target.get("signature_values")
            if not sig_values:
                normalized_targets.append(target)
                continue

            grouped: dict[str, list[dict[str, Any]]] = {}
            order: list[str] = []

            for entry in sig_values:
                etype = entry.get("expectation_type")
                if etype not in grouped:
                    grouped[etype] = []
                    order.append(etype)

                if "values" in entry and isinstance(entry["values"], list):
                    grouped[etype].extend(entry["values"])
                else:
                    grouped[etype].append(
                        {k: v for k, v in entry.items() if k != "expectation_type"}
                    )

            normalized_target = dict(target)
            normalized_target["signature_values"] = [
                {"expectation_type": etype, "values": grouped[etype]} for etype in order
            ]
            normalized_targets.append(normalized_target)

        normalized = dict(signatures)
        normalized["targets"] = normalized_targets
        return normalized

    def _send_chunked(
        self, inject_id: str, signatures: dict[str, Any], phase: str | None = None
    ) -> None:
        """Split targets across sequential POSTs, each tagged with chunk metadata.

        Args:
            inject_id: Inject UUID for the callback path.
            signatures: Normalised inner signatures body to partition.
            phase: Execution phase forwarded to each chunk envelope.

        Raises:
            SignatureTransmissionError: A single target alone exceeds max_payload_size.
        """
        targets = signatures.get("targets", [])
        if not targets:
            payload = self._build_callback_payload(signatures, phase=phase)
            size = len(json.dumps(payload, separators=(",", ":")).encode())
            if size > self._max_payload_size:
                self._logger.warning(
                    "Payload of %d bytes exceeds max_payload_size %d but has no "
                    "'targets' key to chunk on; sending unchunked",
                    size,
                    self._max_payload_size,
                )
            self._send_with_retry(inject_id, payload)
            return

        budget = max(self._max_payload_size - self._CHUNK_METADATA_RESERVE, 0)
        chunks: list[list[Any]] = []
        current_chunk: list[Any] = []

        for target in targets:
            candidate = current_chunk + [target]
            size = len(
                json.dumps(
                    {"expectation_signature": {"targets": candidate}},
                    separators=(",", ":"),
                ).encode()
            )

            if size <= budget:
                current_chunk.append(target)
                continue

            if not current_chunk:
                raise SignatureTransmissionError(
                    error_message=(
                        f"Single target payload of {size} bytes exceeds "
                        f"max_payload_size {self._max_payload_size}; cannot chunk further"
                    ),
                )

            chunks.append(current_chunk)
            current_chunk = [target]
            solo_size = len(
                json.dumps(
                    {"expectation_signature": {"targets": [target]}},
                    separators=(",", ":"),
                ).encode()
            )
            if solo_size > budget:
                raise SignatureTransmissionError(
                    error_message=(
                        f"Single target payload of {solo_size} bytes exceeds "
                        f"max_payload_size {self._max_payload_size}; cannot chunk further"
                    ),
                )

        if current_chunk:
            chunks.append(current_chunk)

        total_chunks = len(chunks)
        for idx, chunk_targets in enumerate(chunks):
            chunk_payload = self._build_callback_payload(
                {"targets": chunk_targets},
                phase=phase,
                chunk_index=idx,
                total_chunks=total_chunks,
            )
            self._send_with_retry(inject_id, chunk_payload)

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
        path = f"{self.path}/{inject_id}/callback"
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
