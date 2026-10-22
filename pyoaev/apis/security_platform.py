from typing import Any, Dict

import xtm_oaev_sdk as exc

from pyoaev.base import RESTManager, RESTObject
from pyoaev.exceptions import on_http_error
from pyoaev.mixins import CreateMixin, GetMixin, ListMixin, UpdateMixin
from pyoaev.utils import RequiredOptional


class SecurityPlatform(RESTObject):
    pass


class SecurityPlatformManager(
    GetMixin, ListMixin, CreateMixin, UpdateMixin, RESTManager
):
    _path = "/security_platforms"
    _obj_cls = SecurityPlatform
    _create_attrs = RequiredOptional(
        required=("asset_name", "security_platform_type"),
        optional=(
            "asset_description",
            "security_platform_logo_light",
            "security_platform_logo_dark",
        ),
    )

    @on_http_error(exc.OpenAEVUpdateError)
    def upsert(
        self, security_platform: Dict[str, Any], **kwargs: Any
    ) -> Dict[str, Any]:
        path = f"{self.path}/upsert"
        result = self.openaev.http_post(path, post_data=security_platform, **kwargs)
        return result
