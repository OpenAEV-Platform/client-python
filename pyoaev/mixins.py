import enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

import requests

import pyoaev
from pyoaev import base
from pyoaev import exceptions as exc
from pyoaev import utils

__all__ = [
    "GetMixin",
    "GetWithoutIdMixin",
]

if TYPE_CHECKING:
    # When running mypy we use these as the base classes
    _RestManagerBase = base.RESTManager
    _RestObjectBase = base.RESTObject
else:
    _RestManagerBase = object
    _RestObjectBase = object


class HeadMixin(_RestManagerBase):
    @exc.on_http_error(exc.OpenAEVHeadError)
    def head(
        self, id: Optional[Union[str, int]] = None, **kwargs: Any
    ) -> "requests.structures.CaseInsensitiveDict[Any]":
        if TYPE_CHECKING:
            assert self.path is not None

        path = self.path
        if id is not None:
            path = f"{path}/{utils.EncodedId(id)}"

        return self.openaev.http_head(path, **kwargs)


class GetMixin(HeadMixin, _RestManagerBase):
    _computed_path: Optional[str]
    _from_parent_attrs: Dict[str, Any]
    _obj_cls: Optional[Type[base.RESTObject]]
    _optional_get_attrs: Tuple[str, ...] = ()
    _parent: Optional[base.RESTObject]
    _parent_attrs: Dict[str, Any]
    _path: Optional[str]
    openaev: pyoaev.OpenAEV

    @exc.on_http_error(exc.OpenAEVGetError)
    def get(self, id: Union[str, int], **kwargs: Any) -> base.RESTObject:
        if isinstance(id, str):
            id = utils.EncodedId(id)
        path = f"{self.path}/{id}"
        if TYPE_CHECKING:
            assert self._obj_cls is not None
        server_data = self.openaev.http_get(path, **kwargs)
        if TYPE_CHECKING:
            assert not isinstance(server_data, requests.Response)
        return self._obj_cls(self, server_data)


class GetWithoutIdMixin(HeadMixin, _RestManagerBase):
    _computed_path: Optional[str]
    _from_parent_attrs: Dict[str, Any]
    _obj_cls: Optional[Type[base.RESTObject]]
    _optional_get_attrs: Tuple[str, ...] = ()
    _parent: Optional[base.RESTObject]
    _parent_attrs: Dict[str, Any]
    _path: Optional[str]
    openaev: pyoaev.OpenAEV

    @exc.on_http_error(exc.OpenAEVGetError)
    def get(self, **kwargs: Any) -> base.RESTObject:
        if TYPE_CHECKING:
            assert self.path is not None
        server_data = self.openaev.http_get(self.path, **kwargs)
        if TYPE_CHECKING:
            assert not isinstance(server_data, requests.Response)
            assert self._obj_cls is not None
        return self._obj_cls(self, server_data)


class ListMixin(HeadMixin, _RestManagerBase):
    _computed_path: Optional[str]
    _from_parent_attrs: Dict[str, Any]
    _list_filters: Tuple[str, ...] = ()
    _obj_cls: Optional[Type[base.RESTObject]]
    _parent: Optional[base.RESTObject]
    _parent_attrs: Dict[str, Any]
    _path: Optional[str]
    openaev: pyoaev.OpenAEV

    @exc.on_http_error(exc.OpenAEVListError)
    def list(self, **kwargs: Any) -> Union[base.RESTObjectList, List[base.RESTObject]]:

        if self.openaev.per_page:
            kwargs.setdefault("per_page", self.openaev.per_page)

        # global keyset pagination
        if self.openaev.pagination:
            kwargs.setdefault("pagination", self.openaev.pagination)

        if self.openaev.order_by:
            kwargs.setdefault("order_by", self.openaev.order_by)

        # Allow to overwrite the path, handy for custom listings
        path = kwargs.pop("path", self.path)

        if TYPE_CHECKING:
            assert self._obj_cls is not None
        obj = self.openaev.http_list(path, **kwargs)
        if isinstance(obj, list):
            return [self._obj_cls(self, item, created_from_list=True) for item in obj]
        return base.RESTObjectList(self, self._obj_cls, obj)


