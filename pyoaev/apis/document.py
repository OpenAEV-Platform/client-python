from typing import Any, Dict

import xtm_oaev_sdk as exc

from pyoaev.base import RESTManager, RESTObject
from pyoaev.exceptions import on_http_error


class Document(RESTObject):
    _id_attr = "document_id"


class DocumentManager(RESTManager):
    _path = "/documents"
    _obj_cls = Document

    @on_http_error(exc.OpenAEVUpdateError)
    def download(self, document_id: str, **kwargs: Any) -> Dict[str, Any]:
        path = f"{self.path}/" + document_id + "/file"
        result = self.openaev.http_get(path, **kwargs)
        return result

    @on_http_error(exc.OpenAEVUpdateError)
    def upsert(
        self, document: Dict[str, Any], file: tuple, **kwargs: Any
    ) -> Dict[str, Any]:
        path = f"{self.path}/upsert"
        result = self.openaev.http_post(
            path, post_data=document, files={"file": file}, **kwargs
        )
        return result
