from typing import Any, Dict

import xtm_oaev_sdk as exc

from pyoaev.base import RESTManager, RESTObject
from pyoaev.exceptions import on_http_error


class Tag(RESTObject):
    _id_attr = "tag_id"


class TagManager(RESTManager):
    _path = "/tags"
    _obj_cls = Tag

    @on_http_error(exc.OpenAEVUpdateError)
    def upsert(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        path = f"{self.path}/upsert"
        result = self.openaev.http_post(path, post_data=data, **kwargs)
        return result
