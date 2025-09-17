from typing import Any, Dict

from pyobas import exceptions as exc
from pyobas.apis.inputs.search import InjectorContractSearchPaginationInput
from pyobas.base import RESTManager, RESTObject
from pyobas.mixins import CreateMixin, DeleteMixin, UpdateMixin
from pyobas.utils import RequiredOptional


class InjectorContract(RESTObject):
    pass


class InjectorContractManager(CreateMixin, UpdateMixin, DeleteMixin, RESTManager):
    _path = "/injector_contracts"
    _obj_cls = InjectorContract
    _create_attrs = RequiredOptional(
        required=(
            "contract_content",
            "contract_id",
            "contract_labels",
            "injector_id",
        ),
        optional=(
            "contract_attack_patterns_ids",
            "contract_attack_patterns_external_ids",
            "contract_vulnerability_external_ids",
            "contract_manual",
            "contract_platforms",
            "external_contract_id",
            "is_atomic_testing",
        ),
    )
    _update_attrs = RequiredOptional(
        required=(
            "contract_content",
            "contract_labels",
        ),
        optional=(
            "contract_attack_patterns_ids",
            "contract_vulnerability_ids",
            "contract_manual",
            "contract_platforms",
            "is_atomic_testing",
        ),
    )

    @exc.on_http_error(exc.OpenBASUpdateError)
    def search(
        self, input: InjectorContractSearchPaginationInput, **kwargs: Any
    ) -> Dict[str, Any]:
        path = f"{self.path}/search"
        # force the serialisation here since we only need a naive serialisation to json
        result = self.openbas.http_post(path, post_data=input.to_dict(), **kwargs)
        return result