@enum.unique
class UpdateMethod(enum.IntEnum):
    PUT = 1
    POST = 2
    PATCH = 3


class UpdateMixin(_RestManagerBase):
    _computed_path: Optional[str]
    _from_parent_attrs: Dict[str, Any]
    _obj_cls: Optional[Type[base.RESTObject]]
    _parent: Optional[base.RESTObject]
    _parent_attrs: Dict[str, Any]
    _path: Optional[str]
    _update_method: UpdateMethod = UpdateMethod.PUT
    openaev: pyoaev.OpenAEV

    def _get_update_method(
        self,
    ) -> Callable[..., Union[Dict[str, Any], requests.Response]]:
        """Return the HTTP method to use.

        Returns:
            http_put (default) or http_post
        """
        if self._update_method is UpdateMethod.POST:
            http_method = self.openaev.http_post
        elif self._update_method is UpdateMethod.PATCH:
            # only patch uses required kwargs, so our types are a bit misaligned
            http_method = self.openaev.http_patch  # type: ignore[assignment]
        else:
            http_method = self.openaev.http_put
        return http_method

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def update(
        self,
        id: Optional[Union[str, int]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        new_data = new_data or {}

        if id is None:
            path = self.path
        else:
            path = f"{self.path}/{utils.EncodedId(id)}"

        # excludes = []
        # if self._obj_cls is not None and self._obj_cls._id_attr is not None:
        #    excludes = [self._obj_cls._id_attr]
        # self._update_attrs.validate_attrs(data=new_data, excludes=excludes)
        http_method = self._get_update_method()
        result = http_method(path, post_data=new_data, **kwargs)
        if TYPE_CHECKING:
            assert not isinstance(result, requests.Response)
        return result


class CreateMixin(_RestManagerBase):
    _computed_path: Optional[str]
    _from_parent_attrs: Dict[str, Any]
    _obj_cls: Optional[Type[base.RESTObject]]
    _parent: Optional[base.RESTObject]
    _parent_attrs: Dict[str, Any]
    _path: Optional[str]
    openaev: pyoaev.OpenAEV

    @exc.on_http_error(exc.OpenAEVCreateError)
    def create(
        self, data: Optional[Dict[str, Any]] = None, icon: tuple = None, **kwargs: Any
    ) -> base.RESTObject:
        if data is None:
            data = {}
        self._create_attrs.validate_attrs(data=data)
        # Handle specific URL for creation
        path = kwargs.pop("path", self.path)

        if icon:
            files = {"icon": icon}
        elif icon is False:
            files = {}
        else:
            files = None
        server_data = self.openaev.http_post(
            path, post_data=data, files=files, **kwargs
        )
        if TYPE_CHECKING:
            assert not isinstance(server_data, requests.Response)
            assert self._obj_cls is not None
        return self._obj_cls(self, server_data)


class DeleteMixin(_RestManagerBase):
    _computed_path: Optional[str]
    _from_parent_attrs: Dict[str, Any]
    _obj_cls: Optional[Type[base.RESTObject]]
    _parent: Optional[base.RESTObject]
    _parent_attrs: Dict[str, Any]
    _path: Optional[str]
    openaev: pyoaev.OpenAEV

    @exc.on_http_error(exc.OpenAEVCreateError)
    def delete(
        self, id: Optional[Union[str, int]] = None, **kwargs: Any
    ) -> requests.Response:
        if id is None:
            path = self.path
        else:
            path = f"{self.path}/{utils.EncodedId(id)}"

        result = self.openaev.http_delete(path, **kwargs)
        if TYPE_CHECKING:
            assert isinstance(result, requests.Response)
        return result
