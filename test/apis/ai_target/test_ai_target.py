from unittest import TestCase, main, mock


def mock_response(*args, **kwargs):
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.history = None
            self.content = None
            self.headers = {"Content-Type": "application/json"}

        def json(self):
            return {}

    return MockResponse()


class TestAiTargetManager(TestCase):
    @mock.patch("requests.Session.request", side_effect=mock_response)
    def test_create_posts_to_ai_targets(self, mock_request):
        from pyoaev import OpenAEV

        api_client = OpenAEV("url", "token")
        data = {
            "asset_name": "OpenAI guardrail",
            "ai_target_provider": "openai",
            "ai_target_endpoint": "https://api.openai.com/v1",
        }

        api_client.ai_target.create(data=data)

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["method"], "post")
        self.assertEqual(kwargs["url"], "url/api/ai_targets")
        self.assertEqual(kwargs["json"], data)

    @mock.patch("requests.Session.request", side_effect=mock_response)
    def test_get_requests_single_ai_target(self, mock_request):
        from pyoaev import OpenAEV

        api_client = OpenAEV("url", "token")

        api_client.ai_target.get("asset-123")

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["method"], "get")
        self.assertEqual(kwargs["url"], "url/api/ai_targets/asset-123")

    @mock.patch("requests.Session.request", side_effect=mock_response)
    def test_update_puts_to_ai_target(self, mock_request):
        from pyoaev import OpenAEV

        api_client = OpenAEV("url", "token")
        new_data = {"asset_description": "updated"}

        api_client.ai_target.update("asset-123", new_data=new_data)

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["method"], "put")
        self.assertEqual(kwargs["url"], "url/api/ai_targets/asset-123")
        self.assertEqual(kwargs["json"], new_data)

    @mock.patch("requests.Session.request", side_effect=mock_response)
    def test_delete_calls_delete_on_ai_target(self, mock_request):
        from pyoaev import OpenAEV

        api_client = OpenAEV("url", "token")

        api_client.ai_target.delete("asset-123")

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["method"], "delete")
        self.assertEqual(kwargs["url"], "url/api/ai_targets/asset-123")


if __name__ == "__main__":
    main()
