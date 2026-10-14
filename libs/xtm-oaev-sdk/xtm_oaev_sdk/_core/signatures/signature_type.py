"""Signature type model and matching-structure builder.

This module defines ``SignatureType``, which couples a signature label with a
matching policy and can generate helper structures for signature matching.
"""

from typing import Any

from xtm_oaev_sdk._core.signatures.signature_match import SignatureMatch
from xtm_oaev_sdk._core.signatures.types import MatchTypes, SignatureTypes

__all__ = ["SignatureType"]


class SignatureType:
    """Describe a signature type and its matching policy.

    Args:
        label: Type specifier.
        match_type: Matching policy used when trying to match this signature
            type, for example fuzzy or simple.
        match_score: Threshold score used when ``match_type`` is fuzzy.
    """

    def __init__(
        self,
        label: SignatureTypes,
        match_type: MatchTypes = MatchTypes.MATCH_TYPE_SIMPLE,
        match_score: int | None = None,
    ) -> None:
        self.label = label
        self.match_policy = SignatureMatch(match_type, match_score)

    def make_struct_for_matching(self, data: Any) -> dict[str, Any]:
        """Format matching metadata for helper-based signature matching.

        Args:
            data: Arbitrary data, most often a string or numeric primitive.

        Returns:
            A dictionary with matching specifiers containing:
                - ``type``: Matching type string.
                - ``data``: Provided data payload.
                - ``score``: Optional score threshold when configured.
        """
        struct: dict[str, Any] = {
            "type": self.match_policy.match_type.value,
            "data": data,
        }

        if self.match_policy.match_score is not None:
            struct["score"] = self.match_policy.match_score

        return struct
