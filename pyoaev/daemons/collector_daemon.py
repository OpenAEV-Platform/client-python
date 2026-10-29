import sched
import time
from typing import Any

from pyoaev import Configuration
from pyoaev.daemons import BaseDaemon
from pyoaev.utils import PingAlive

DEFAULT_PERIOD_SECONDS = 60

# Neutral grey used for tags auto-created alongside the security platform,
# consistent with the tag colors already used across collectors.
DEFAULT_PLATFORM_TAG_COLOR = "#6b7280"

# Expectation types declared by a collector that does not choose its own.
DEFAULT_SUPPORTED_EXPECTATION_TYPES = ["DETECTION", "PREVENTION"]
# Expectation types a collector can declare. Listed explicitly: ExpectationTypeEnum
# maps any unknown value to Other, so it cannot be used to validate them.
DECLARABLE_EXPECTATION_TYPES = ("DETECTION", "PREVENTION", "LOGGING", "VULNERABILITY")


def _validate_expectation_types(expectation_types: list[str]) -> list[str]:
    """Returns the expectation types without duplicates, in their order.

    :raises ValueError: if the list is empty or holds a value that is not an
        uppercase declarable expectation type
    """
    if isinstance(expectation_types, str) or not expectation_types:
        raise ValueError(
            "Supported expectation types must be a non-empty list, "
            f"got {expectation_types!r}"
        )
    validated = []
    for expectation_type in expectation_types:
        if expectation_type not in DECLARABLE_EXPECTATION_TYPES:
            raise ValueError(
                f"Unsupported expectation type {expectation_type!r}, "
                f"expected one of {', '.join(DECLARABLE_EXPECTATION_TYPES)}"
            )
        if expectation_type not in validated:
            validated.append(expectation_type)
    return validated


