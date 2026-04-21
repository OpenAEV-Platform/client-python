import unittest

from pyoaev.backends import backend as module


class TestRequestsBackend(unittest.TestCase):
    def test_no_cookie_allowed(self):
        backend = module.RequestsBackend()

        self.assertIsNotNone(backend._client.cookies._policy.allowed_domains())
        self.assertEqual(len(backend._client.cookies._policy.allowed_domains()), 0)
