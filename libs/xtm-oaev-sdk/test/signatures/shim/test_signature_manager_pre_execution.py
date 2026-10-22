import ipaddress
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from pyoaev.signatures.models import (
    CloudInjectorConfig,
    ExecutionSignature,
    NetworkInjectorConfig,
    build_network_configs,
)
from pyoaev.signatures.signature_manager import SignatureManager

# --------------------------------------------------
# SCENARIOS
# --------------------------------------------------


@scenario(
    "features/signature_manager_pre_execution.feature",
    "Network category returns required IP and timing fields and no cloud or query fields",
)
def test_network_category_required_fields():
    pass


@scenario(
    "features/signature_manager_pre_execution.feature",
    "Network hostname target returns hostname and no target_ipv4",
)
def test_network_hostname_target():
    pass


@scenario(
    "features/signature_manager_pre_execution.feature",
    "Cloud category returns required cloud identity fields and no IP fields",
)
def test_cloud_category_required_fields():
    pass


@scenario(
    "features/signature_manager_pre_execution.feature",
    "Network multi-target returns one dict per target with a shared source IP",
)
def test_network_multi_target():
    pass


@scenario(
    "features/signature_manager_pre_execution.feature",
    "All network multi-target dicts share the same source_ipv4",
)
def test_network_multi_target_shared_source():
    pass


@scenario(
    "features/signature_manager_pre_execution.feature",
    "Cloud multi-region returns one dict per region with a shared account ID",
)
def test_cloud_multi_region():
    pass


@scenario(
    "features/signature_manager_pre_execution.feature",
    "Builder classifies a mixed list of targets into typed configs",
)
def test_builder_classifies_mixed_targets():
    pass


@scenario(
    "constraints/signature_manager_pre_execution_constraints.feature",
    "start_time is generated at method-call time not at class instantiation time",
)
def test_start_time_generated_at_call_time():
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


def parse_utc_iso8601(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc)


# --------------------------------------------------
# GIVEN
# --------------------------------------------------


@given(
    "a SignatureManager initialised with constructor SignatureManager(client, logger)",
    target_fixture="signature_manager",
)
def signature_manager():
    return SignatureManager(client=MagicMock(), logger=None)


@given(
    parsers.parse('a NetworkInjectorConfig with target_ipv4="{target_ipv4}"'),
    target_fixture="config",
)
def network_config_ipv4(target_ipv4):
    return NetworkInjectorConfig(target_ipv4=target_ipv4)


@given(
    parsers.parse('a NetworkInjectorConfig with target_hostname="{target_hostname}"'),
    target_fixture="config",
)
def network_config_hostname(target_hostname):
    return NetworkInjectorConfig(target_hostname=target_hostname)


@given(
    parsers.parse(
        'a CloudInjectorConfig with cloud_provider="{cloud_provider}", '
        'cloud_account_id="{cloud_account_id}", cloud_region="{cloud_region}", '
        'and target_service="{target_service}"'
    ),
    target_fixture="config",
)
def cloud_config_single(
    cloud_provider,
    cloud_account_id,
    cloud_region,
    target_service,
):
    return CloudInjectorConfig(
        cloud_provider=cloud_provider,
        cloud_account_id=cloud_account_id,
        cloud_region=cloud_region,
        target_service=target_service,
    )


@given(
    parsers.parse(
        "a list of 3 NetworkInjectorConfig with target_ipv4 "
        '"{ip_1}", "{ip_2}", "{ip_3}"'
    ),
    target_fixture="config",
)
def network_config_list(ip_1, ip_2, ip_3):
    return [
        NetworkInjectorConfig(target_ipv4=ip_1),
        NetworkInjectorConfig(target_ipv4=ip_2),
        NetworkInjectorConfig(target_ipv4=ip_3),
    ]


@given(
    "a list of 3 NetworkInjectorConfig built from default IPv4 targets",
    target_fixture="config",
)
def network_config_list_default():
    return [
        NetworkInjectorConfig(target_ipv4="10.0.0.1"),
        NetworkInjectorConfig(target_ipv4="10.0.0.2"),
        NetworkInjectorConfig(target_ipv4="10.0.0.3"),
    ]


