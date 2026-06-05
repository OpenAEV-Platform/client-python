import inspect

import pytest
from pytest_bdd import given, scenario, then, when


@scenario(
    "features/signature_manager_backward_compat.feature",
    "Injectors that do not call SignatureManager experience no behavioural change",
)
def test_injector_no_behavioural_change():
    pass


@scenario(
    "features/signature_manager_backward_compat.feature",
    "Existing public import paths in pyoaev remain unchanged",
)
def test_existing_public_import_paths_remain_unchanged():
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


@given("an injector that does not call any SignatureManager method")
def injector_without_signature_manager(context, monkeypatch):
    from pyoaev import OpenAEV

    monkeypatch.setattr(
        OpenAEV,
        "http_post",
        lambda self, path, post_data=None, **kwargs: {
            "path": path,
            "post_data": post_data,
        },
    )

    client = OpenAEV("url", "token")
    context["client"] = client


@given("the pyoaev package with SignatureManager merged")
def pyoaev_package_available(context):
    context["pyoaev_package_available"] = True


# --------------------------------------------------
# WHEN
# --------------------------------------------------


@when("that injector executes its normal workflow")
def execute_injector_workflow(context):
    result = None
    caught_exception = None
    try:
        result = context["client"].inject.execution_callback(
            "inject-id",
            {"result": "ok"},
        )
    except Exception as exc:  # pragma: no cover
        caught_exception = exc

    context["workflow_result"] = result
    context["workflow_exception"] = caught_exception


@when(
    "existing code imports InjectManager, SignatureType, SignatureTypes, SignatureMatch, or Expectation using their current import paths"
)
def import_existing_public_paths(context):
    imported = {}
    import_error = None
    try:
        from pyoaev import OpenAEV
        from pyoaev.apis.inject import InjectManager
        from pyoaev.apis.inject_expectation.model.expectation import (
            DetectionExpectation,
            Expectation,
            PreventionExpectation,
        )
        from pyoaev.signatures.signature_match import SignatureMatch
        from pyoaev.signatures.signature_type import SignatureType
        from pyoaev.signatures.types import MatchTypes, SignatureTypes

        imported = {
            "OpenAEV": OpenAEV,
            "InjectManager": InjectManager,
            "SignatureTypes": SignatureTypes,
            "MatchTypes": MatchTypes,
            "SignatureType": SignatureType,
            "SignatureMatch": SignatureMatch,
            "Expectation": Expectation,
            "DetectionExpectation": DetectionExpectation,
            "PreventionExpectation": PreventionExpectation,
        }
    except ImportError as exc:  # pragma: no cover
        import_error = exc

    context["imported"] = imported
    context["import_error"] = import_error


# --------------------------------------------------
# THEN
# --------------------------------------------------


@then(
    "its behaviour is identical to its behaviour before SignatureManager was introduced"
)
def assert_behaviour_unchanged(context):
    assert context["workflow_result"] == {
        "path": "/injects/execution/callback/inject-id",
        "post_data": {"result": "ok"},
    }


@then("no import errors, attribute errors, or unexpected exceptions occur")
def assert_no_exceptions(context):
    assert context["workflow_exception"] is None


@then("all imports resolve without error")
def assert_imports_resolve(context):
    assert context["import_error"] is None

    expected_symbols = {
        "OpenAEV",
        "InjectManager",
        "SignatureTypes",
        "MatchTypes",
        "SignatureType",
        "SignatureMatch",
        "Expectation",
        "DetectionExpectation",
        "PreventionExpectation",
    }
    assert expected_symbols.issubset(set(context["imported"].keys()))


@then("all constructor signatures remain unchanged")
def assert_constructor_signatures(context):
    imported = context["imported"]

    openaev_params = list(inspect.signature(imported["OpenAEV"]).parameters)
    assert openaev_params[:9] == [
        "url",
        "token",
        "timeout",
        "per_page",
        "pagination",
        "order_by",
        "ssl_verify",
        "tenant_id",
        "kwargs",
    ]

    assert list(inspect.signature(imported["InjectManager"]).parameters) == [
        "openaev",
        "parent",
    ]
    assert list(inspect.signature(imported["SignatureType"]).parameters) == [
        "label",
        "match_type",
        "match_score",
    ]
    assert list(inspect.signature(imported["SignatureMatch"]).parameters) == [
        "match_type",
        "match_score",
    ]

    expectation_params = list(inspect.signature(imported["Expectation"]).parameters)
    for required in (
        "inject_expectation_id",
        "inject_expectation_signatures",
        "success_label",
        "failure_label",
    ):
        assert required in expectation_params


@then("all public method signatures remain unchanged")
def assert_public_method_signatures(context):
    imported = context["imported"]

    def params(fn):
        return list(inspect.signature(fn).parameters)

    assert params(imported["InjectManager"].execution_callback) == [
        "self",
        "inject_id",
        "data",
        "kwargs",
    ]
    assert params(imported["InjectManager"].execution_reception) == [
        "self",
        "inject_id",
        "data",
        "kwargs",
    ]
    assert params(imported["SignatureType"].make_struct_for_matching) == [
        "self",
        "data",
    ]
    assert params(imported["Expectation"].update) == [
        "self",
        "success",
        "sender_id",
        "metadata",
    ]
    assert params(imported["Expectation"].match_alert) == [
        "self",
        "relevant_signature_types",
        "alert_data",
    ]
    assert params(imported["Expectation"].match_fuzzy) == [
        "tested",
        "reference",
        "threshold",
    ]
    assert params(imported["Expectation"].match_simple) == [
        "tested",
        "reference",
    ]
