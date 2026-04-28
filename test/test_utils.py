import importlib
import unittest
import warnings

from pythonjsonlogger.json import JsonFormatter

import pyoaev.utils as module


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


if __name__ == "__main__":
    unittest.main()
