"""Defines signature match result objects.

This module provides the `SignatureMatch` class, which stores the selected
match type and its optional score.
"""

from xtm_oaev_sdk.engine.errors import OpenAEVError
from xtm_oaev_sdk.engine.signatures.types import MatchTypes

__all__ = ["SignatureMatch"]


class SignatureMatch:
    """Represents a signature matching outcome.

    Args:
        match_type: The matching strategy/result type.
        match_score: Optional score produced by matching.

    Raises:
        OpenAEVError: If `match_score` is not provided for non-simple match
            types.
    """

    def __init__(self, match_type: MatchTypes, match_score: int | None):
        if match_score is None and match_type != MatchTypes.MATCH_TYPE_SIMPLE:
            raise OpenAEVError(
                f"Match type {match_type} requires score to be set, found score = {match_score}"
            )
        self.match_type = match_type
        self.match_score = match_score
