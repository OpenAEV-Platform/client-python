"""Daemon runtime: lifecycle shared by collector and injector daemons."""

import argparse
import sys
from inspect import signature
from types import FunctionType
from typing import Any, Callable

from xtm_oaev_sdk.seam.common import BaseClient, OpenAEVError
from xtm_oaev_sdk.seam.configuration import ConfigurationProtocol
from xtm_oaev_sdk.seam.daemons import DevOptions

__all__ = ["DaemonRuntime"]

_DEV_DESCRIPTION = (
    "Dev mode: run the daemon without the OpenAEV platform. It reads the platform's"
    " own payloads, and writes every call it would have sent to the platform as one"
    ' JSON list of {"method", "path", "body"}.'
)
_DEV_EPILOG = "Guide: xtm-oaev-sdk docs/how_to_dev_mode.md."


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
        # Only the flag this parser owns reaches it: dev flags and the daemon's own
        # flags share the command line. parse_args stays the parsing call, so code
        # that patches it keeps working.
        own = [arg for arg in sys.argv[1:] if arg == "--dump-config-schema"]
        args = parser.parse_args(own)
        return bool(args.dump_config_schema)

    def dev_argument_parser(
        self, description: str | None = None, epilog: str | None = None
    ) -> argparse.ArgumentParser:
        # No automatic -h and no abbreviations: every daemon reads these options, dev
        # or not, so they must never act on a flag that is not theirs. -h / --help
        # only counts together with --dev (see dev_options).
        parser = argparse.ArgumentParser(
            usage="<daemon> --dev [dev options]",
            description=description or _DEV_DESCRIPTION,
            epilog=epilog or _DEV_EPILOG,
            add_help=False,
            allow_abbrev=False,
        )
        common = parser.add_argument_group("common options")
        common.add_argument(
            "--dev", action="store_true", help="run without the platform"
        )
        common.add_argument(
            "-h", "--help", action="store_true", help="show this help and exit"
        )
        common.add_argument(
            "--out",
            metavar="PATH",
            help="where the calls the daemon would have sent go, as one JSON list"
            " (default: stdout)",
        )
        common.add_argument(
            "--record",
            metavar="PATH",
            help="record every outside call (HTTP, commands) and its answer to PATH",
        )
        common.add_argument(
            "--replay",
            metavar="PATH",
            help="answer every outside call from PATH, offline; a call it does not"
            " hold fails",
        )
        return parser

    def dev_options(self, argv: list[str] | None = None) -> DevOptions:
        args, _ = self.dev_argument_parser().parse_known_args(argv)
        return DevOptions(
            enabled=args.dev,
            out=args.out,
            record=args.record,
            replay=args.replay,
            help=args.help and args.dev,
        )

    def dev_help(self) -> str:
        return self.dev_argument_parser().format_help()

    def dump_config_schema(self, configuration: ConfigurationProtocol) -> None:
        print(configuration.schema())

    def ensure_callback(self, callback: Callable[..., Any] | None) -> None:
        if callback is None:
            raise OpenAEVError("This daemon has no configured callback.")

    def default_api_client(self) -> BaseClient:
        raise OpenAEVError(
            "No api_client was provided to the daemon; inject an OpenAEV API client."
        )
