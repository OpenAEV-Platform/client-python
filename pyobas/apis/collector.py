from typing import Any, Dict

from pyoaev import exceptions as exc
from pyoaev.base import RESTManager, RESTObject
from pyoaev.mixins import CreateMixin, GetMixin, ListMixin, UpdateMixin
from pyoaev.utils import RequiredOptional


class Collector(RESTObject):
    pass


class CollectorManager(GetMixin, ListMixin, CreateMixin, UpdateMixin, RESTManager):
    _path = "/collectors"
    _obj_cls = Collector
    _create_attrs = RequiredOptional(
        required=(
            "collector_id",
            "collector_name",
            "collector_type",
            "collector_period",
        )
    )

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def get(self, collector_id: str, **kwargs: Any) -> Dict[str, Any]:
        path = f"{self.path}/" + collector_id
        result = self.openaev.http_get(path, **kwargs)
        return result
