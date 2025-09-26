"""Provide access to static Neo4j queries.

All queries should be provided as functions wrapped by a cache decorator so that repeat
fetches don't reload the file.
"""

from functools import cache
from importlib.resources import files
from pathlib import Path

_query_dir = Path(str(files("metakb.repository.queries")))


def _load(filename: str) -> str:
    """Load a query file

    :param filename: path to query file (probably relative location)
    :return: file contents
    :raise FileNotFoundError: if filename can't be found in queries directory
    """
    path = _query_dir / filename
    if not path.exists():
        raise FileNotFoundError(path)
    return (path).read_text(encoding="utf-8")


def _load_multiple_queries(filename: str) -> list[str]:
    """Load a file containing multiple queries, separated by semicolons.

    For some actions, like adding a bunch of constraints, it's convenient to keep them
    all in one file, but Neo4j will get mad if you try to get it to execute multiple
    queries at once; this splits them up.

    :param filename: path to file
    :return: list of queries contained within, with comments removed
    """
    raw_text = _load(filename)
    return " ".join(
        filter(None, [line.split("//")[0] for line in raw_text.split("\n")])
    ).split(";")[:-1]


@cache
def initialize() -> list[str]:
    return _load_multiple_queries("initialize.cypher")


@cache
def teardown() -> list[str]:
    return _load_multiple_queries("teardown.cypher")


@cache
def load_dac_catvar() -> str:
    return _load("load_definingalleleconstraint_catvar.cypher")


@cache
def load_document() -> str:
    return _load("load_document.cypher")


@cache
def load_gene() -> str:
    return _load("load_gene.cypher")


@cache
def load_disease() -> str:
    return _load("load_disease.cypher")


@cache
def load_drug() -> str:
    return _load("load_drug.cypher")


@cache
def load_therapy_group() -> str:
    return _load("load_therapy_group.cypher")


@cache
def load_method() -> str:
    return _load("load_method.cypher")


@cache
def load_statement() -> str:
    return _load("load_statement.cypher")


@cache
def search_statements() -> str:
    return _load("search_statements.cypher")


@cache
def get_statements() -> str:
    return _load("get_statements.cypher")
