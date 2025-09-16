# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import re
from pathlib import Path

project = "nanodjango"
copyright = "2024, Richard Terry"
author = "Richard Terry"


def find_version(*paths):
    path = Path(*paths)
    content = path.read_text()
    match = re.search(r"^__version__\s*=\s*['\"]([^'\"]*)['\"]", content, re.M)
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find version string.")


# The full version, including alpha/beta/rc tags
release = find_version("..", "nanodjango", "__init__.py")


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "furo_nanodjango",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo_nanodjango"
html_static_path = ["_static"]
html_title = ""
html_theme_options = {
    "light_css_variables": {
        "font-stack": "Barlow, sans-serif;",
        "font-stack--monospace": "Fira Mono, monospace",
        "font-stack--headings": "Barlow, sans-serif;",
    },
}
