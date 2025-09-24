from typing import Any, Dict

from pyoaev import exceptions as exc
from pyoaev.base import RESTManager, RESTObject
from pyoaev.mixins import CreateMixin, ListMixin, UpdateMixin
from pyoaev.utils import RequiredOptional


class User(RESTObject):
    _id_attr = "user_id"


class UserManager(CreateMixin, ListMixin, UpdateMixin, RESTManager):
    _path = "/players"
    _obj_cls = User
    _create_attrs = RequiredOptional(
        required=("user_email",),
        optional=(
            "user_firstname",
            "user_lastname",
            "user_organization",
            "user_country",
            "user_tags",
        ),
    )

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def upsert(self, user: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        path = f"{self.path}/upsert"
        result = self.openaev.http_post(path, post_data=user, **kwargs)
        return result
