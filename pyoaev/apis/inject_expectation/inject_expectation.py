import logging
from typing import Any, Dict, List, Type, TypeVar

from pydantic import ValidationError

from pyoaev import exceptions as exc
from pyoaev.apis.inject_expectation.model import (
    DetectionExpectation,
    ExpectationTypeEnum,
    LoggingExpectation,
    PreventionExpectation,
)
from pyoaev.apis.inject_expectation.model.expectation import Expectation
from pyoaev.base import RESTManager, RESTObject
from pyoaev.mixins import ListMixin, UpdateMixin
from pyoaev.utils import RequiredOptional

logger = logging.getLogger(__name__)

ExpectationModel = TypeVar("ExpectationModel", bound=Expectation)

# Expectation models built by expectations_models_for_source, by expectation type.
# The /assets route only returns these two types.
_ASSET_EXPECTATION_MODELS: Dict[str, Type[Expectation]] = {
    ExpectationTypeEnum.Detection.value: DetectionExpectation,
    ExpectationTypeEnum.Prevention.value: PreventionExpectation,
}
_LOGGING_EXPECTATION_MODELS: Dict[str, Type[LoggingExpectation]] = {
    ExpectationTypeEnum.Logging.value: LoggingExpectation,
}


def _as_list_of_dicts(
    raw: Any, path: str, label: str, item_label: str
) -> List[Dict[str, Any]]:
    """Checks that a server response is a JSON list of objects.

    :param label: what the list holds, in the plural (e.g. "AI expectations")
    :param item_label: the same, in the singular (e.g. "AI expectation")

    :raises OpenAEVParsingError: if it is not
    """
    if not isinstance(raw, list):
        raise exc.OpenAEVParsingError(
            error_message=(
                f"Expected a list of {label} from {path}, got {type(raw).__name__}"
            )
        )
    for item in raw:
        if not isinstance(item, dict):
            raise exc.OpenAEVParsingError(
                error_message=(
                    f"Expected {item_label} objects (dicts) from {path}, "
                    f"got a list element of type {type(item).__name__}"
                )
            )
    return [item for item in raw]


class InjectExpectation(RESTObject):
    _id_attr = "inject_expectation_id"


