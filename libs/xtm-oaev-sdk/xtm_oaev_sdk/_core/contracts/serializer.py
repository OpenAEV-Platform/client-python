"""Contract serialization into platform API payloads."""

import json
from typing import Any

from xtm_oaev_sdk._core.common import JsonEncoding
from xtm_oaev_sdk.seam.contracts import ContractData

__all__ = ["ContractSerializer"]


class ContractSerializer:
    """Implements ``ContractSerializerPort``."""

    def __init__(self) -> None:
        self._encoding = JsonEncoding()

    def to_add_input(self, contract: ContractData, source_id: str) -> dict[str, Any]:
        """Serialize a contract for the platform creation API.

        Args:
            source_id: The injector ID that owns this contract.

        Returns:
            Dict payload for the contract creation endpoint.
        """
        return {
            "contract_id": contract.contract_id,
            "external_contract_id": contract.external_id,
            "injector_id": source_id,
            "contract_manual": contract.manual,
            "contract_labels": contract.label,
            "contract_attack_patterns_external_ids": contract.contract_attack_patterns_external_ids,
            "contract_vulnerability_external_ids": contract.contract_vulnerability_external_ids,
            "contract_content": json.dumps(
                contract, default=self._encoding.encode_default
            ),
            "is_atomic_testing": contract.is_atomic_testing,
            "contract_platforms": contract.platforms,
            "contract_domains": contract.domains,
        }

    def to_update_input(self, contract: ContractData) -> dict[str, Any]:
        """Serialize a contract for the platform update API.

        Returns:
            Dict payload for the contract update endpoint.
        """
        return {
            "contract_manual": contract.manual,
            "contract_labels": contract.label,
            "contract_attack_patterns_external_ids": contract.contract_attack_patterns_external_ids,
            "contract_vulnerability_external_ids": contract.contract_vulnerability_external_ids,
            "contract_content": json.dumps(
                contract, default=self._encoding.encode_default
            ),
            "is_atomic_testing": contract.is_atomic_testing,
            "contract_platforms": contract.platforms,
            "contract_domains": contract.domains,
        }

    def prepare(self, contracts: list[ContractData]) -> list[dict[str, Any]]:
        """Serialize a list of contracts for bulk platform registration.

        Args:
            contracts: List of Contract instances to serialize.

        Returns:
            List of dicts suitable for the bulk contract registration API.
        """
        return list(
            map(
                lambda c: {
                    "contract_id": c.contract_id,
                    "contract_labels": c.label,
                    "contract_attack_patterns_external_ids": c.contract_attack_patterns_external_ids,
                    "contract_content": json.dumps(
                        c, default=self._encoding.encode_default
                    ),
                    "contract_platforms": c.platforms,
                    "contract_domains": c.domains,
                },
                contracts,
            )
        )
