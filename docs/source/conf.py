# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "MetaKB"
copyright = "2018-2024, Variant Interpretation for Cancer Consortium"
author = "Variant Interpretation for Cancer Consortium"
html_title = "MetaKB"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx.ext.linkcode",
    "sphinx_copybutton",
    "sphinx.ext.autosummary",
    "sphinx_github_changelog",
]

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = []
html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/solid.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/brands.min.css",
]
html_theme_options = {
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/{{ cookiecutter.org }}/{{ cookiecutter.repo }}",
            "html": "",
            "class": "fa-brands fa-solid fa-github",
        },
        {
            "name": "Variant Interpretation for Cancer Consortium",
            "url": "https://cancervariants.org/",
            "html": "",
            "class": "fa-solid fa-house",
        }
    ],
}
# -- autodoc things ----------------------------------------------------------
import os
import sys

sys.path.insert(0, os.path.abspath("../../"))
autodoc_preserve_defaults = True

# -- get version -------------------------------------------------------------
from importlib.metadata import version

release = version = version("metakb")

# -- linkcode ----------------------------------------------------------------
def linkcode_resolve(domain, info):
    if domain != "py":
        return None
    if not info["module"]:
        return None
    filename = info["module"].replace(".", "/")
    return f"https://github.com/cancervariants/metakb/blob/main/src/{filename}.py"


# -- code block style --------------------------------------------------------
pygments_style = "default"
pygements_dark_style = "monokai"
