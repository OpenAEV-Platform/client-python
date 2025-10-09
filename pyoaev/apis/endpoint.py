from typing import Any, Dict

from pyoaev import exceptions as exc
from pyoaev.apis.inputs.search import SearchPaginationInput
from pyoaev.base import RESTManager, RESTObject
from pyoaev.utils import RequiredOptional


class Endpoint(RESTObject):
    _id_attr = "asset_id"


class EndpointManager(RESTManager):
    _path = "/endpoints"
    _obj_cls = Endpoint
    _create_attrs = RequiredOptional(
        required=(
            "endpoint_hostname",
            "endpoint_platform",
            "endpoint_arch",
        ),
        optional=(
            "endpoint_mac_addresses",
            "endpoint_ips",
            "asset_external_reference",
        ),
    )

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def get(self, asset_id: str, **kwargs: Any) -> Dict[str, Any]:
        path = f"{self.path}/" + asset_id
        result = self.openaev.http_get(path, **kwargs)
        return result

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def upsert(self, endpoint: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        path = f"{self.path}/agentless/upsert"
        result = self.openaev.http_post(path, post_data=endpoint, **kwargs)
        return result

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def search(
            self, input: SearchPaginationInput, **kwargs: Any
    ) -> Dict[str, Any]:
        path = f"{self.path}/targets"
        result = self.openaev.http_post(path, post_data=input.to_dict(), **kwargs)
        return result
