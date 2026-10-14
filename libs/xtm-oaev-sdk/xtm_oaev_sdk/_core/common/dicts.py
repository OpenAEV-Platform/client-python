"""Dict tools: reshape the dictionaries exchanged with the platform."""

from typing import Any

__all__ = ["DictTools"]


class DictTools:
    """Implements ``DictToolsPort``."""

    def copy_dict(self, *, src: dict[str, Any], dest: dict[str, Any]) -> None:
        for k, v in src.items():
            if isinstance(v, dict):
                for dict_k, dict_v in v.items():
                    dest[f"{k}[{dict_k}]"] = dict_v
            else:
                dest[k] = v

    def remove_none_from_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in data.items() if v is not None}
