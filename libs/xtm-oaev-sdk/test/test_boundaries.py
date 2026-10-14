"""SDK dependency and source-boundary assertions."""

import pathlib
import re
import subprocess
import sys

import pytest

_SDK_ROOT = pathlib.Path(__file__).resolve().parents[1] / "xtm_oaev_sdk"


def _when_searching_sdk_sources(pattern: str) -> list[tuple[str, str]]:
    regex = re.compile(pattern)
    return [
        (str(path.relative_to(_SDK_ROOT)), line)
        for path in sorted(_SDK_ROOT.rglob("*.py"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if regex.search(line)
    ]


@pytest.mark.parametrize("package", ["pyoaev", "requests", "pika", "thefuzz"])
def test_sdk_sources_do_not_import(package: str) -> None:
    """It never imports the legacy client nor its transport dependencies."""
    pattern = rf"^\s*(?:from|import)\s+{package}(?:\.|\b)"
    assert _when_searching_sdk_sources(pattern) == []


@pytest.mark.parametrize(
    "artifact",
    [
        "class ListenQueue",
        "class PingAlive",
        "class OpenAEVConfigHelper",
        "class OpenAEVCollectorHelper",
        "class OpenAEVInjectorHelper",
        "class OpenAEVDetectionHelper",
        "def create_mq_ssl_context",
    ],
)
def test_sdk_sources_do_not_define_client_helpers(artifact: str) -> None:
    """It leaves transport and daemon helpers to the client."""
    assert _when_searching_sdk_sources(rf"^\s*{artifact}\b") == []


def _sdk_modules() -> list[str]:
    package_root = _SDK_ROOT.parent
    return sorted(
        ".".join(path.relative_to(package_root).with_suffix("").parts).removesuffix(
            ".__init__"
        )
        for path in _SDK_ROOT.rglob("*.py")
    )


@pytest.mark.parametrize("module", _sdk_modules())
def test_every_sdk_module_imports_first_in_a_fresh_interpreter(module: str) -> None:
    """It has no import cycle hidden by a lucky import order."""
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", f"import {module}"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
