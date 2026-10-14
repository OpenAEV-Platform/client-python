"""DEPRECATED: the daemon helpers moved to :mod:`collectors_sdk`,
:mod:`injectors_sdk` and :mod:`xtm_oaev_sdk`.

Backward-compatibility shim: every legacy name resolves to the *identical* SDK
object and emits a :class:`DeprecationWarning` on access, with two adapters:
``OpenAEVInjectorHelper`` keeps building the ``OpenAEV`` client when none is
injected, and ``OpenAEVCollectorHelper`` (already deprecated) stays here as
legacy glue over the collectors-sdk ``CollectorDaemon``.
"""

import collectors_sdk as _collectors_sdk
import injectors_sdk as _injectors_sdk
import xtm_oaev_sdk as _sdk
from collectors_sdk.seam import detection as _detection
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

from pyoaev import OpenAEV
from pyoaev.daemons.collector_daemon import (
    _COLLECTOR_DAEMON_MESSAGE,
    _ClientCollectorDaemon,
)


class _ClientInjectorHelper(_injectors_sdk.OpenAEVInjectorHelper):
    """injectors-sdk OpenAEVInjectorHelper building an OpenAEV client when none
    is injected."""

    def _create_default_api_client(self, config) -> OpenAEV:
        return OpenAEV(
            url=config.get_conf("openaev_url"),
            token=config.get_conf("openaev_token"),
            tenant_id=config.get_conf("openaev_tenant_id"),
        )


### DEPRECATED
class _OpenAEVCollectorHelper:
    def __init__(
        self,
        config: _injectors_sdk.OpenAEVConfigHelper,
        icon,
        collector_type=None,
        security_platform_type=None,
        connect_run_and_terminate: bool = False,
    ) -> None:
        config_obj = config.to_configuration()
        # ensure the icon path is set in config
        config_obj.set("collector_icon_filepath", icon)
        # override the platform in config if passed this way
        if security_platform_type is not None:
            config_obj.set("collector_platform", security_platform_type)

        self.__daemon = _ClientCollectorDaemon(
            configuration=config_obj,
            callback=None,
            collector_type=collector_type,
        )

        self.__daemon.logger.warning(
            f"DEPRECATED: this collector should be migrated to use {_ClientCollectorDaemon}."
        )

        self.logger_class = _sdk.logger(
            config.get_conf("collector_log_level", default="error").upper(),
            config.get_conf("collector_json_logging", default=True),
        )
        self.collector_logger = self.logger_class(config.get_conf("collector_name"))
        self.api = self.__daemon.api
        self.config_helper = config
        self.config = {
            "collector_id": config_obj.get("collector_id"),
            "collector_name": config_obj.get("collector_name"),
            "collector_type": collector_type,
            "collector_period": config_obj.get("collector_period"),
        }

    def schedule(self, message_callback, delay):
        # backwards compatibility: when older style call sets delay
        # and no config exists,
        if self.__daemon._configuration.get("collector_period") is None:
            self.__daemon._configuration.set("collector_period", delay)
        self.__daemon.set_callback(message_callback)
        self.__daemon.start()


_FROM_XTM = [
    "Configuration",
    "ConfigurationError",
    "PingAlive",
    "data_to_temp_file",
    "is_memory_certificate",
    "logger",
    "ssl_cert_chain",
    "ssl_verify_locations",
]
_FROM_INJECTORS = ["ListenQueue", "OpenAEVConfigHelper", "create_mq_ssl_context"]
_TRUTHINESS = {
    "TRUTHY": (["yes", "true", "True"], "is_truthy"),
    "FALSY": (["no", "false", "False"], "is_falsy"),
}

__getattr__ = _make_deprecated_getattr(
    {
        **{
            name: (
                f"Use 'from xtm_oaev_sdk import {name}' instead.",
                getattr(_sdk, name),
            )
            for name in _FROM_XTM
        },
        **{
            name: (
                f"Use 'from injectors_sdk import {name}' instead.",
                getattr(_injectors_sdk, name),
            )
            for name in _FROM_INJECTORS
        },
        "OpenAEVInjectorHelper": (
            "Use 'from injectors_sdk import OpenAEVInjectorHelper' and pass "
            "api_client=OpenAEV(...) instead.",
            _ClientInjectorHelper,
        ),
        "OpenAEVDetectionHelper": (
            "Use 'from collectors_sdk import OpenAEVDetectionHelper' instead.",
            _collectors_sdk.OpenAEVDetectionHelper,
        ),
        "_is_base64_encoded": (
            "'_is_base64_encoded' is private and will be removed.",
            _detection._is_base64_encoded,
        ),
        "CollectorDaemon": (_COLLECTOR_DAEMON_MESSAGE, _ClientCollectorDaemon),
        "OpenAEVCollectorHelper": (
            "OpenAEVCollectorHelper is deprecated; use "
            "'from collectors_sdk import CollectorDaemon' instead.",
            _OpenAEVCollectorHelper,
        ),
        **{
            name: (
                f"'{name}' is deprecated; use 'from xtm_oaev_sdk import {helper}' "
                "instead.",
                value,
            )
            for name, (value, helper) in _TRUTHINESS.items()
        },
    },
    module_name=__name__,
)
