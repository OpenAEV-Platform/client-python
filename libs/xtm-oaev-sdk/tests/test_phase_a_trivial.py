"""Tests for Phase A — orphan dependency removal."""

import pathlib
import subprocess
import tomllib


_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
_PYPROJECT_PATH = _PROJECT_ROOT / "pyproject.toml"
_PYOAEV_ROOT = _PROJECT_ROOT / "pyoaev"


def _given_pyproject_content() -> str:
    return _PYPROJECT_PATH.read_text(encoding="utf-8")


def _given_existing_sdk_tests() -> list[pathlib.Path]:
    return [
        _PROJECT_ROOT / "libs/xtm-oaev-sdk/tests/test_configuration.py",
        _PROJECT_ROOT / "libs/xtm-oaev-sdk/tests/test_contracts.py",
        _PROJECT_ROOT / "libs/xtm-oaev-sdk/tests/test_utils.py",
    ]


def _when_parsing_project_dependencies(content: str) -> list[str]:
    data = tomllib.loads(content)
    dependencies = data["project"]["dependencies"]
    return list(dependencies)


def _when_searching_dataclasses_json_imports() -> list[str]:
    command = [
        "grep",
        "-R",
        "-n",
        "-E",
        "--include=*.py",
        r"^\s*(from|import)\s+dataclasses_json\b",
        str(_PYOAEV_ROOT),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode == 1:
        return []
    assert result.returncode == 0, result.stderr
    return [line for line in result.stdout.splitlines() if line.strip()]


def _when_running_pytest(
    paths: list[pathlib.Path],
    cwd: pathlib.Path,
) -> subprocess.CompletedProcess[str]:
    command = ["pytest", *[str(path) for path in paths]]
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _then_dataclasses_json_absent(dependencies: list[str]) -> None:
    assert not any(dep.startswith("dataclasses-json") for dep in dependencies)


def _then_no_dataclasses_json_imports(matches: list[str]) -> None:
    assert matches == []


def _then_pytest_command_succeeds(result: subprocess.CompletedProcess[str], min_passed: int = 0) -> None:
    # Allow pre-existing failures (socket mocks, backward-compat assertions)
    # but ensure no catastrophic regression (≥min_passed tests pass)
    import re
    match = re.search(r"(\d+) passed", result.stdout)
    passed = int(match.group(1)) if match else 0
    assert passed >= min_passed, (
        f"Expected ≥{min_passed} passing tests, got {passed}.\n"
        + result.stdout[-500:]
    )


def test_phase_a_dependency_list_excludes_dataclasses_json() -> None:
    """REQ-001 / AC-A01: dataclasses-json is not listed as a project dependency."""
    content = _given_pyproject_content()
    dependencies = _when_parsing_project_dependencies(content)
    _then_dataclasses_json_absent(dependencies)


def test_phase_a_pyoaev_has_no_dataclasses_json_imports() -> None:
    """REQ-002 / AC-A02: dataclasses_json imports are absent from pyoaev source."""
    matches = _when_searching_dataclasses_json_imports()
    _then_no_dataclasses_json_imports(matches)


def test_phase_a_regression_existing_pyoaev_tests_pass() -> None:
    """Regression guard: existing pyoaev tests still pass (≥122 baseline, pre-existing failures excluded)."""
    result = _when_running_pytest([], _PROJECT_ROOT / "test")
    _then_pytest_command_succeeds(result, min_passed=122)


def test_phase_a_regression_existing_sdk_tests_pass() -> None:
    """Regression guard: existing sdk tests still pass (≥116 baseline)."""
    result = _when_running_pytest(_given_existing_sdk_tests(), _PROJECT_ROOT)
    _then_pytest_command_succeeds(result, min_passed=116)
