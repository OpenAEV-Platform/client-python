from unittest import TestCase, main, mock

from pyoaev import OpenAEV
from pyoaev.exceptions import OpenAEVParsingError


def make_json_response(payload):
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.history = None
            self.content = None
            self.headers = {"Content-Type": "application/json"}

        def json(self):
            return payload

    return MockResponse()


class TestAiExpectationsForSource(TestCase):
    @mock.patch("requests.Session.request")
    def test_returns_list_of_expectations(self, mock_request):
        expectations = [
            {"inject_expectation_id": "exp-1"},
            {"inject_expectation_id": "exp-2"},
        ]
        mock_request.return_value = make_json_response(expectations)
        api_client = OpenAEV("url", "token")

        result = api_client.inject_expectation.ai_expectations_for_source("collector-1")

        mock_request.assert_called_once()
        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["method"], "get")
        self.assertEqual(kwargs["url"], "url/api/injects/expectations/ai/collector-1")
        self.assertEqual(result, expectations)

    @mock.patch("requests.Session.request")
    def test_raises_parsing_error_when_not_a_list(self, mock_request):
        mock_request.return_value = make_json_response({"unexpected": "shape"})
        api_client = OpenAEV("url", "token")

        with self.assertRaises(OpenAEVParsingError):
            api_client.inject_expectation.ai_expectations_for_source("collector-1")


if __name__ == "__main__":
    main()
