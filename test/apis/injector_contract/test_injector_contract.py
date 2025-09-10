import json
from unittest import TestCase, main, mock
from unittest.mock import ANY

from pyobas import OpenBAS
from pyobas.apis.inputs.search import (
    Filter,
    FilterGroup,
    InjectorContractSearchPaginationInput,
)


def create_mock_api_client():
    return mock.MagicMock()


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
        api_client = OpenBAS("url", "token")

        search_input = InjectorContractSearchPaginationInput(
            0,
            20,
            FilterGroup("or", [Filter("prop", "and", "eq", ["titi", "toto"])]),
            None,
            None,
        )

        expected_json = search_input.to_dict()
        api_client.injector_contract.search(search_input)

        mock_request.assert_called_once_with(
            method="post",
            url="url/api/injector_contracts/search",
            params={},
            data=None,
            timeout=None,
            stream=False,
            verify=True,
            json=expected_json,
            headers=ANY,
            auth=ANY,
        )


if __name__ == "__main__":
    main()