class InjectExpectationManager(ListMixin, UpdateMixin, RESTManager):
    _path = "/injects/expectations"
    _obj_cls = InjectExpectation
    _update_attrs = RequiredOptional(required=("collector_id", "result", "is_success"))
    # Whether the missing LOGGING route of an older platform was already reported.
    _logging_route_missing_reported = False

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def expectations_assets_for_source(
        self, source_id: str, expiration_time: int = None, **kwargs: Any
    ) -> List[Dict[str, Any]]:
        path = f"{self.path}/assets/" + source_id
        # The route returns a JSON list; http_get is annotated Union[Dict, Response].
        result: Any = self.openaev.http_get(
            path,
            query_data=(
                {"expiration_time": expiration_time}
                if expiration_time
                else {
                    "expiration_time": 360
                }  # 360 minutes (6 hours) - corresponds to the expiration time configured in the Expectations Expiration Manager.
                # Expectations older than this duration will be automatically expired to prevent
                # processing outdated data, particularly important when launching new collectors.
            ),
            **kwargs,
        )
        return result

    @exc.on_http_error(exc.OpenAEVListError)
    def ai_expectations_for_source(
        self, source_id: str, **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Returns agentless DETECTION/PREVENTION expectations (AI adversarial injects) not yet
        filled for the given source. Used by AI defense collectors (LLM firewall / guardrail).

        :param source_id: the identifier of the collector requesting expectations
        :type source_id: str
        :raises OpenAEVParsingError: if the server does not return a JSON list of dicts
        :return: a list of agentless detection/prevention expectation dicts
        :rtype: list[dict]
        """
        path = f"{self.path}/ai/{source_id}"
        # http_get is annotated Union[Dict, requests.Response]; widen to Any so the list
        # validation stays meaningful to type checkers.
        raw: Any = self.openaev.http_get(path, **kwargs)
        return _as_list_of_dicts(raw, path, "AI expectations", "AI expectation")

    @exc.on_http_error(exc.OpenAEVListError)
    def logging_expectations_for_source(
        self, source_id: str, **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Returns the LOGGING expectations not yet filled for the given source.

        Only collectors that declare LOGGING in their supported expectation
        types receive them. An older platform without the LOGGING route answers
        404: it is treated as "no LOGGING expectation", with a warning.

        :param source_id: the identifier of the collector requesting expectations
        :type source_id: str
        :raises OpenAEVParsingError: if the server does not return a JSON list of dicts
        :return: a list of logging expectation dicts
        :rtype: list[dict]
        """
        path = f"{self.path}/logging/{source_id}"
        try:
            raw: Any = self.openaev.http_get(path, **kwargs)
        except exc.OpenAEVHttpError as err:
            if err.response_code != 404:
                raise
            self._report_missing_logging_route(path)
            return []
        return _as_list_of_dicts(
            raw, path, "Logging expectations", "Logging expectation"
        )

    def _report_missing_logging_route(self, path: str) -> None:
        if self._logging_route_missing_reported:
            logger.debug("%s answered 404, no LOGGING expectation collected", path)
            return
        self._logging_route_missing_reported = True
        logger.warning(
            "%s answered 404: this OpenAEV platform does not support LOGGING "
            "expectations yet, none will be collected",
            path,
        )

    def logging_expectation_models_for_source(
        self, source_id: str, **kwargs: Any
    ) -> List[LoggingExpectation]:
        """Returns the LOGGING expectations from OpenAEV that have had no result
            yet from the source_id (e.g. collector), as models.

        :param source_id: the identifier of the collector requesting expectations
        :type source_id: str
        :param kwargs: additional data to pass to the endpoint
        :type kwargs: dict, optional

        :return: a list of expectation objects
        :rtype: list[LoggingExpectation]
        """
        return self._models_from_dicts(
            self.logging_expectations_for_source(source_id=source_id, **kwargs),
            _LOGGING_EXPECTATION_MODELS,
        )

    def expectations_models_for_source(
        self, source_id: str, **kwargs: Any
    ) -> List[Expectation]:
        """Returns all expectations from OpenAEV that have had no result yet
            from the source_id (e.g. collector).

        :param source_id: the identifier of the collector requesting expectations
        :type source_id: str
        :param kwargs: additional data to pass to the endpoint
        :type kwargs: dict, optional

        :return: a list of expectation objects
        :rtype: list[DetectionExpectation|PreventionExpectation]
        """
        return self._models_from_dicts(
            self.expectations_assets_for_source(source_id=source_id, **kwargs),
            _ASSET_EXPECTATION_MODELS,
        )

    def _models_from_dicts(
        self,
        expectation_dicts: List[Dict[str, Any]],
        model_by_type: Dict[str, Type[ExpectationModel]],
    ) -> List[ExpectationModel]:
        """Builds the model of each expectation dict, by expectation type.

        A type missing from model_by_type is skipped with a warning, never
        mapped to another model: a collector must not answer an expectation
        type it does not handle.
        """
        expectations: List[ExpectationModel] = []
        for expectation_dict in expectation_dicts:
            expectation_type: str = (
                expectation_dict.get("inject_expectation_type") or ""
            )
            expectation_class = model_by_type.get(expectation_type)
            if expectation_class is None:
                logger.warning(
                    "Skipping expectation %s, its type %s is not one of %s",
                    expectation_dict.get("inject_expectation_id"),
                    expectation_type,
                    ", ".join(model_by_type),
                )
                continue
            # One invalid expectation (e.g. an unknown signature type) must not
            # hide the valid ones from the collector.
            try:
                expectations.append(
                    expectation_class(**expectation_dict, api_client=self)
                )
            except ValidationError as err:
                logger.warning(
                    "Skipping expectation %s, it does not match the %s model: %s",
                    expectation_dict.get("inject_expectation_id"),
                    expectation_class.__name__,
                    err,
                )
        return expectations

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def prevention_expectations_for_source(
        self, source_id: str, **kwargs: Any
    ) -> Dict[str, Any]:
        path = f"{self.path}/prevention" + source_id
        result = self.openaev.http_get(path, **kwargs)
        return result

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def detection_expectations_for_source(
        self, source_id: str, expiration_time: int = None, **kwargs: Any
    ) -> Dict[str, Any]:
        path = f"{self.path}/detection/" + source_id
        result = self.openaev.http_get(
            path,
            query_data=(
                {"expiration_time": expiration_time} if expiration_time else None
            ),
            **kwargs,
        )
        return result

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def update(
        self,
        inject_expectation_id: str,
        inject_expectation: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        path = f"{self.path}/{inject_expectation_id}"
        result = self.openaev.http_put(path, post_data=inject_expectation, **kwargs)
        return result

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def bulk_update(
        self,
        inject_expectation_input_by_id: Dict[str, Dict[str, Any]],
        **kwargs: Any,
    ) -> None:
        path = f"{self.path}/bulk"
        self.openaev.http_put(
            path, post_data={"inputs": inject_expectation_input_by_id}, **kwargs
        )
