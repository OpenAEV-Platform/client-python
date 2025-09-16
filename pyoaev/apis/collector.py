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
