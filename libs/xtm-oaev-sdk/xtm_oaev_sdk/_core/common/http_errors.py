"""HTTP error translation: generic HTTP errors into operation-specific ones."""

from typing import Any, Callable

from xtm_oaev_sdk.seam.common import OpenAEVHttpError

__all__ = ["HttpErrorTranslator"]


class HttpErrorTranslator:
    """Implements ``HttpErrorPort``."""

    def call(
        self,
        function: Callable[..., Any],
        error: type[Exception],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        try:
            return function(*args, **kwargs)
        except OpenAEVHttpError as e:
            raise error(e.error_message, e.response_code, e.response_body) from e
