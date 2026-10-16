"""Contract assembly: what a builder does to the fields it collects."""

from typing import Any

from xtm_oaev_sdk.seam.contracts import ContractElement

__all__ = ["ContractAssembly"]


class ContractAssembly:
    """Implements ``ContractAssemblyPort``."""

    def concat(self, existing: list[Any], extra: list[Any]) -> list[Any]:
        return existing + extra

    def set_mandatory(
        self, element: ContractElement, mandatory: bool
    ) -> ContractElement:
        element.mandatory = mandatory
        return element

    def require_group(self, elements: list[ContractElement]) -> list[ContractElement]:
        keys: list[str] = list(map(lambda iterable: iterable.key, elements))
        for element in elements:
            element.mandatory = True
            element.mandatoryGroups = keys
        return elements
