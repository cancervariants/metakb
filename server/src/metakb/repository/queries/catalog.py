"""Provide class for accessing static Neo4j queries."""

from functools import cached_property
from importlib.resources import files
from pathlib import Path


class CypherCatalog:
    """Container class for raw query strings.

    Lazily load from an adjacent directory.

    TODO -- make this a singleton
    """

    def __init__(self) -> None:
        """Initialize query holder."""
        self._query_dir = Path(str(files("metakb.repository.queries")))

    def _load(self, filename: str) -> str:
        path = self._query_dir / filename
        if not path.exists():
            raise FileNotFoundError(path)
        return (path).read_text(encoding="utf-8")

    def _load_multiple_queries(self, filename: str) -> list[str]:
        """Load a file containing multiple queries, separated by semicolons."""
        raw_text = self._load(filename)
        return " ".join(
            filter(None, [line.split("//")[0] for line in raw_text.split("\n")])
        ).split(";")[:-1]

    @cached_property
    def initialize(self) -> list[str]:
        return self._load_multiple_queries("initialize.cypher")

    @cached_property
    def teardown(self) -> list[str]:
        return self._load_multiple_queries("teardown.cypher")

    @cached_property
    def load_dac_catvar(self) -> str:
        return self._load("load_definingalleleconstraint_catvar.cypher")

    @cached_property
    def load_document(self) -> str:
        return self._load("load_document.cypher")

    @cached_property
    def load_gene(self) -> str:
        return self._load("load_gene.cypher")

    @cached_property
    def load_disease(self) -> str:
        return self._load("load_disease.cypher")

    @cached_property
    def load_drug(self) -> str:
        return self._load("load_drug.cypher")

    @cached_property
    def load_therapy_group(self) -> str:
        return self._load("load_therapy_group.cypher")

    @cached_property
    def load_method(self) -> str:
        return self._load("load_method.cypher")

    @cached_property
    def load_statement(self) -> str:
        return self._load("load_statement.cypher")

    @cached_property
    def search_statements(self) -> str:
        return self._load("search_statements.cypher")

    @cached_property
    def get_statements(self) -> str:
        return self._load("get_statements.cypher")
