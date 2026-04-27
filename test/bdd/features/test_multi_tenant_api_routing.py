from uuid import UUID

from pytest_bdd import given, parsers, scenario, then, when

from pyoaev import OpenAEV

# --------------------------------------------------
# SCENARIOS
# --------------------------------------------------


@scenario(
    "multi_tenant_api_routing.feature",
    "Full URL bypasses tenant routing",
)
def test_full_url_bypasses_tenant_routing():
    pass


@scenario(
    "multi_tenant_api_routing.feature",
    "Relative path routing depends on tenant configuration",
)
def test_relative_path_routing():
    pass


# --------------------------------------------------
# GIVEN
# --------------------------------------------------


@given(
    "an OpenAEV client with any tenant configuration",
    target_fixture="client",
)
def client_any():
    return OpenAEV(
        "base_url",
        "token",
        tenant_id=None,
    )


@given(
    parsers.parse('an OpenAEV client with tenant_id "{tenant_id}"'),
    target_fixture="client",
)
def client_with_tenant(tenant_id):
    if tenant_id is None or tenant_id == "None":
        tenant_id_value = None
    else:
        tenant_id_value = UUID(tenant_id)
    return OpenAEV(
        "base_url",
        "token",
        tenant_id=tenant_id_value,
    )


# --------------------------------------------------
# WHEN
# --------------------------------------------------


@when(
    parsers.parse('I build the URL for "{path}"'),
    target_fixture="result",
)
def build_url(client, path):
    return client._build_url(path)


# --------------------------------------------------
# THEN
# --------------------------------------------------


@then(parsers.parse('the resulting URL should be "{output}"'))
def assert_url(result, output):
    assert result == output
