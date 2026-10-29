from unittest import TestCase, main, mock
from uuid import uuid4

from pyoaev import OpenAEV
from pyoaev.apis.inject_expectation.model import (
    DetectionExpectation,
    LoggingExpectation,
    PreventionExpectation,
)
from pyoaev.exceptions import OpenAEVHttpError, OpenAEVListError, OpenAEVParsingError


def make_json_response(payload):
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.history = None
            self.content = None
            self.headers = {"Content-Type": "application/json"}

        def json(self):
            return payload

    return MockResponse()


class TestAiExpectationsForSource(TestCase):
    @mock.patch("requests.Session.request")
    def test_returns_list_of_expectations(self, mock_request):
        expectations = [
            {"inject_expectation_id": "exp-1"},
            {"inject_expectation_id": "exp-2"},
        ]
        mock_request.return_value = make_json_response(expectations)
        api_client = OpenAEV("url", "token")

        result = api_client.inject_expectation.ai_expectations_for_source("collector-1")

        mock_request.assert_called_once()
        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["method"], "get")
        self.assertEqual(kwargs["url"], "url/api/injects/expectations/ai/collector-1")
        self.assertEqual(result, expectations)

    @mock.patch("requests.Session.request")
    def test_raises_parsing_error_when_not_a_list(self, mock_request):
        mock_request.return_value = make_json_response({"unexpected": "shape"})
        api_client = OpenAEV("url", "token")

        with self.assertRaises(OpenAEVParsingError):
            api_client.inject_expectation.ai_expectations_for_source("collector-1")

    @mock.patch("requests.Session.request")
    def test_raises_parsing_error_when_elements_not_dicts(self, mock_request):
        mock_request.return_value = make_json_response(["not", "a", "dict"])
        api_client = OpenAEV("url", "token")

        with self.assertRaises(OpenAEVParsingError) as ctx:
            api_client.inject_expectation.ai_expectations_for_source("collector-1")

        # The message should call out the offending element type, not just "list".
        self.assertIn("str", str(ctx.exception))

    def test_http_error_is_mapped_to_list_error(self):
        api_client = OpenAEV("url", "token")

        with mock.patch.object(
            OpenAEV, "http_get", side_effect=OpenAEVHttpError("boom")
        ):
            with self.assertRaises(OpenAEVListError):
                api_client.inject_expectation.ai_expectations_for_source("collector-1")


class TestLoggingExpectationsForSource(TestCase):
    @mock.patch("requests.Session.request")
    def test_returns_list_of_expectations_from_the_logging_route(self, mock_request):
        expectations = [
            {"inject_expectation_id": "exp-1"},
            {"inject_expectation_id": "exp-2"},
        ]
        mock_request.return_value = make_json_response(expectations)
        api_client = OpenAEV("url", "token")

        result = api_client.inject_expectation.logging_expectations_for_source(
            "collector-1"
        )

        mock_request.assert_called_once()
        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["method"], "get")
        self.assertEqual(
            kwargs["url"], "url/api/injects/expectations/logging/collector-1"
        )
        self.assertEqual(result, expectations)

    @mock.patch("requests.Session.request")
    def test_raises_parsing_error_when_not_a_list(self, mock_request):
        mock_request.return_value = make_json_response({"unexpected": "shape"})
        api_client = OpenAEV("url", "token")

        with self.assertRaises(OpenAEVParsingError):
            api_client.inject_expectation.logging_expectations_for_source("collector-1")

    @mock.patch("requests.Session.request")
    def test_raises_parsing_error_when_elements_not_dicts(self, mock_request):
        mock_request.return_value = make_json_response(["not", "a", "dict"])
        api_client = OpenAEV("url", "token")

        with self.assertRaises(OpenAEVParsingError):
            api_client.inject_expectation.logging_expectations_for_source("collector-1")

    def test_older_platform_404_returns_empty_list_and_warns_once(self):
        api_client = OpenAEV("url", "token")

        with mock.patch.object(
            OpenAEV,
            "http_get",
            side_effect=OpenAEVHttpError("Not Found", response_code=404),
        ):
            with self.assertLogs(
                "pyoaev.apis.inject_expectation.inject_expectation", level="DEBUG"
            ) as logs:
                first = api_client.inject_expectation.logging_expectations_for_source(
                    "collector-1"
                )
                second = api_client.inject_expectation.logging_expectations_for_source(
                    "collector-1"
                )

        self.assertEqual([], first)
        self.assertEqual([], second)
        warnings = [r for r in logs.records if r.levelname == "WARNING"]
        self.assertEqual(1, len(warnings))
        self.assertIn("/logging/collector-1", warnings[0].getMessage())

    def test_other_http_errors_are_mapped_to_list_error(self):
        api_client = OpenAEV("url", "token")

        with mock.patch.object(
            OpenAEV,
            "http_get",
            side_effect=OpenAEVHttpError("boom", response_code=500),
        ):
            with self.assertRaises(OpenAEVListError):
                api_client.inject_expectation.logging_expectations_for_source(
                    "collector-1"
                )


def make_expectation(expectation_type, signatures):
    return {
        "inject_expectation_id": str(uuid4()),
        "inject_expectation_type": expectation_type,
        "inject_expectation_signatures": signatures,
    }


