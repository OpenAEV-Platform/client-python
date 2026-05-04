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

autoapi_dirs = ["../pyoaev"]  # adjust this path to where your source package is
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
