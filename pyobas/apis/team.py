from typing import Any, Dict

from pyoaev import exceptions as exc
from pyoaev.base import RESTManager, RESTObject
from pyoaev.mixins import CreateMixin, ListMixin, UpdateMixin
from pyoaev.utils import RequiredOptional


class Team(RESTObject):
    _id_attr = "team_id"


class TeamManager(CreateMixin, ListMixin, UpdateMixin, RESTManager):
    _path = "/teams"
    _obj_cls = Team
    _create_attrs = RequiredOptional(
        required=("team_name",),
        optional=("team_description", "team_organization", "team_tags"),
    )

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def upsert(self, team: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        path = f"{self.path}/upsert"
        result = self.openaev.http_post(path, post_data=team, **kwargs)
        return result
