"""Daemon adapters: the base daemon runtime and its heartbeat.

Each adapter speaks the daemons seam types and delegates to the core
implementation of its port. The API client is injected (``BaseClient``).
"""

import threading
from abc import ABC, abstractmethod

from xtm_oaev_sdk._core.daemons import DaemonRuntime, Heartbeat
from xtm_oaev_sdk.public.common import logger
from xtm_oaev_sdk.public.configuration import Configuration
from xtm_oaev_sdk.seam.common import BaseClient
from xtm_oaev_sdk.seam.daemons import DaemonRuntimePort, HeartbeatPort

__all__ = ["BaseDaemon", "PingAlive"]

_runtime: DaemonRuntimePort = DaemonRuntime()
_heartbeat: HeartbeatPort = Heartbeat()


class BaseDaemon(ABC):
    """A base class for implementing a kind of daemon that periodically polls
    a given callback.

    :param configuration: configuration to provide the daemon
        (allowing for looking up values within the callback for example)
    :type configuration: Configuration
    :param callback: a method or function to periodically call, defaults to None.
    :type callback: callable, optional
    :param logger: a logger object, to log events. if not supplied, a default logger
        will be spawned to provide this functionality.
    :type logger: Any
    :param api_client: an API client that will provide connectivity with other systems,
        conforming to the ``BaseClient`` protocol. When omitted, the client is built by
        ``_create_default_api_client()``, which the SDK cannot do on its own: it never
        depends on a concrete client. Inject one, or override the hook.
    :type api_client: BaseClient, optional
    """

    def __init__(
        self,
        configuration: Configuration,
        callback: callable = None,
        logger=None,
        api_client: BaseClient | None = None,
    ):
        self._configuration = configuration
        self._callback = callback
        self.api = api_client or self._create_default_api_client()

        # logging
        # compatibility layer: in order for older configs to still work, search for legacy names
        actual_log_level = _runtime.resolve_log_level(self._configuration)
        actual_log_name = _runtime.resolve_name(self._configuration)
        self.logger = logger or BaseDaemon.__get_default_logger(
            actual_log_level.upper(),
            actual_log_name,
        )

    @abstractmethod
    def _setup(self):
        """A run-once method that inheritors must implement. This serves to instantiate
        all useful objects and functionality for the implementor to run.
        """
        pass

    @abstractmethod
    def _start_loop(self):
        """Starts the daemon's main execution loop. Implementors should implement
        the main execution logic in here.
        """
        pass

    def _try_callback(self):
        """Tries to call the configured callback. Note that if any error is thrown,
        it is immediately swallowed (but still logged) allowing the collector to keep
        running. This is useful for any transient issue (e.g. API endpoint down...).
        """
        _runtime.invoke_callback(self._callback, self, self.logger)

    def start(self):
        """Start the daemon. This will run the implementor's run-once setup method and
        follow-up with the main execution loop. Note that at this point, if there is no
        configured callback, the method will abort and kill the daemon.
        """
        if _runtime.dump_config_schema_requested():
            _runtime.dump_config_schema(self._configuration)
            return

        _runtime.ensure_callback(self._callback)
        self._setup()
        self._start_loop()

    def set_callback(self, callback: callable):
        """Configures a callback to call in the main execution loop. If the callback
        was not provided in the daemon's ctor, this should be set before calling start().
        """
        self._callback = callback

    def get_id(self):
        """Returns the daemon instance's ID contained in configuration. Configuration
        must define any of these keys: `id`, `collector_id`, `injector_id`.
        """
        return _runtime.resolve_id(self._configuration)

    def _create_default_api_client(self) -> BaseClient:
        """Builds the API client used when none was injected. The SDK has no
        concrete client to build: client libraries override this hook (e.g. to
        construct one from the ``openaev_url``, ``openaev_token`` and
        ``openaev_tenant_id`` configuration keys).
        """
        return _runtime.default_api_client()

    @classmethod
    def __get_default_logger(cls, log_level, name):
        return logger(log_level)(name)


class PingAlive(threading.Thread):
    """Heartbeat thread keeping a daemon registered on the platform."""

    def __init__(self, api, config, logger, ping_type) -> None:
        threading.Thread.__init__(self)
        self.ping_type = ping_type
        self.api = api
        self.tenant_id = _heartbeat.tenant_of(self.api)
        self.config = config
        self.logger = logger
        self.in_error = False
        self.exit_event = threading.Event()

    def ping(self) -> None:
        _heartbeat.ping(
            self.api, self.config, self.ping_type, self.logger, self.exit_event
        )

    def run(self) -> None:
        self.logger.info(
            "Starting PingAlive thread", _heartbeat.tenant_meta(self.tenant_id)
        )
        self.ping()

    def stop(self) -> None:
        self.logger.info(
            "Preparing PingAlive for clean shutdown",
            _heartbeat.tenant_meta(self.tenant_id),
        )
        self.exit_event.set()
