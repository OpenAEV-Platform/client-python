"""Heartbeat: keep a daemon registered on the platform."""

import threading
from typing import Any

__all__ = ["Heartbeat"]


class Heartbeat:
    """Implements ``HeartbeatPort``."""

    def tenant_of(self, api: Any) -> Any:
        return getattr(api, "tenant_id", None)

    def tenant_meta(self, tenant_id: Any) -> dict[str, Any]:
        return {"tenant_id": str(tenant_id) if tenant_id else None}

    def ping(
        self,
        api: Any,
        config: Any,
        ping_type: str,
        logger: Any,
        exit_event: threading.Event,
    ) -> None:
        while not exit_event.is_set():
            try:
                if ping_type == "injector":
                    api.injector.create(config, False)
                else:
                    api.collector.create(config, False)
            except Exception as err:  # pylint: disable=broad-except
                logger.error("Error pinging the API: " + str(err))
            exit_event.wait(40)
