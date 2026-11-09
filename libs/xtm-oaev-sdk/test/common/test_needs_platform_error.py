"""Tests for the error of a call only the platform can answer.

Feature: A call that needs the platform
  A daemon running without the platform (dev mode) gets a stand-in for the platform
  client. A call only the platform can answer fails with an error naming the call, so the
  developer knows what dev mode cannot do instead of meeting a bare attribute error.
"""

from typing import Any

import xtm_oaev_sdk as sdk


def _given_needs_platform_error() -> Any:
    """Given the SDK has an error for the calls that need the platform"""
    error = getattr(sdk, "NeedsPlatformError", None)
    assert error is not None, "Expected xtm_oaev_sdk.NeedsPlatformError"
    return error


def _when_raising_for(error: Any, call: str) -> Exception:
    """When a dev stand-in refuses "<call>" """
    try:
        raise error(call)
    except Exception as raised:  # pylint: disable=broad-except
        return raised


def test_a_call_that_needs_the_platform_fails_naming_it() -> None:
    """It names the call and says dev mode cannot answer it.

    Scenario: A call that needs the platform fails, naming it
      Given the SDK has an error for the calls that need the platform
      When a dev stand-in refuses "document.download"
      Then the error is an OpenAEV error
      And it names "document.download" and says it needs the platform, not available in dev mode
    """
    error = _given_needs_platform_error()
    raised = _when_raising_for(error, "document.download")
    assert isinstance(raised, sdk.OpenAEVError)
    assert raised.call == "document.download"
    assert str(raised) == (
        "document.download needs the platform: not available in dev mode"
    )