@given(
    parsers.parse(
        'a list of 3 CloudInjectorConfig with cloud_account_id="{cloud_account_id}" '
        'and regions "{region_1}", "{region_2}", "{region_3}"'
    ),
    target_fixture="config",
)
def cloud_config_list(cloud_account_id, region_1, region_2, region_3):
    return [
        CloudInjectorConfig(
            cloud_provider="aws",
            cloud_account_id=cloud_account_id,
            cloud_region=region,
        )
        for region in (region_1, region_2, region_3)
    ]


@given(
    parsers.parse('a raw mixed target list "{value_1}", "{value_2}", "{value_3}"'),
    target_fixture="raw_targets",
)
def raw_mixed_target_list(value_1, value_2, value_3):
    return [value_1, value_2, value_3]


@given(
    "the running container has a resolvable IPv4 address",
    target_fixture="source_ipv4",
)
def resolvable_container_ipv4(request):
    patcher = patch(
        "pyoaev.signatures.signature_manager.SignatureManager.resolve_container_ip",
        return_value="172.17.0.2",
    )
    patcher.start()
    request.addfinalizer(patcher.stop)
    return "172.17.0.2"


@given(
    parsers.parse(
        'the running container has a resolvable IPv4 address "{source_ipv4}"'
    ),
    target_fixture="source_ipv4",
)
def resolvable_container_ipv4_explicit(request, source_ipv4):
    patcher = patch(
        "pyoaev.signatures.signature_manager.SignatureManager.resolve_container_ip",
        return_value=source_ipv4,
    )
    patcher.start()
    request.addfinalizer(patcher.stop)
    return source_ipv4


@given(
    "a SignatureManager that was instantiated at timestamp T0",
    target_fixture="signature_manager",
)
def signature_manager_at_t0(context):
    t0 = datetime(2024, 6, 26, 6, 6, 1, tzinfo=timezone.utc)
    context["t0"] = t0
    manager = SignatureManager(client=MagicMock(), logger=None)
    manager._test_t0 = t0
    return manager


@given(
    "5 seconds elapse after instantiation",
    target_fixture="t1",
)
def elapsed_5_seconds(context):
    t1 = context["t0"] + timedelta(seconds=5)
    context["t1"] = t1
    return t1


# --------------------------------------------------
# WHEN
# --------------------------------------------------


@when(
    "I call build_execution_signatures with the config",
    target_fixture="result",
)
def call_build_with_config(signature_manager, config):
    return signature_manager.build_execution_signatures(config=config)


@when(
    "I call build_execution_signatures with the config list",
    target_fixture="result",
)
def call_build_with_config_list(signature_manager, config):
    return signature_manager.build_execution_signatures(config=config)


@when(
    "I call build_execution_signatures with the config at timestamp T1",
    target_fixture="result",
)
def call_build_at_t1(signature_manager, config, t1):
    with patch.object(signature_manager, "_utcnow", return_value=t1):
        return signature_manager.build_execution_signatures(config=config)


@when(
    "I build network configs from the raw list",
    target_fixture="built_configs",
)
def build_configs_from_raw(raw_targets):
    return build_network_configs(raw_targets)


# --------------------------------------------------
# THEN
# --------------------------------------------------


@then("the returned dict contains source_ipv4 as a non-empty valid IPv4 address string")
def source_ipv4_is_valid(result):
    source_ipv4 = result.source_ipv4
    assert source_ipv4
    ipaddress.IPv4Address(source_ipv4)


@then("the returned dict contains start_time as a UTC ISO 8601 string")
def start_time_is_utc_iso8601(result):
    start_time = result.start_time
    parsed = parse_utc_iso8601(start_time)
    assert parsed.tzinfo is not None


@then(parsers.parse('the returned dict contains target_ipv4 equal to "{value}"'))
def returned_dict_target_ipv4(result, value):
    assert result.target_ipv4 == value


@then(parsers.parse('the returned dict contains target_hostname equal to "{value}"'))
def returned_dict_target_hostname(result, value):
    assert result.target_hostname == value


@then(parsers.parse('the returned dict contains cloud_provider equal to "{value}"'))
def returned_dict_cloud_provider(result, value):
    assert result.cloud_provider == value


