"""Truthiness: the strings signalling a boolean configuration value."""

__all__ = ["Truthiness"]


class Truthiness:
    """Implements ``TruthinessPort``."""

    def is_truthy(self, value: str) -> bool:
        return value.lower() in ["yes", "true"]

    def is_falsy(self, value: str) -> bool:
        return value.lower() in ["no", "false"]
