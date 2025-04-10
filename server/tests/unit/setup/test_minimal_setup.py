"""Tests basic project setup."""

import sys


def test_python_version():
    """Should use python 3.7.1."""
    assert sys.version_info.major == 3, "Must use Python 3"
    assert sys.version_info.minor >= 7, "Must use at least Python 3.7"


def test_import_main_package():
    """Should have a package module."""
    import metakb  # noqa: F401


def test_import_pytest():
    """Should have a pytest module."""
    import pytest  # noqa: F401
