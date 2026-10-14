import unittest
from unittest.mock import MagicMock

import pyoaev.exceptions as module


class TestExceptions(unittest.TestCase):
    def test_openaeverror_init(self):
        error_message = MagicMock()
        response_code = MagicMock()
        response_body = MagicMock()

        exception = module.OpenAEVError(error_message, response_code, response_body)

        self.assertEqual(exception.response_code, response_code)
        self.assertEqual(exception.response_body, response_body)
        self.assertEqual(exception.error_message, error_message.decode.return_value)

    def test_openaeverror_init_auto_decode(self):
        response_code = MagicMock()
        response_body = MagicMock()

        exception = module.OpenAEVError(b"test", response_code, response_body)

        self.assertEqual(exception.error_message, "test")

        exception = module.OpenAEVError("test", response_code, response_body)

        self.assertEqual(exception.error_message, "test")

    def test_openaeverror_strcast_no_message(self):
        error_message = None
        response_code = 418
        response_body = MagicMock()

        exception = module.OpenAEVError(error_message, response_code, response_body)

        strdata = str(exception)

        self.assertEqual(strdata, "418: Unknown error")

    def test_openaeverror_strcast_no_message_no_code(self):
        error_message = None
        response_code = None
        response_body = MagicMock()

        exception = module.OpenAEVError(error_message, response_code, response_body)

        strdata = str(exception)

        self.assertEqual(strdata, "Unknown error")

    def test_openaeverror_strcast_with_body(self):
        error_message = None
        response_code = 418
        response_body = b'{"message": "I am a teapot"}'

        exception = module.OpenAEVError(error_message, response_code, response_body)

        strdata = str(exception)

        self.assertEqual(strdata, "418: I am a teapot")