class CollectorDaemon(BaseDaemon):
    """Implementation of a daemon of Collector type. Note that it requires
    specific configuration keys to run its setup.
    `collector_icon_filepath`: relative path to an icon image (preferably PNG)
    `collector_id`: unique identifier for the collector (UUIDv4)
    `collector_period`: time to wait in seconds between each loop execution; note
    that this time is added to the time the loop takes to run, so the actual total
    time between each loop start is time_of_loop+period.
    `collector_author` (optional): source-declared author override for the
    collector's payloads and contracts; when absent, the platform attributes
    them to the collector's name.
    `collector_platform_description` (optional): description applied to the
    security platform auto-created when `collector_platform` is set, so the
    read-only card is not empty in the UI.
    `collector_platform_tags` (optional): list of tag names (or a
    comma-separated string) applied to the auto-created security platform.

    :param supported_expectation_types: expectation types the collector can
        answer, sent to the platform at registration and on every ping, e.g.
        ``["DETECTION", "PREVENTION", "LOGGING"]``. Defaults to DETECTION and
        PREVENTION: a collector only receives LOGGING expectations once it
        declares LOGGING. Use :meth:`update_supported_expectation_types` to
        change it at runtime.
    :type supported_expectation_types: list[str], optional
    """

    def __init__(
        self,
        configuration: Configuration,
        callback: callable = None,
        logger=None,
        api_client=None,
        collector_type=None,
        supported_expectation_types: list[str] | None = None,
    ):
        super().__init__(configuration, callback, logger, api_client)
        if collector_type is None:
            raise ValueError("Must define a value for collector type")
        self.collector_type = collector_type
        self._supported_expectation_types = _validate_expectation_types(
            DEFAULT_SUPPORTED_EXPECTATION_TYPES
            if supported_expectation_types is None
            else supported_expectation_types
        )
        # Registration payload, re-sent by PingAlive; set by _setup.
        self._registration_config: dict[str, Any] | None = None

    def _setup(self):
        if self._configuration.get("collector_period") is None:
            self._configuration.set("collector_period", DEFAULT_PERIOD_SECONDS)
        icon_path = self._configuration.get("collector_icon_filepath")
        icon_name = self._configuration.get("collector_id") + ".png"
        with open(icon_path, "rb") as icon_file_handle:
            collector_icon = (icon_name, icon_file_handle, "image/png")
            document = self.api.document.upsert(document={}, file=collector_icon)
            if self._configuration.get("collector_platform") is not None:
                security_platform_input = {
                    "asset_name": self._configuration.get("collector_name"),
                    "asset_external_reference": self._configuration.get("collector_id"),
                    "security_platform_type": self._configuration.get(
                        "collector_platform"
                    ),
                    "security_platform_logo_light": document.get("document_id"),
                    "security_platform_logo_dark": document.get("document_id"),
                }
                description = self._configuration.get("collector_platform_description")
                if description:
                    security_platform_input["asset_description"] = description
                tag_ids = self.__upsert_platform_tags(
                    self._configuration.get("collector_platform_tags")
                )
                if tag_ids:
                    security_platform_input["asset_tags"] = tag_ids
                security_platform = self.api.security_platform.upsert(
                    security_platform_input
                )
            else:
                security_platform = {}
            security_platform_id = security_platform.get("asset_id")
            config = {
                "collector_id": self._configuration.get("collector_id"),
                "collector_name": self._configuration.get("collector_name"),
                "collector_type": self.collector_type,
                "collector_period": self._configuration.get("collector_period"),
                "collector_security_platform": security_platform_id,
                # Optional author override; None lets the platform fall back to
                # the collector name.
                "collector_author": self._configuration.get("collector_author"),
                "collector_supported_expectation_types": list(
                    self._supported_expectation_types
                ),
            }
        with open(icon_path, "rb") as icon_file_handle:
            collector_icon = (icon_name, icon_file_handle, "image/png")
            self.api.collector.create(config, collector_icon)

        self._registration_config = config
        PingAlive(self.api, config, self.logger, "collector").start()

    def update_supported_expectation_types(
        self, supported_expectation_types: list[str]
    ) -> None:
        """Changes the expectation types declared to the platform.

        Once the collector is registered, the next ping (within 40 seconds)
        carries the new list. For example, a collector withdraws LOGGING when
        its log source becomes unusable, so the platform stops waiting for its
        LOGGING results.

        :param supported_expectation_types: the new list, e.g. ``["DETECTION", "PREVENTION"]``
        :type supported_expectation_types: list[str]
        :raises ValueError: if the list is invalid; the declared list is then unchanged
        """
        validated = _validate_expectation_types(supported_expectation_types)
        self._supported_expectation_types = validated
        if self._registration_config is not None:
            # Assign a new list, never change it in place: the PingAlive thread
            # may be serializing the current one.
            self._registration_config["collector_supported_expectation_types"] = list(
                validated
            )
        self.logger.info(f"Supported expectation types: {', '.join(validated)}")

    def __upsert_platform_tags(self, tag_names) -> list:
        """Upserts the configured security platform tags and returns their ids.

        Accepts either a list of tag names or a comma-separated string; tag
        upsert failures are logged and skipped so the collector setup never
        fails because of a tag.
        """
        if not tag_names:
            return []
        if isinstance(tag_names, str):
            tag_names = tag_names.split(",")
        tag_ids = []
        for raw_name in tag_names:
            # Strip whitespace for both string and list inputs (YAML list values
            # can carry stray spaces too).
            tag_name = raw_name.strip() if isinstance(raw_name, str) else raw_name
            if not tag_name:
                continue
            try:
                tag = self.api.tag.upsert(
                    {"tag_name": tag_name, "tag_color": DEFAULT_PLATFORM_TAG_COLOR}
                )
                tag_id = tag.get("tag_id")
                if tag_id:
                    tag_ids.append(tag_id)
            except Exception as err:  # noqa: BLE001
                self.logger.warning(
                    f"Could not upsert security platform tag {tag_name}: {err}"
                )
        return tag_ids

    def _start_loop(self):
        scheduler = sched.scheduler(time.time, time.sleep)
        delay = self._configuration.get("collector_period")
        self._try_callback()
        scheduler.enter(
            delay=delay,
            priority=1,
            action=self.__schedule,
            argument=(scheduler, self._try_callback, delay),
        )
        scheduler.run()

    def __schedule(self, scheduler, callback, delay):
        callback()
        scheduler.enter(
            delay=delay,
            priority=1,
            action=self.__schedule,
            argument=(scheduler, callback, delay),
        )
