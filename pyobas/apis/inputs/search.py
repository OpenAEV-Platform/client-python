from typing import Dict, List


class Filter:
    def __init__(self, key: str, mode: str, operator: str, values: List[str]):
        self.key = key
        self.mode = mode
        self.operator = operator
        self.values = values


class FilterGroup:
    def __init__(self, mode: str, filters: List[Filter]):
        self.mode = mode
        self.filters = filters


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
        self.filter_group = filter_group
        self.text_search = text_search
        self.sorts = sorts


class InjectorContractSearchPaginationInput(SearchPaginationInput):
    def __init__(
        self,
        page: int,
        size: int,
        filter_group: FilterGroup,
        text_search: str,
        sorts: Dict[str, str],
        full_details: bool = True,
    ):
        super().__init__(page, size, filter_group, text_search, sorts)
        self.full_details = full_details
