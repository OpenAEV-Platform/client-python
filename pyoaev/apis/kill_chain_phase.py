from typing import Any, Dict, List

from pyoaev import exceptions as exc
from pyoaev.base import RESTManager, RESTObject


class KillChainPhase(RESTObject):
    _id_attr = "phase_id"


class KillChainPhaseManager(RESTManager):
    _path = "/kill_chain_phases"
    _obj_cls = KillChainPhase

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def upsert(
        self, kill_chain_phases: List[Dict[str, Any]], **kwargs: Any
    ) -> Dict[str, Any]:
        data = {"kill_chain_phases": kill_chain_phases}
        path = f"{self.path}/upsert"
        result = self.openaev.http_post(path, post_data=data, **kwargs)
        return result
