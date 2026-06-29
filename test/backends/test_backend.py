import unittest
from unittest.mock import MagicMock

from pyoaev.backends import backend as module


class TestTokenAuth(unittest.TestCase):
    def test_auto_bearer_token(self):
        request = MagicMock()
        request.headers = dict()
        token = "my-secret-token"

        token_auth = module.TokenAuth(token=token)

        _request = token_auth(request)

        self.assertEqual(
            _request.headers["Authorization"],
            f"Bearer {token}",
        )

class TestRequestsReponse(unittest.TestCase):
    def test_init_and_properties(self):
        response = MagicMock()

        rr = module.RequestsResponse(response)

        self.assertEqual(response, rr.response)
        self.assertEqual(response.status_code, rr.status_code)
        self.assertEqual(response.headers, rr.headers)
        self.assertEqual(response.content, rr.content)
        self.assertEqual(response.reason, rr.reason)

class TestRequestsBackend(unittest.TestCase):
    def test_no_cookie_allowed(self):
        backend = module.RequestsBackend()

        self.assertIsNotNone(backend._client.cookies._policy.allowed_domains())
        self.assertEqual(len(backend._client.cookies._policy.allowed_domains()), 0)
