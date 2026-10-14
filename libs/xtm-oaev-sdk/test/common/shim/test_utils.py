import dataclasses
import json
import logging
import unittest
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

    def test_enhanced_json_encoder_serializes_not_dataclasses(self):
        data = {"test": "this is a test", "other": 3}
        classic_json_dump = json.dumps(data)
        enhanced_json_dump = json.dumps(data, cls=module.EnhancedJSONEncoder)
        self.assertFalse(dataclasses.is_dataclass(data))
        self.assertEqual(
            classic_json_dump,
            enhanced_json_dump,
        )

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
        with patch("xtm_oaev_sdk._core.utils.logging.basicConfig") as mock_basic_config:
            module.setup_logging_config(logging.INFO, json_logging=True)

        kwargs = mock_basic_config.call_args.kwargs
        self.assertEqual(kwargs["level"], logging.INFO)
        self.assertIn("handlers", kwargs)
        self.assertIsInstance(
            kwargs["handlers"][0].formatter, module.CustomJsonFormatter
        )

    def test_setup_logging_config_json_logging_false_calls_basic_config(self):
        with patch("xtm_oaev_sdk._core.utils.logging.basicConfig") as mock_basic_config:
            module.setup_logging_config(logging.WARNING, json_logging=False)

        mock_basic_config.assert_called_once_with(level=logging.WARNING)

    def test_app_logger_methods_delegate_to_local_logger(self):
        with patch("xtm_oaev_sdk._core.utils.setup_logging_config"):
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
        with patch("xtm_oaev_sdk._core.utils.setup_logging_config"):
            helper = module.logger(logging.INFO)
        self.assertIsInstance(helper, module.AppLogger)


if __name__ == "__main__":
    unittest.main()
