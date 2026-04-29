"""URL normalization in OpenAEV client feature tests."""

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from pyoaev import OpenAEV

# --------------------------------------------------
# SCENARIOS
# --------------------------------------------------


@scenario(
    "multi_tenant_api_routing_constraint.feature",
    "URL normalization combines base_url and path correctly",
)
def test_url_normalization():
    pass


# --------------------------------------------------
# FIXTURE CONTEXT
# --------------------------------------------------


@pytest.fixture
def context():
    return {}


# --------------------------------------------------
# GIVEN
# --------------------------------------------------


@given(parsers.parse('an OpenAEV client with base_url "{base_url}"'))
def client(context, base_url):
    context["client"] = OpenAEV(
        url=base_url,
        token="token",
        tenant_id=None,
    )


# --------------------------------------------------
# WHEN
# --------------------------------------------------


@when(parsers.parse('I build the URL for "{path}"'))
def build_url(context, path):
    client = context["client"]
    context["result"] = client._build_url(path)


# --------------------------------------------------
# THEN
# --------------------------------------------------


@then(parsers.parse('the resulting URL should be "{expected}"'))
def check_url(context, expected):
    assert context["result"] == expected