class TestExpectationsModelsForSource(TestCase):
    def setUp(self):
        self.api_client = OpenAEV("url", "token")

    def models_for(self, expectations):
        with mock.patch.object(
            self.api_client.inject_expectation,
            "expectations_assets_for_source",
            return_value=expectations,
        ):
            return self.api_client.inject_expectation.expectations_models_for_source(
                "collector-1"
            )

    def test_builds_the_model_matching_each_expectation_type(self):
        signatures = [{"type": "process_name", "value": "obas-implant.exe"}]

        models = self.models_for(
            [
                make_expectation("DETECTION", signatures),
                make_expectation("PREVENTION", signatures),
            ]
        )

        self.assertEqual(
            [DetectionExpectation, PreventionExpectation],
            [type(model) for model in models],
        )

    def test_other_expectation_types_are_skipped_not_built_as_prevention(self):
        signatures = [{"type": "process_name", "value": "obas-implant.exe"}]
        detection = make_expectation("DETECTION", signatures)
        unknown = [
            make_expectation(expectation_type, signatures)
            for expectation_type in ("VULNERABILITY", "LOGGING", "FOO")
        ]

        with self.assertLogs(
            "pyoaev.apis.inject_expectation.inject_expectation", level="WARNING"
        ) as logs:
            models = self.models_for([detection, *unknown])

        self.assertEqual([DetectionExpectation], [type(model) for model in models])
        self.assertEqual(3, len(logs.records))
        for expectation, output in zip(unknown, logs.output):
            self.assertIn(expectation["inject_expectation_id"], output)
            self.assertIn(expectation["inject_expectation_type"], output)

    def test_an_invalid_expectation_does_not_hide_the_valid_ones(self):
        # Regression for client-python#352: signature types sent by SignatureManager
        # before the fix (start_time, source_ipv4, ...) are not SignatureTypes.
        valid_detection = make_expectation(
            "DETECTION", [{"type": "process_name", "value": "eicar.com"}]
        )
        legacy = make_expectation(
            "PREVENTION",
            [
                {"type": "start_time", "value": "2026-10-16T08:00:00Z"},
                {"type": "source_ipv4", "value": "10.0.0.5"},
            ],
        )
        valid_prevention = make_expectation(
            "PREVENTION", [{"type": "target_ipv4_address", "value": "192.0.2.11"}]
        )

        with self.assertLogs(
            "pyoaev.apis.inject_expectation.inject_expectation", level="WARNING"
        ) as logs:
            models = self.models_for([valid_detection, legacy, valid_prevention])

        self.assertEqual(
            [
                valid_detection["inject_expectation_id"],
                valid_prevention["inject_expectation_id"],
            ],
            [str(model.inject_expectation_id) for model in models],
        )
        self.assertEqual(1, len(logs.records))
        self.assertIn(legacy["inject_expectation_id"], logs.output[0])
        self.assertIn("PreventionExpectation", logs.output[0])

    def test_returns_an_empty_list_when_every_expectation_is_invalid(self):
        with self.assertLogs(
            "pyoaev.apis.inject_expectation.inject_expectation", level="WARNING"
        ) as logs:
            models = self.models_for(
                [
                    make_expectation("DETECTION", [{"type": "end_time", "value": "x"}]),
                    make_expectation("PREVENTION", [{"type": "process_name"}]),
                ]
            )

        self.assertEqual([], models)
        self.assertEqual(2, len(logs.records))

    def test_expectations_with_null_signatures_are_still_returned(self):
        models = self.models_for([make_expectation("DETECTION", None)])

        self.assertEqual(1, len(models))
        self.assertEqual([], models[0].inject_expectation_signatures)


class TestLoggingExpectationModelsForSource(TestCase):
    def setUp(self):
        self.api_client = OpenAEV("url", "token")

    def models_for(self, expectations):
        with mock.patch.object(
            self.api_client.inject_expectation,
            "logging_expectations_for_source",
            return_value=expectations,
        ):
            return self.api_client.inject_expectation.logging_expectation_models_for_source(
                "collector-1"
            )

    def test_builds_logging_expectations_with_logging_labels(self):
        models = self.models_for(
            [
                make_expectation(
                    "LOGGING",
                    [{"type": "parent_process_name", "value": "oaev-implant-1"}],
                )
            ]
        )

        self.assertEqual([LoggingExpectation], [type(model) for model in models])
        self.assertEqual("Logged", models[0].success_label)
        self.assertEqual("Not Logged", models[0].failure_label)

    def test_other_expectation_types_are_skipped(self):
        logging_expectation = make_expectation("LOGGING", [])
        detection = make_expectation("DETECTION", [])

        with self.assertLogs(
            "pyoaev.apis.inject_expectation.inject_expectation", level="WARNING"
        ) as logs:
            models = self.models_for([detection, logging_expectation])

        self.assertEqual(
            [logging_expectation["inject_expectation_id"]],
            [str(model.inject_expectation_id) for model in models],
        )
        self.assertEqual(1, len(logs.records))
        self.assertIn(detection["inject_expectation_id"], logs.output[0])

    def test_an_invalid_expectation_is_skipped_with_a_warning(self):
        valid = make_expectation(
            "LOGGING", [{"type": "source_ipv4_address", "value": "10.0.0.5"}]
        )
        invalid = make_expectation("LOGGING", [{"type": "start_time", "value": "x"}])

        with self.assertLogs(
            "pyoaev.apis.inject_expectation.inject_expectation", level="WARNING"
        ) as logs:
            models = self.models_for([invalid, valid])

        self.assertEqual(
            [valid["inject_expectation_id"]],
            [str(model.inject_expectation_id) for model in models],
        )
        self.assertEqual(1, len(logs.records))
        self.assertIn("LoggingExpectation", logs.output[0])

    def test_older_platform_returns_no_model(self):
        with mock.patch.object(
            OpenAEV,
            "http_get",
            side_effect=OpenAEVHttpError("Not Found", response_code=404),
        ):
            with self.assertLogs(
                "pyoaev.apis.inject_expectation.inject_expectation", level="WARNING"
            ):
                models = self.api_client.inject_expectation.logging_expectation_models_for_source(
                    "collector-1"
                )

        self.assertEqual([], models)


if __name__ == "__main__":
    main()
