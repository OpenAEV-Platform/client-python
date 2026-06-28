"""Deterministic per-inject canary marker shared by the AI red-team injector and the AI defense
collectors.

The marker is derived purely from the inject (and optional agent) id, so the injector that sends the
attack and the collector that validates an AI defense response compute the same value independently,
without the platform having to store it. It is emitted by the injector (request header + in-prompt
token) and matched by collectors against guardrail / firewall logs.
"""

import hashlib


def build_marker(inject_id: str, agent_id: str = "") -> str:
    seed = f"{inject_id}:{agent_id}".encode("utf-8")
    return "oaev" + hashlib.sha256(seed).hexdigest()[:16]
