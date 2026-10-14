import unittest
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


if __name__ == "__main__":
    unittest.main()
