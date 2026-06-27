from unittest import TestCase, main, mock
from unittest.mock import ANY

from pyoaev import AssetCategory, AssetSubCategory, CloudProvider, OpenAEV
from pyoaev.apis.inputs.search import Filter, FilterGroup, SearchPaginationInput


def mock_response(**kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.history = None
            self.content = None
            self.headers = {"Content-Type": "application/json"}

        def json(self):
            return self.json_data

    return MockResponse(None, 200)


class TestInjectorContract(TestCase):
    @mock.patch("requests.Session.request", side_effect=mock_response)
    def test_search_input_correctly_serialised(self, mock_request):
        api_client = OpenAEV("url", "token")

        search_input = SearchPaginationInput(
            0,
            20,
            FilterGroup(
                "or",
                [Filter("targets", "and", "eq", ["target_1", "target_2", "target_3"])],
            ),
            None,
            None,
        )

        expected_json = search_input.to_dict()
        api_client.endpoint.searchTargets(search_input)

        mock_request.assert_called_once_with(
            method="post",
            url="url/api/endpoints/targets",
            params={},
            data=None,
            timeout=None,
            stream=False,
            verify=True,
            json=expected_json,
            headers=ANY,
            auth=ANY,
        )


class TestEndpointCategorization(TestCase):
    @mock.patch("requests.Session.request", side_effect=mock_response)
    def test_upsert_web_application_without_platform(self, mock_request):
        api_client = OpenAEV("url", "token")
        data = {
            "asset_name": "Filigran website",
            "asset_category": AssetCategory.WEB_APPLICATION,
            "asset_subcategory": AssetSubCategory.WEBSITE,
            "endpoint_url": "https://filigran.io",
            "asset_internet_facing": True,
        }

        api_client.endpoint.upsert(data)

        mock_request.assert_called_once()
        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["method"], "post")
        self.assertEqual(kwargs["url"], "url/api/endpoints/agentless/upsert")
        self.assertEqual(kwargs["json"]["asset_category"], "WEB_APPLICATION")
        # A category-driven asset can be upserted without platform / arch.
        self.assertNotIn("endpoint_platform", kwargs["json"])
        self.assertNotIn("endpoint_arch", kwargs["json"])

    @mock.patch("requests.Session.request", side_effect=mock_response)
    def test_upsert_cloud_resource(self, mock_request):
        api_client = OpenAEV("url", "token")
        data = {
            "asset_name": "prod-bucket",
            "asset_category": AssetCategory.CLOUD_RESOURCE,
            "asset_subcategory": AssetSubCategory.STORAGE,
            "asset_cloud_provider": CloudProvider.AWS,
            "asset_cloud_native_type": "s3_bucket",
            "asset_cloud_region": "eu-west-1",
        }

        api_client.endpoint.upsert(data)

        mock_request.assert_called_once()
        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["url"], "url/api/endpoints/agentless/upsert")
        self.assertEqual(kwargs["json"]["asset_cloud_provider"], "AWS")
        self.assertEqual(kwargs["json"]["asset_cloud_native_type"], "s3_bucket")


if __name__ == "__main__":
    main()
