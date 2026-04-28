import dataclasses
import importlib
import json
import logging
import unittest
import warnings
from typing import Any, cast
from unittest.mock import MagicMock, patch

from pythonjsonlogger.json import JsonFormatter

import pyoaev.utils as module


@dataclasses.dataclass
class _SampleData:
    value: int


class TestUtils(unittest.TestCase):
    def test_custom_json_formatter_inherits_non_deprecated_formatter(self):
        self.assertTrue(issubclass(module.CustomJsonFormatter, JsonFormatter))

    def test_reloading_utils_does_not_raise_jsonlogger_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            importlib.reload(module)

        deprecation_messages = [
            str(warning.message)
            for warning in caught
            if issubclass(warning.category, DeprecationWarning)
        ]
        self.assertFalse(
            any(
                "pythonjsonlogger.jsonlogger has been moved" in message
                for message in deprecation_messages
            )
        )

    def test_get_content_type(self):
        self.assertEqual(
            module.get_content_type("application/json; charset=utf-8"),
            "application/json",
        )

    def test_copy_dict_flattens_nested_dict(self):
        destination = {}
        module.copy_dict(
            src={"a": 1, "meta": {"x": "y", "n": 2}},
            dest=destination,
        )
        self.assertEqual(destination, {"a": 1, "meta[x]": "y", "meta[n]": 2})

    def test_remove_none_from_dict(self):
        self.assertEqual(module.remove_none_from_dict({"a": 1, "b": None}), {"a": 1})

    def test_encoded_id_from_existing_instance_returns_same_object(self):
        encoded_id = module.EncodedId("with space")
        self.assertIs(module.EncodedId(encoded_id), encoded_id)

    def test_encoded_id_encodes_string_and_keeps_int(self):
        self.assertEqual(module.EncodedId("a/b c"), "a%2Fb%20c")
        self.assertEqual(module.EncodedId(42), "42")

    def test_encoded_id_rejects_unsupported_type(self):
        with self.assertRaises(TypeError):
            module.EncodedId(cast(Any, ["bad"]))

    def test_enhanced_json_encoder_serializes_dataclasses(self):
        self.assertEqual(
            json.dumps(_SampleData(value=3), cls=module.EnhancedJSONEncoder),
            '{"value": 3}',
        )

    def test_required_optional_required_attribute_missing(self):
        rules = module.RequiredOptional(required=("name",))
        with self.assertRaises(AttributeError):
            rules.validate_attrs(data={})

    def test_required_optional_excludes_required_attribute(self):
        rules = module.RequiredOptional(required=("name",))
        rules.validate_attrs(data={}, excludes=["name"])

    def test_required_optional_exclusive_allows_only_one_key(self):
        rules = module.RequiredOptional(exclusive=("a", "b"))
        with self.assertRaises(AttributeError):
            rules.validate_attrs(data={"a": 1, "b": 2})

    def test_required_optional_exclusive_requires_one_key(self):
        rules = module.RequiredOptional(exclusive=("a", "b"))
        with self.assertRaises(AttributeError):
            rules.validate_attrs(data={})

    def test_required_optional_exclusive_with_single_key_is_valid(self):
        rules = module.RequiredOptional(exclusive=("a", "b"))
        rules.validate_attrs(data={"a": 1})

    def test_response_content_returns_iterator_when_requested(self):
        response = MagicMock()
        response.iter_content.return_value = iter([b"a", b"b"])

        iterator = module.response_content(
            response,
            streamed=False,
            action=None,
            chunk_size=10,
            iterator=True,
        )

        self.assertEqual(list(iterator), [b"a", b"b"])

    def test_response_content_returns_raw_content_when_not_streamed(self):
        response = MagicMock()
        response.content = b"payload"

        data = module.response_content(
            response,
            streamed=False,
            action=None,
            chunk_size=10,
            iterator=False,
        )

        self.assertEqual(data, b"payload")

    def test_response_content_streamed_uses_action_for_non_empty_chunks(self):
        response = MagicMock()
        response.iter_content.return_value = [b"one", b"", b"two"]
        action = MagicMock()

        returned = module.response_content(
            response,
            streamed=True,
            action=action,
            chunk_size=10,
            iterator=False,
        )

        self.assertIsNone(returned)
        action.assert_any_call(b"one")
        action.assert_any_call(b"two")
        self.assertEqual(action.call_count, 2)

    def test_response_content_streamed_defaults_to_stdout_stream(self):
        response = MagicMock()
        response.iter_content.return_value = [b"visible"]

        with patch("builtins.print") as mock_print:
            module.response_content(
                response,
                streamed=True,
                action=None,
                chunk_size=10,
                iterator=False,
            )

        mock_print.assert_called_once_with(b"visible")

    def test_custom_json_formatter_add_fields_sets_timestamp_and_level(self):
        formatter = module.CustomJsonFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )
        log_record = {}

        formatter.add_fields(log_record, record, {})

        self.assertIn("timestamp", log_record)
        self.assertEqual(log_record["level"], "INFO")

    def test_setup_logging_config_json_logging_true_uses_custom_formatter(self):
        with patch("pyoaev.utils.logging.basicConfig") as mock_basic_config:
            module.setup_logging_config(logging.INFO, json_logging=True)

        kwargs = mock_basic_config.call_args.kwargs
        self.assertEqual(kwargs["level"], logging.INFO)
        self.assertIn("handlers", kwargs)
        self.assertIsInstance(
            kwargs["handlers"][0].formatter, module.CustomJsonFormatter
        )

    def test_setup_logging_config_json_logging_false_calls_basic_config(self):
        with patch("pyoaev.utils.logging.basicConfig") as mock_basic_config:
            module.setup_logging_config(logging.WARNING, json_logging=False)

        mock_basic_config.assert_called_once_with(level=logging.WARNING)

    def test_app_logger_methods_delegate_to_local_logger(self):
        with patch("pyoaev.utils.setup_logging_config"):
            app_logger = module.AppLogger(logging.INFO)
        app_logger.local_logger = MagicMock()

        app_logger.debug("d", {"x": 1})
        app_logger.info("i")
        app_logger.warning("w")
        app_logger.error("e")

        self.assertTrue(app_logger.local_logger.debug.called)
        self.assertTrue(app_logger.local_logger.info.called)
        self.assertTrue(app_logger.local_logger.warning.called)
        self.assertTrue(app_logger.local_logger.error.called)

    def test_logger_helper_returns_app_logger(self):
        with patch("pyoaev.utils.setup_logging_config"):
            helper = module.logger(logging.INFO)
        self.assertIsInstance(helper, module.AppLogger)

    def test_pingalive_ping_uses_injector_branch(self):
        api = MagicMock()
        logger = MagicMock()
        ping_alive = module.PingAlive(
            api=api, config={"id": 1}, logger=logger, ping_type="injector"
        )
        ping_alive.exit_event.is_set = MagicMock(side_effect=[False, True])
        ping_alive.exit_event.wait = MagicMock()

        ping_alive.ping()

        api.injector.create.assert_called_once_with({"id": 1}, False)
        ping_alive.exit_event.wait.assert_called_once_with(40)

    def test_pingalive_ping_uses_collector_branch_and_logs_errors(self):
        api = MagicMock()
        api.collector.create.side_effect = Exception("boom")
        logger = MagicMock()
        ping_alive = module.PingAlive(
            api=api, config={}, logger=logger, ping_type="collector"
        )
        ping_alive.exit_event.is_set = MagicMock(side_effect=[False, True])
        ping_alive.exit_event.wait = MagicMock()

        ping_alive.ping()

        logger.error.assert_called_once()
        ping_alive.exit_event.wait.assert_called_once_with(40)

    def test_pingalive_run_and_stop(self):
        ping_alive = module.PingAlive(
            api=MagicMock(), config={}, logger=MagicMock(), ping_type="collector"
        )
        ping_alive.ping = MagicMock()

        ping_alive.run()
        ping_alive.stop()

        ping_alive.logger.info.assert_any_call("Starting PingAlive thread")
        ping_alive.logger.info.assert_any_call("Preparing PingAlive for clean shutdown")
        self.assertTrue(ping_alive.exit_event.is_set())


if __name__ == "__main__":
    unittest.main()
