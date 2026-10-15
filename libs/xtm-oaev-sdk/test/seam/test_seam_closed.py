"""The two wire-facing seam modules stay closed to the SDK internals."""

import ast
from pathlib import Path

from xtm_oaev_sdk.seam.port_io import models as port_io_models
from xtm_oaev_sdk.seam.signatures import seam as seam_module


def test_port_io_models_import_only_the_signatures_seam():
    """The wire contract is closed: no import of the capability internals."""
    source = Path(port_io_models.__file__).read_text()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "xtm_oaev_sdk"
        ):
            assert node.module == "xtm_oaev_sdk.seam.signatures.seam", node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("xtm_oaev_sdk"), alias.name


def test_seam_imports_nothing_from_capability():
    """The seam is pure data: no imports from xtm_oaev_sdk itself."""
    source = Path(seam_module.__file__).read_text()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(
                    "xtm_oaev_sdk"
                ), f"seam imports capability module {alias.name!r} — pure-data violation"
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert not module.startswith(
                "xtm_oaev_sdk"
            ), f"seam imports from capability module {module!r} — pure-data violation"
