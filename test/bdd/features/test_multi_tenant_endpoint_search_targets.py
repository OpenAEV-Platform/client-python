from unittest.mock import MagicMock
from uuid import UUID

import pytest

from pyoaev import OpenAEV
from pyoaev.apis.inputs.search import Filter, FilterGroup, SearchPaginationInput


class MockResponse:
    def __init__(self, json_data=None, status_code=200):
        self._json_data = json_data
        self.status_code = status_code
        self.history = None
        self.content = None
        self.headers = {"Content-Type": "application/json"}

    def json(self):
        return self._json_data or {}


def build_search_input():
    return SearchPaginationInput(
        0,
        20,
        FilterGroup(
            "or",
            [
                Filter(
                    "targets",
                    "and",
                    "eq",
                    ["target_1", "target_2", "target_3"],
                )
            ],
        ),
        None,
        None,
    )


@pytest.mark.parametrize(
    "tenant_id, expected_url",
    [
        (
            None,
            "url/api/endpoints/targets",
        ),
        (
            UUID("2cffad3a-0001-4078-b0e2-ef74274022c3"),
            "url/api/tenants/2cffad3a-0001-4078-b0e2-ef74274022c3/endpoints/targets",
        ),
    ],
    ids=[
        "legacy_routing_no_tenant",
        "tenant_routing_enabled",
    ],
)
def test_search_input_correctly_serialised(monkeypatch, tenant_id, expected_url):
    mock_request = MagicMock(return_value=MockResponse())
    monkeypatch.setattr("requests.Session.request", mock_request)

    api_client = OpenAEV("url", "token", tenant_id=tenant_id)
    search_input = build_search_input()
    expected_json = search_input.to_dict()
    api_client.endpoint.searchTargets(search_input)

    assert mock_request.call_count == 1
    _, kwargs = mock_request.call_args

    assert kwargs["method"] == "post"
    assert kwargs["json"] == expected_json
    assert kwargs["url"] == expected_url
