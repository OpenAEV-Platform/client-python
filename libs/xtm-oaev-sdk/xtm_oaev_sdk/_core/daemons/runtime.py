"""Daemon runtime: lifecycle shared by collector and injector daemons."""

import argparse
from inspect import signature
from types import FunctionType
from typing import Any, Callable

from xtm_oaev_sdk.seam.common import BaseClient, OpenAEVError
from xtm_oaev_sdk.seam.configuration import ConfigurationProtocol

__all__ = ["DaemonRuntime"]


class DaemonRuntime:
    """Implements ``DaemonRuntimePort``."""

    # compatibility layer: in order for older configs to still work, search for legacy names
    def resolve_log_level(self, configuration: ConfigurationProtocol) -> str:
        return (
            configuration.get("log_level")
            or configuration.get("collector_log_level")
            or configuration.get("injector_log_level")
            or "info"
        )

    def resolve_name(self, configuration: ConfigurationProtocol) -> str:
        return (
            configuration.get("name")
            or configuration.get("collector_name")
            or configuration.get("injector_name")
            or "daemon"
        )

    def resolve_id(self, configuration: ConfigurationProtocol) -> Any:
        return (
            configuration.get("id")
            or configuration.get("collector_id")
            or configuration.get("injector_id")
        )

    def invoke_callback(
        self, callback: Callable[..., Any] | None, daemon: Any, logger: Any
    ) -> None:
        try:
            # this is some black magic to allow injecting the collector daemon instance
            # into an arbitrary callback that has a specific argument name
            # this allow for avoiding subclassing the CollectorDaemon class just to provide the callback
            # Example:
            #
            # def standalone_func(collector):
            #   collector.api.call_openaev()
            #
            # CollectorDaemon(config=<pyboas.configuration.Configuration>, standalone_func).start()
            if (
                isinstance(callback, FunctionType)
                and "collector" in signature(callback).parameters
            ):
                callback(collector=daemon)
            else:
                callback()
        except Exception as err:  # pylint: disable=broad-except
            logger.error(f"Error calling: {err}")

    def dump_config_schema_requested(self) -> bool:
        parser = argparse.ArgumentParser(description="parse daemon options")
        parser.add_argument("--dump-config-schema", action="store_true")
        args = parser.parse_args()
        return bool(args.dump_config_schema)

    def dump_config_schema(self, configuration: ConfigurationProtocol) -> None:
        print(configuration.schema())

    def ensure_callback(self, callback: Callable[..., Any] | None) -> None:
        if callback is None:
            raise OpenAEVError("This daemon has no configured callback.")

    def default_api_client(self) -> BaseClient:
        raise OpenAEVError(
            "No api_client was provided to the daemon; inject an OpenAEV API client."
        )
