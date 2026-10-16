from typing import Any, Dict

import xtm_oaev_sdk as exc

from pyoaev.base import RESTManager, RESTObject
from pyoaev.exceptions import on_http_error


class Cve(RESTObject):
    _id_attr = "cve_id"


class CveManager(RESTManager):
    _path = "/cves"

    @on_http_error(exc.OpenAEVUpdateError)
    def upsert(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        path = f"{self.path}/bulk"
        result = self.openaev.http_post(path, post_data=data, **kwargs)
        return result
