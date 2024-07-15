# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "metakb"
copyright = "2018-2024, Variant Interpretation for Cancer Consortium"
author = "Alex H Wagner, Brian Walsh, Jeff Liu, Kori Kuzma, James S Stevenson"
html_title = "metakb"

# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx.ext.linkcode",
    "sphinx_copybutton",
    "sphinx.ext.autosummary",
    "sphinx_github_changelog",
    "sphinx_click",
    "sphinxcontrib.images"
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
            "url": "https://github.com/cancervariants/metakb",
            "html": "",
            "class": "fa-brands fa-solid fa-github",
        },
        {
            "name": "Variant Interpretation for Cancer Consortium",
            "url": "https://cancervariants.org",
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
from metakb import __version__

release = version = __version__

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

# -- sphinx-click ------------------------------------------------------------
# These functions let us write descriptions/docstrings in a way that doesn't look
# weird in the Click CLI, but get additional formatting in the sphinx-click autodocs for
# better readability.
from typing import List
import re

from click.core import Context
from sphinx.application import Sphinx
from sphinx_click.ext import _get_usage, _format_usage, _indent

CMD_PATTERN = r"--[^ ]+"
STR_PATTERN = r"\"[^ ]+\""
SNAKE_PATTERN = r"[A-Z]+_[A-Z_]*[A-Z][., ]"


def _add_formatting_to_string(line: str) -> str:
    """Add fixed-width code formatting to span sections in lines:

    * shell options, eg `--update_all`
    * double-quoted strings, eg `"HGNC"`
    * all caps SNAKE_CASE env vars, eg `GENE_NORM_REMOTE_DB_URL`
    """
    for pattern in (CMD_PATTERN, STR_PATTERN, SNAKE_PATTERN):
        line = re.sub(pattern, lambda x: f"``{x.group()}``", line)
    return line


def process_description(app: Sphinx, ctx: Context, lines: List[str]):
    """Add custom formatting to sphinx-click autodoc descriptions.

    * remove :param: :return: etc
    * add fixed-width (code) font to certain words
    * add code block formatting to example shell commands
    * move primary usage example to the top of the description

    Because we have to modify the lines list in place, we have to make multiple passes
    through it to format everything correctly.
    """
    if not lines:
        return

    # chop off params
    param_boundary = None
    for i, line in enumerate(lines):
        if ":param" in line:
            param_boundary = i
            break
    if param_boundary is not None:
        del lines[param_boundary:]
        lines[-1] = ""

    # add code formatting to strings, commands, and env vars
    lines_to_fmt = []
    for i, line in enumerate(lines):
        if line.startswith(("   ", ">>> ", "|")):
            continue  # skip example code blocks
        if any(
            [
                re.findall(CMD_PATTERN, line),
                re.findall(STR_PATTERN, line),
                re.findall(SNAKE_PATTERN, line),
            ]
        ):
            lines_to_fmt.append(i)
    for line_num in lines_to_fmt:
        lines[line_num] = _add_formatting_to_string(lines[line_num])

    # add code block formatting to example console commands
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith(("    ", "|     ")):
            if lines[i].startswith("|     "):
                lines[i] = lines[i][3:]
            if (i == 0 or lines[i - 1] == "\b" or lines[i - 1] == ""):
                lines.insert(i, "")
                lines.insert(i, ".. code-block:: console")

    # put usage at the top of the description
    lines.insert(0, "")
    for usage_line in _get_usage(ctx).splitlines()[::-1]:
        lines.insert(0, _indent(usage_line))
    lines.insert(0, "")
    lines.insert(0, ".. code-block:: shell")


def process_option(app: Sphinx, ctx: Context, lines: List[str]):
    """Add fixed-width formatting to strings in sphinx-click autodoc options."""
    for i, line in enumerate(lines):
        if re.findall(STR_PATTERN, line):
            lines[i] = re.sub(STR_PATTERN, lambda x: f"``{x.group()}``", line)


def setup(app):
    """Used to hook format customization into sphinx-click build.

    In particular, since we move usage to the top of the command description, we need
    an extra hook here to silence the built-in usage section.
    """
    app.connect("sphinx-click-process-description", process_description)
    app.connect("sphinx-click-process-options", process_option)
    app.connect("sphinx-click-process-usage", lambda app, ctx, lines: lines.clear())

######## OLD

# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']
