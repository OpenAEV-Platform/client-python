from typing import Any, Dict, Optional

import requests

from pyoaev import exceptions as exc
from pyoaev.base import RESTManager, RESTObject
from pyoaev.credential.errors import (
    CredentialErrorCode,
    CredentialResolutionError,
    credential_error_code_from_http,
)


class Inject(RESTObject):
    _id_attr = None


class InjectManager(RESTManager):
    _path = "/injects"
    _obj_cls = Inject

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def execution_callback(
        self, inject_id: str, data: Dict[str, Any], **kwargs: Any
    ) -> Dict[str, Any]:
        path = f"{self.path}/execution/callback/{inject_id}"
        result = self.openaev.http_post(path, post_data=data, **kwargs)
        return result

    @exc.on_http_error(exc.OpenAEVUpdateError)
    def execution_reception(
        self, inject_id: str, data: Dict[str, Any], **kwargs: Any
    ) -> Dict[str, Any]:
        path = f"{self.path}/execution/reception/{inject_id}"
        result = self.openaev.http_post(path, post_data=data, **kwargs)
        return result

    def resolve_attachment_secret(
        self, inject_id: str, attachment_id: str, authorisation: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """Resolve the secret of a credential attached to an inject.

        Must be called while the inject is being executed, with the
        authorisation code received with the job. The tenant prefix is added
        by the client when a tenant id is configured.

        Raises:
            CredentialResolutionError: on any failure. The request and response
                bodies are never logged nor kept on the error.
        """
        path = f"{self.path}/{inject_id}/attachment/secret"
        data = {"attachment_id": attachment_id, "authorisation": authorisation}
        error_code: Optional[CredentialErrorCode] = None
        response_code: Optional[int] = None
        # The error is raised outside of the except blocks so the original
        # exception, which holds the response body, is not chained to it.
        try:
            result = self.openaev.http_post(path, post_data=data, **kwargs)
        except exc.OpenAEVError as e:
            response_code = e.response_code
            error_code = credential_error_code_from_http(
                e.response_code, e.error_message
            )
        except requests.RequestException:
            error_code = CredentialErrorCode.CREDENTIAL_ACCESS_DENIED
        else:
            if not isinstance(result, dict):
                error_code = CredentialErrorCode.CREDENTIAL_ACCESS_DENIED
        if error_code is not None:
            raise CredentialResolutionError(
                error_code, reference=attachment_id, response_code=response_code
            )
        return result
