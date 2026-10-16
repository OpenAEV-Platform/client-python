import ipaddress
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from xtm_oaev_sdk import SignatureManager


@scenario(
    "features/signature_manager_ip_resolution.feature",
    "resolve_container_ip returns a valid IPv4 in each supported execution environment",
)
def test_resolve_container_ip_returns_valid_ipv4():
    pass


@scenario(
    "constraints/signature_manager_ip_resolution_constraints.feature",
    "resolve_container_ip returns unknown and emits exactly one warning when all strategies fail",
)
def test_resolve_container_ip_returns_unknown_when_all_strategies_fail():
    pass


@pytest.fixture
def context():
    logger = MagicMock()
    return {
        "logger": logger,
        "signature_manager": SignatureManager(transport=MagicMock(), logger=logger),
    }


@given(parsers.parse('a SignatureManager running in a "{environment}" environment'))
def signature_manager_environment(context, monkeypatch, environment):
    if environment == "Docker":
        monkeypatch.setattr(
            "socket.gethostbyname",
            lambda _: "172.17.0.2",
        )
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: SimpleNamespace(
                returncode=0,
                stdout="172.17.0.2\n",
            ),
        )
    elif environment == "Kubernetes":
        monkeypatch.setattr(
            "socket.gethostbyname",
            lambda _: (_ for _ in ()).throw(OSError("socket fail")),
        )
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: SimpleNamespace(
                returncode=0,
                stdout="10.244.0.8\n",
            ),
        )
    else:
        monkeypatch.setattr(
            "socket.gethostbyname",
            lambda _: "192.0.2.20",
        )


@given("all IP resolution strategies are mocked to fail")
def all_ip_resolution_strategies_fail(context, monkeypatch):
    monkeypatch.setattr(
        "socket.gethostbyname",
        lambda _: (_ for _ in ()).throw(OSError("socket fail")),
    )
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("command fail")),
    )


@when("I call resolve_container_ip")
def call_resolve_container_ip(context):
    context["resolve_exception"] = None
    try:
        context["resolved_ip"] = context["signature_manager"].resolve_container_ip()
    except Exception as exc:
        context["resolve_exception"] = exc


@then("the returned value is a non-empty valid IPv4 address string")
def assert_returned_value_valid_ipv4(context):
    assert context["resolve_exception"] is None
    resolved_ip = context["resolved_ip"]
    assert isinstance(resolved_ip, str)
    assert resolved_ip.strip() != ""
    assert ipaddress.ip_address(resolved_ip).version == 4


@then(parsers.parse('the returned value is the string "{expected_value}"'))
def assert_returned_value_matches(context, expected_value):
    assert context["resolved_ip"] == expected_value


@then(parsers.parse("exactly {count:d} WARNING log message is emitted"))
def assert_warning_count(context, count):
    assert context["logger"].warning.call_count == count


@then("no exception propagates from resolve_container_ip")
def assert_no_exception_from_resolve_container_ip(context):
    assert context["resolve_exception"] is None
