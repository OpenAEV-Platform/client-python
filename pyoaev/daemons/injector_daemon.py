from pyoaev.daemons import BaseDaemon
from pyoaev.utils import PingAlive
from xtm_oaev_sdk import Configuration


class InjectorDaemon(BaseDaemon):
    """Implementation of a daemon of Injector type. Uses a RabbitMQ
    message queue (ListenQueue) instead of a polling scheduler.

    Requires specific configuration keys to run its setup:
    ``injector_id``: unique identifier for the injector (UUIDv4)
    ``injector_name``: human-readable injector name
    ``injector_type``: type identifier used for icon naming and platform registration
    ``injector_contracts``: contracts the injector supports
    ``injector_icon_filepath``: relative path to an icon image (PNG);
        ignored when an ``icon`` file handle is passed to the constructor.
    """

    def __init__(
        self,
        configuration: Configuration,
        callback: callable = None,
        logger=None,
        api_client=None,
        icon=None,
    ):
        super().__init__(configuration, callback, logger, api_client)
        # icon can be a file handle (legacy bridge) or None (read from config)
        self._icon = icon
        self.config: dict = {}
        self.injector_config = None
        self.ping = None
        self.listen_queue = None

    def _setup(self):
        self.config = {
            k: v
            for k, v in {
                "injector_id": self._configuration.get("injector_id"),
                "injector_name": self._configuration.get("injector_name"),
                "injector_type": self._configuration.get("injector_type"),
                "injector_contracts": self._configuration.get("injector_contracts"),
                "injector_custom_contracts": self._configuration.get(
                    "injector_custom_contracts"
                ),
                "injector_category": self._configuration.get("injector_category"),
                "injector_executor_commands": self._configuration.get(
                    "injector_executor_commands"
                ),
                "injector_executor_clear_commands": self._configuration.get(
                    "injector_executor_clear_commands"
                ),
            }.items()
            if v is not None
        }

        icon_name = self._configuration.get("injector_type") + ".png"

        if self._icon is not None:
            # Legacy bridge: file handle passed directly
            injector_icon = (icon_name, self._icon, "image/png")
        else:
            # New path: read icon from configuration filepath
            icon_path = self._configuration.get("injector_icon_filepath")
            self._icon = open(icon_path, "rb")  # noqa: SIM115
            injector_icon = (icon_name, self._icon, "image/png")

        self.injector_config = self.api.injector.create(self.config, injector_icon)

        self.ping = PingAlive(self.api, self.config, self.logger, "injector")
        self.ping.start()

    def _start_loop(self):
        from pyoaev.helpers import ListenQueue  # lazy to avoid circular import

        self.listen_queue = ListenQueue(
            self.config, self.injector_config, self.logger, self._callback
        )
        self.listen_queue.start()
