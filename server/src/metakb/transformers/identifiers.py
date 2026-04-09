"""Utilities related to ID minting for newly-constructed objects"""

import json
from uuid import uuid4

from ga4gh.core import sha512t24u
from ga4gh.va_spec.base import (
    ConditionSet,
    MembershipOperator,
    TherapyGroup,
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)


def _hash_array(str_array: list[str]) -> str:
    """Generate deterministic hash of a list of strings

    :param str_array: array of string values (e.g. IDs, predicate terms, etc)
    :return: hash
    :raise ValueError: if input array contains empty or null values
    """
    if not all(str_array):
        # all values need to be non-null/non-empty
        raise ValueError
    str_array.sort()
    blob = json.dumps(str_array, separators=(",", ":"), sort_keys=True).encode("ascii")
    return sha512t24u(blob)


def compute_assertion_id(
    proposition: VariantTherapeuticResponseProposition
    | VariantDiagnosticProposition
    | VariantPrognosticProposition,
) -> str:
    """Create ID for MetaKB assertion from proposition

    ID hash parts:

    * proposition entities (variant, gene, therapy(*), disease)
    * proposition predicate

    :param proposition: proposed proposition object
    :return: assertion ID
    """
    member_ids: list[str] = [
        str(proposition.predicate),
        proposition.subjectVariant.id,
        proposition.geneContextQualifier.id,
    ]
    if isinstance(proposition, VariantTherapeuticResponseProposition):
        member_ids += [
            proposition.conditionQualifier.root.id,
            proposition.objectTherapeutic.root.id,
        ]
    else:
        member_ids += [proposition.objectCondition.root.id]

    digest = _hash_array(member_ids)

    return f"metakb.assertion:{digest}"


def compute_combo_id(
    source_prefix: str,
    combo_class: type[TherapyGroup] | type[ConditionSet],
    operator: MembershipOperator,
    ids: list[str],
) -> str:
    """Compute identifier for concept set (eg therapy group or condition set)

    >>> compute_combo_id(
    ...     SourceName.MOA.value,
    ...     TherapyGroup,
    ...     MembershipOperator.AND,
    ...     ["moa.therapy:imatinib", "moa.therapy:trastuzumab"],
    ... )
    'moa.tg:ojf-glrsMg7fNrGKoGwGEF0OTyssCuCA'

    These values should generally be for internal use only, so it's not super
    important that they are especially meaningful, but they should be consistent

    :param source_prefix: prefix to use in ID namespace
    :param combo_class: type of entity combination
    :param operator: operator enum instance from concept set
    :param ids: list of entity IDs to combine, must all be non-empty/non-null
    :return: CURIE designating the combination in a deterministic way
    :raise ValueError: if unrecognized combo_class type or if IDs list contains
        null or empty values
    """
    if not all(ids):
        raise ValueError
    # use the whole membership operator enum string (ie "MembershipOperator.OR")
    # to distinguish from an improbable clash w/ a real entity name
    ids.append(str(operator))
    ids.sort()
    blob = json.dumps(ids, separators=(",", ":"), sort_keys=True).encode("ascii")
    digest = sha512t24u(blob)

    if combo_class is TherapyGroup:
        combo_class_abbrev = "tg"
    elif combo_class is ConditionSet:
        combo_class_abbrev = "cs"
    else:
        raise ValueError
    return f"{source_prefix.lower()}.{combo_class_abbrev}:{digest}"


def generate_metakb_evidenceline_id() -> str:
    """Create a UUID for an evidence line object

    It's sort of silly to have a one-line function like this, but it lets us
    explicitly declare an identifier policy.

    These are supposed to behave like UUIDs rather than hashes, because they might move
    around. We could potentially calculate them based off something like proposition +
    strength + outcome, but we don't add propositions to evidence lines right now. They
    should probably get removed before an end user sees them, but they can be helpful
    for internal CRUD operations

    :return: identifier with a UUID
    """
    return f"metakb.evline:{uuid4()}"
