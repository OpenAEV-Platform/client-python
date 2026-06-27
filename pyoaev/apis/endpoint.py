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
    # asset_name is the only required attribute. Everything else - including endpoint_hostname,
    # endpoint_platform and endpoint_arch - is optional: agents and collectors typically provide
    # the endpoint fields, while category-driven assets (web app, cloud, network, ...) may omit
    # them and the platform defaults endpoint_platform / endpoint_arch to "Unknown" server-side.
    _create_attrs = RequiredOptional(
        required=("asset_name",),
        optional=(
            "endpoint_hostname",
            "endpoint_platform",
            "endpoint_arch",
            "endpoint_ips",
            "endpoint_mac_addresses",
            "endpoint_url",
            "asset_description",
            "asset_external_reference",
            "asset_tags",
            "asset_category",
            "asset_subcategory",
            "asset_criticality",
            "asset_internet_facing",
            "asset_cloud_provider",
            "asset_cloud_native_type",
            "asset_cloud_region",
            "asset_metadata",
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
    def searchTargets(
        self, input: SearchPaginationInput, **kwargs: Any
    ) -> Dict[str, Any]:
        path = f"{self.path}/targets"
        result = self.openaev.http_post(path, post_data=input.to_dict(), **kwargs)
        return result
