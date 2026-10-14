import unittest
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pyoaev.utils as module


class TestUtils(unittest.TestCase):
    def test_get_content_type(self):
        self.assertEqual(
            module.get_content_type("application/json; charset=utf-8"),
            "application/json",
        )

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

    def test_encoded_id_from_existing_instance_returns_same_object(self):
        encoded_id = module.EncodedId("with space")
        self.assertIs(module.EncodedId(encoded_id), encoded_id)

    def test_encoded_id_encodes_string_and_keeps_int(self):
        self.assertEqual(module.EncodedId("a/b c"), "a%2Fb%20c")
        self.assertEqual(module.EncodedId(42), "42")

    def test_encoded_id_rejects_unsupported_type(self):
        with self.assertRaises(TypeError):
            module.EncodedId(cast(Any, ["bad"]))

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

    def test_copy_dict_flattens_nested_dict(self):
        destination = {}
        module.copy_dict(
            src={"a": 1, "meta": {"x": "y", "n": 2}},
            dest=destination,
        )
        self.assertEqual(destination, {"a": 1, "meta[x]": "y", "meta[n]": 2})

    def test_remove_none_from_dict(self):
        self.assertEqual(module.remove_none_from_dict({"a": 1, "b": None}), {"a": 1})


if __name__ == "__main__":
    unittest.main()
