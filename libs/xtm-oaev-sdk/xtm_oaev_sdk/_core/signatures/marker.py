"""AI marker: deterministic per-inject canary shared by the AI red-team injector
and the AI defense collectors."""

import hashlib

__all__ = ["MarkerBuilder"]


class MarkerBuilder:
    """Implements ``MarkerPort``."""

    def build_marker(self, inject_id: str, agent_id: str = "") -> str:
        seed = f"{inject_id}:{agent_id}".encode("utf-8")
        return "oaev" + hashlib.sha256(seed).hexdigest()[:16]
