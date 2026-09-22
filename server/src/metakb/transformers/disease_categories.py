"""Provide categorization for disease terms

Mostly useful for the UI. Temporarily homed here, but might get moved to the normalizer.
"""

import logging

import fastobo
from disease.schemas import (
    NAMESPACE_TO_SYSTEM_URI as DISEASE_NAMESPACE_TO_SYSTEM_URI,
)
from disease.schemas import (
    NamespacePrefix as DiseaseNamespacePrefix,
)
from ga4gh.core.models import Coding, ConceptMapping, Relation, code
from wags_tails.mondo import MondoData

_logger = logging.getLogger(__name__)


class CategorizationError(Exception):
    """Encompass category generation errors"""


class MissingMondoTermError(CategorizationError):
    """Raise for inability to recover referenced MONDO term

    Possibly indicates mismatch in MONDO versions/systems
    """


def _get_frame_for_term(
    mondo: fastobo.doc.OboDoc, term_id: str
) -> fastobo.term.TermFrame:
    try:
        term_frame = next(t for t in mondo if str(t.id) == term_id.upper())
    except StopIteration as e:
        msg = f"Unable to retrieve {term_id} from local MONDO ontology"
        raise MissingMondoTermError(msg) from e
    return term_frame


def _get_parents_from_frame(frame: fastobo.term.TermFrame) -> set[str]:
    """Get term parents from a fastobo `frame`

    Exclude overly-broad or non-MONDO terms
    """
    parent_term_ids = set()
    for clause in frame:
        if clause.raw_tag() == "is_a":
            if clause.term.prefix != "MONDO" or clause.raw_value() == "MONDO:0005070":
                continue
            parent_term_ids.add(clause.raw_value())
    return parent_term_ids


def _get_oncotree_xref_from_frame(term_frame: fastobo.term.TermFrame) -> str | None:
    for clause in term_frame:
        if (
            isinstance(clause, fastobo.term.XrefClause)
            and clause.xref.id.prefix == "ONCOTREE"
            and clause.xref.id.local not in {"MT", "OTHER"}
        ):
            return str(clause.xref.id)
    return None


def _get_parent_oncotree_xrefs(
    mondo: fastobo.doc.OboDoc,
    term_frame: fastobo.term.TermFrame,
) -> list[tuple[str, str]]:
    if oncotree_xref := _get_oncotree_xref_from_frame(term_frame):
        return [(oncotree_xref, str(term_frame.id))]

    xrefs = []
    for parent_id in _get_parents_from_frame(term_frame):
        parent_term_frame = _get_frame_for_term(mondo, parent_id)
        xrefs += _get_parent_oncotree_xrefs(mondo, parent_term_frame)

    return xrefs


def _get_best_oncotree_mapping(
    mondo: fastobo.doc.OboDoc, term_frame: fastobo.term.TermFrame
) -> str | None:
    """Recursive function for fetching parental oncotree mappings + filtering to the best one"""
    parent_xref_mappings = list(set(_get_parent_oncotree_xrefs(mondo, term_frame)))

    if len(parent_xref_mappings) > 1:
        # could perform conflict resolution in the future
        _logger.info(
            "Unable to resolve parentage for %s: %s",
            str(term_frame.id),
            [f"{i[0]} (via {i[1]})" for i in parent_xref_mappings],
        )
        return None
    if len(parent_xref_mappings) == 0:
        _logger.info("No available oncotree terms for %s", str(term_frame.id))
        return None
    return parent_xref_mappings[0][0]


ONCOTREE_SYSTEM = DISEASE_NAMESPACE_TO_SYSTEM_URI[DiseaseNamespacePrefix.ONCOTREE]


def get_category_for_mondo_term(
    mondo: fastobo.doc.OboDoc,
    mondo_term_id: str,
) -> ConceptMapping | None:
    """Get Oncotree categorization for a mondo term

    Walks up mondo parentage tree until an Oncotree term is found. Doesn't try to resolve
    conflicts.

    :param mondo: fastobo mondo handle
    :param term_id: mondo term ID
    :return: concept mapping using skos:broadMatch if a categorization can be made
    """
    term_frame = _get_frame_for_term(mondo, mondo_term_id)
    try:
        mapping_result = _get_best_oncotree_mapping(mondo, term_frame)
    except MissingMondoTermError:
        _logger.exception(
            "Encountered missing MONDO term while looking up categorization of %s",
            mondo_term_id,
        )
        return None
    if not mapping_result:
        return None
    return ConceptMapping(
        relation=Relation.BROAD_MATCH,
        coding=Coding(
            id=mapping_result,
            system=ONCOTREE_SYSTEM,
            code=code(mapping_result.split(":", 1)[-1]),
        ),
    )


def get_mondo_handler() -> fastobo.doc.OboDoc:
    """Get MONDO OBO handler

    Pretty limited configurability because this probably should eventually move somewhere else.
    """
    getter = MondoData()
    file, _ = getter.get_latest()
    return fastobo.load(file)
