from typing import Any, Dict, List


class Filter:
    def __init__(self, key: str, mode: str, operator: str, values: List[str]):
        self.key = key
        self.mode = mode
        self.operator = operator
        self.values = values

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


class FilterGroup:
    def __init__(self, mode: str, filters: List[Filter]):
        self.mode = mode
        self.filters = filters

    def to_dict(self) -> dict[str, Any]:
        dictionary: dict[str, Any] = {"mode": self.mode}
        if self.filters:
            filter_dicts: List[dict[str, Any]] = []
            for filter_ in self.filters:
                filter_dicts.append(filter_.to_dict())
            dictionary["filters"] = filter_dicts
        return dictionary


class SearchPaginationInput:
    def __init__(
        self,
        page: int,
        size: int,
        filter_group: FilterGroup,
        text_search: str,
        sorts: Dict[str, str],
    ):
        self.size = size
        self.page = page
        self.filterGroup = filter_group
        self.text_search = text_search
        self.sorts = sorts

    def to_dict(self) -> dict[str, Any]:
        dictionary: dict[str, Any] = {"page": self.page, "size": self.size}
        if self.sorts:
            dictionary["sorts"] = self.sorts
        if self.text_search:
            dictionary["textSearch"] = self.text_search
        if self.filterGroup:
            dictionary["filterGroup"] = self.filterGroup.to_dict()
        return dictionary


class InjectorContractSearchPaginationInput(SearchPaginationInput):
    def __init__(
        self,
        page: int,
        size: int,
        filter_group: FilterGroup,
        text_search: str = None,
        sorts: Dict[str, str] = None,
        include_full_details: bool = True,
    ):
        super().__init__(page, size, filter_group, text_search, sorts)
        self.include_full_details = include_full_details

    def to_dict(self) -> dict[str, Any]:
        dictionary: dict[str, Any] = super().to_dict()
        dictionary["include_full_details"] = self.include_full_details
        return dictionary
