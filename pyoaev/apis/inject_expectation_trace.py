from typing import Any, Dict, List

from pyoaev import exceptions as exc
from pyoaev.base import RESTManager, RESTObject
from pyoaev.mixins import CreateMixin
from pyoaev.utils import RequiredOptional


class InjectExpectationTrace(RESTObject):
    _id_attr = "inject_expectation_trace_id"


class InjectExpectationTraceManager(CreateMixin, RESTManager):
    _path = "/inject-expectations-traces"
    _obj_cls = InjectExpectationTrace
    _create_attrs = RequiredOptional(
        required=(
            "inject_expectation_trace_expectation",
            "inject_expectation_trace_source_id",
            "inject_expectation_trace_alert_name",
            "inject_expectation_trace_alert_link",
            "inject_expectation_trace_date",
        ),
    )

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def bulk_create(
        self, payload: Dict[str, List[Dict[str, str]]], **kwargs: Any
    ) -> dict[str, Any]:
        path = f"{self.path}/bulk"
        result = self.openaev.http_post(
            path,
            post_data=payload,
            **kwargs,
        )
        return result
