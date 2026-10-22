"""Logging setup: root logger configuration and structured record fields."""

import datetime
import logging
from typing import Any

__all__ = ["LoggingSetup"]


class LoggingSetup:
    """Implements ``LoggingPort``."""

    def setup_logging_config(
        self,
        level: int,
        json_logging: bool,
        formatter_class: type[logging.Formatter],
    ) -> None:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("pika").setLevel(logging.ERROR)
        if json_logging:
            log_handler = logging.StreamHandler()
            log_handler.setLevel(level)
            formatter = formatter_class("%(timestamp)s %(level)s %(name)s %(message)s")
            log_handler.setFormatter(formatter)
            logging.basicConfig(handlers=[log_handler], level=level, force=True)
        else:
            logging.basicConfig(level=level)

    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)

    def prepare_meta(self, meta: Any) -> dict[str, Any] | None:
        return None if meta is None else {"attributes": meta}

    def set_library_level(self, lib: str, log_level: int) -> None:
        logging.getLogger(lib).setLevel(log_level)

    def complete_record(
        self, log_record: dict[str, Any], record: logging.LogRecord
    ) -> None:
        if not log_record.get("timestamp"):
            # This doesn't use record.created, so it is slightly off
            now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname
