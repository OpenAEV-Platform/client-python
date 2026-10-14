"""Heartbeat thread keeping a daemon registered on the platform."""

import threading

__all__ = ["PingAlive"]


class PingAlive(threading.Thread):
    def __init__(self, api, config, logger, ping_type) -> None:
        threading.Thread.__init__(self)
        self.ping_type = ping_type
        self.api = api
        self.tenant_id = getattr(self.api, "tenant_id", None)
        self.config = config
        self.logger = logger
        self.in_error = False
        self.exit_event = threading.Event()

    def ping(self) -> None:
        while not self.exit_event.is_set():
            try:
                if self.ping_type == "injector":
                    self.api.injector.create(self.config, False)
                else:
                    self.api.collector.create(self.config, False)
            except Exception as err:  # pylint: disable=broad-except
                self.logger.error("Error pinging the API: " + str(err))
            self.exit_event.wait(40)

    def run(self) -> None:
        self.logger.info(
            "Starting PingAlive thread",
            {"tenant_id": str(self.tenant_id) if self.tenant_id else None},
        )
        self.ping()

    def stop(self) -> None:
        self.logger.info(
            "Preparing PingAlive for clean shutdown",
            {"tenant_id": str(self.tenant_id) if self.tenant_id else None},
        )
        self.exit_event.set()
