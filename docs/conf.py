import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "OpenAEV client for Python"
copyright = "2024, Filigran"
author = "OpenAEV Project"
release = "1.10.1"

master_doc = "index"
pygments_style = "sphinx"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.inheritance_diagram",
    "autoapi.extension",
    "sphinx_autodoc_typehints",
]

autoapi_dirs = ["../pyoaev"]
autoapi_options = [
    "members",
    "undoc-members",
    "private-members",
    "show-inheritance",
]

autodoc_inherit_docstrings = False

# Inherited docstrings from stdlib base classes are noisy — suppress them
_INHERITED_DOCSTRING_MARKERS = [
    "Create a collection of name/value pairs.",  # enum.Enum
    "str(object='') -> str",  # str
]


def _suppress_inherited_docstring(app, what, name, obj, options, lines):
    """Remove inherited stdlib docstrings from generated API docs."""
    if what == "class" and lines:
        joined = "\n".join(lines)
        if any(marker in joined for marker in _INHERITED_DOCSTRING_MARKERS):
            lines.clear()


def setup(app):
    app.connect("autodoc-process-docstring", _suppress_inherited_docstring)


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