@then(parsers.parse('the returned dict contains cloud_account_id equal to "{value}"'))
def returned_dict_cloud_account_id(result, value):
    assert result.cloud_account_id == value


@then(parsers.parse('the returned dict contains cloud_region equal to "{value}"'))
def returned_dict_cloud_region(result, value):
    assert result.cloud_region == value


@then(parsers.parse('the returned dict contains target_service equal to "{value}"'))
def returned_dict_target_service(result, value):
    assert result.target_service == value


@then(parsers.parse('the returned dict contains query equal to "{value}"'))
def returned_dict_query(result, value):
    assert result.query == value


@then(parsers.parse("the returned dict does not contain {field}"))
def returned_dict_does_not_contain_field(result, field):
    assert field not in result


@then("the return value is a list of exactly 3 dicts")
def return_value_is_list_of_three_dicts(result):
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(item, ExecutionSignature) for item in result)


@then(parsers.parse("the return value is a list of {count:d} dicts"))
def return_value_is_list_of_n_dicts(result, count):
    assert isinstance(result, list)
    assert len(result) == count
    assert all(isinstance(item, ExecutionSignature) for item in result)


@then(
    parsers.parse(
        'the dict at position {index:d} contains target_ipv4 equal to "{target_ip}"'
    )
)
def list_dict_contains_target_ipv4_at_position(result, index, target_ip):
    assert result[index].target_ipv4 == target_ip


@then(
    parsers.parse(
        'the dict at position {index:d} contains source_ipv4 equal to "{source_ipv4}"'
    )
)
def list_dict_contains_source_ipv4_at_position(
    result,
    index,
    source_ipv4,
):
    assert result[index].source_ipv4 == source_ipv4


@then(
    parsers.parse(
        'the dict at position {index:d} contains cloud_region equal to "{region}"'
    )
)
def list_dict_contains_cloud_region_at_position(result, index, region):
    assert result[index].cloud_region == region


@then(
    parsers.parse(
        'the dict at position {index:d} contains cloud_account_id equal to "{account_id}"'
    )
)
def list_dict_contains_cloud_account_id_at_position(result, index, account_id):
    assert result[index].cloud_account_id == account_id


@then("all 3 dicts contain the same source_ipv4 value")
def all_dicts_share_same_source_ipv4(result):
    assert isinstance(result, list)
    assert len(result) == 3
    source_values = {item.source_ipv4 for item in result}
    assert len(source_values) == 1
    ipaddress.IPv4Address(next(iter(source_values)))


@then("the start_time in the returned dict equals T1 within 1 second tolerance")
def start_time_equals_t1_with_tolerance(result, t1):
    start_time = parse_utc_iso8601(result.start_time)
    delta_seconds = abs((start_time - t1).total_seconds())
    assert delta_seconds <= 1


@then("start_time does not equal T0")
def start_time_not_equal_t0(result, signature_manager):
    start_time = parse_utc_iso8601(result.start_time)
    assert start_time != signature_manager._test_t0


@then(parsers.parse("the builder returns {count:d} NetworkInjectorConfig"))
def builder_returns_n_configs(built_configs, count):
    assert isinstance(built_configs, list)
    assert len(built_configs) == count
    assert all(isinstance(c, NetworkInjectorConfig) for c in built_configs)


@then(
    parsers.parse('the config at position {index:d} has target_ipv4 equal to "{value}"')
)
def config_has_target_ipv4(built_configs, index, value):
    assert built_configs[index].target_ipv4 == value
    assert built_configs[index].target_ipv6 is None
    assert built_configs[index].target_hostname is None


@then(
    parsers.parse('the config at position {index:d} has target_ipv6 equal to "{value}"')
)
def config_has_target_ipv6(built_configs, index, value):
    assert built_configs[index].target_ipv6 == value
    assert built_configs[index].target_ipv4 is None
    assert built_configs[index].target_hostname is None


@then(
    parsers.parse(
        'the config at position {index:d} has target_hostname equal to "{value}"'
    )
)
def config_has_target_hostname(built_configs, index, value):
    assert built_configs[index].target_hostname == value
    assert built_configs[index].target_ipv4 is None
    assert built_configs[index].target_ipv6 is None
