from unittest.mock import MagicMock
from uuid import UUID

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from pyoaev import OpenAEV
from pyoaev.apis.inputs.search import Filter, FilterGroup, SearchPaginationInput


# --------------------------------------------------
# SCENARIO
# --------------------------------------------------
@scenario(
    "multi_tenant_endpoint_search_targets.feature",
    "searchTargets routing behavior",
)
def test_search_targets_routing():
    pass


# --------------------------------------------------
# FIXTURE CONTEXT
# --------------------------------------------------


@pytest.fixture
def context():
    return {}


# --------------------------------------------------
# HELPERS
# --------------------------------------------------


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


# --------------------------------------------------
# GIVEN
# --------------------------------------------------


@given(parsers.parse('an OpenAEV client with tenant_id "{tenant_id}"'))
def client(context, monkeypatch, tenant_id):
    captured = {}

    def _fake_request(method, url, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        return MockResponse()

    mock_request = MagicMock(side_effect=_fake_request)
    monkeypatch.setattr("requests.Session.request", mock_request)
    context["mock_request"] = mock_request

    context["tenant_id"] = None if tenant_id == "None" else UUID(tenant_id)
    context["captured"] = captured


@given("a valid SearchPaginationInput")
def search_input(context):
    context["search_input"] = build_search_input()


# --------------------------------------------------
# WHEN
# --------------------------------------------------


@when("I call searchTargets on endpoint")
def call_search_targets(context):
    api_client = OpenAEV(
        "url",
        "token",
        tenant_id=context["tenant_id"],
    )

    api_client.endpoint.searchTargets(context["search_input"])


# --------------------------------------------------
# THEN
# --------------------------------------------------


@then(parsers.parse('the request URL should be "{expected_url}"'))
def check_request(context, expected_url):
    captured = context["captured"]
    search_input = context["search_input"]
    mock_request = context["mock_request"]

    assert mock_request.call_count == 1
    assert captured["method"] == "post"
    assert captured["url"] == expected_url
    assert captured["json"] == search_input.to_dict()
