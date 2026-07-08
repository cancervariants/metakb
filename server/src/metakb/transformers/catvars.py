"""Construct Categorical Variants from constituent parts for evidence aggregation.

Provide constructor functions and also define rules/methods for minting IDs.
"""

import logging

from cool_seq_tool.handlers import SeqRepoAccess
from cool_seq_tool.sources import TranscriptMappings
from ga4gh.cat_vrs.models import (
    CategoricalVariant,
    Constraint,
    CopyChangeConstraint,
    DefiningAlleleConstraint,
    DefiningLocationConstraint,
    FeatureContextConstraint,
)
from ga4gh.cat_vrs.recipes import CategoricalCnv, ProteinSequenceConsequence
from ga4gh.cat_vrs.relations import LIFTOVER_TO_RELATION, TRANSLATION_OF_RELATION
from ga4gh.core.models import Coding, MappableConcept, code
from ga4gh.vrs.models import Allele, CopyNumberChange

_logger = logging.getLogger(__name__)


def build_copynumberchange_catvar(variant: CopyNumberChange) -> CategoricalCnv:
    """Build a CopyNumberChange catvar

    :param variant: VRS copynumberchange variant
    :return: CategoricalCNV using the input variant, with MetaKB name and ID
    """
    cv_id = f"metakb.cv:CNC.{variant.copyChange}_{variant.id.split(':')[1]}"
    cv_name = "tmp name"
    return CategoricalCnv(
        id=cv_id,
        name=cv_name,
        constraints=[
            Constraint(root=CopyChangeConstraint(copyChange=variant.copyChange)),
            Constraint(
                root=DefiningLocationConstraint(
                    location=variant.location,
                    matchCharacteristic=MappableConcept(
                        primaryCoding=Coding(
                            code=code("is_within"),
                            system="ga4gh-gks-term:location-match",
                        )
                    ),
                    relations=[LIFTOVER_TO_RELATION],
                )
            ),
        ],
    )


def _extract_ref_alt(allele: Allele) -> tuple[str, str]:
    """Extract (ref, alt) sequences from a VRS Allele, inferring empty ref for insertions."""
    location_seq = allele.location.sequence

    if not hasattr(allele.state, "sequence"):
        msg = "Protein consequence normalization supports sequence-based states only"
        raise NotImplementedError(msg)

    alt = getattr(allele.state.sequence, "root", allele.state.sequence)

    if location_seq is None:
        if allele.location.start == allele.location.end:
            # Only treat as insertion if alt is non-empty
            if alt:
                ref = ""
            else:
                msg = "Cannot infer reference sequence for empty alt and missing location.sequence"
                raise NotImplementedError(msg)
        else:
            msg = "Protein consequence normalization requires location.sequence"
            raise NotImplementedError(msg)
    else:
        ref = getattr(location_seq, "root", location_seq)

    return ref, alt


def _resolve_protein_and_gene(
    seqrepo_access: SeqRepoAccess,
    transcript_mappings: TranscriptMappings,
    allele: Allele,
) -> tuple[str, str]:
    """Return (protein_accession, gene_symbol) for the allele's sequence."""

    def _strip(alias: str) -> str:
        return alias.split(":", 1)[1] if ":" in alias else alias

    refget = getattr(
        allele.location.sequenceReference.refgetAccession,
        "root",
        allele.location.sequenceReference.refgetAccession,
    )

    alias_candidates: set[str] = set()
    for query in (f"ga4gh:{refget}", refget):
        aliases, _ = seqrepo_access.translate_alias(query)
        identifiers, _ = seqrepo_access.translate_identifier(query)
        alias_candidates.update(aliases)
        alias_candidates.update(identifiers)

    def _is_protein(alias: str) -> bool:
        if seqrepo_access.extract_sequence_type(alias) == "p":
            return True
        return _strip(alias).startswith(("NP_", "XP_", "ENSP"))

    protein_aliases = [a for a in alias_candidates if _is_protein(a)]
    if not protein_aliases:
        msg = f"Allele {allele.id} is not on a protein sequence"
        raise ValueError(msg)

    for alias in protein_aliases:
        acc = _strip(alias)
        gene = transcript_mappings.get_gene_symbol_from_refseq_protein(
            acc
        ) or transcript_mappings.get_gene_symbol_from_ensembl_protein(acc)
        if gene:
            return acc, gene

    msg = f"Unable to determine gene for allele {allele.id}"
    raise ValueError(msg)


def _split_ref_alt(ref: str, alt: str) -> tuple[int, str, str]:
    """Split ref/alt into shared prefix and differing middle segments.

    Returns (prefix_len, ref_mid, alt_mid), where ref_mid/alt_mid are the
    non-matching portions after removing the longest common prefix and suffix.
    """
    # longest common prefix
    i = 0
    while i < min(len(ref), len(alt)) and ref[i] == alt[i]:
        i += 1

    # longest common suffix
    j = 0
    while j < (len(ref) - i) and j < (len(alt) - i) and ref[-(j + 1)] == alt[-(j + 1)]:
        j += 1

    ref_mid = ref[i : len(ref) - j if j else len(ref)]
    alt_mid = alt[i : len(alt) - j if j else len(alt)]

    return i, ref_mid, alt_mid


def _format_protein_change(
    seqrepo_access: SeqRepoAccess,
    gene: str,
    accession: str,
    ref: str,
    alt: str,
    start_pos: int,  # 1-based
    end_pos: int,  # 1-based inclusive
) -> str:
    """Format a protein consequence string from ref/alt sequences and coordinates.

    Supported variant types:
    - Substitution:      V600E
    - Deletion:          D579del, W557_K558del
    - Insertion:         A763_Y764insFQEA
    - Delins:            L747_A750delinsP

    Coordinates:
    - ``start_pos`` and ``end_pos`` are 1-based, inclusive residue coordinates
      corresponding to the replaced region (derived from VRS inter-residue coords).
    - SeqRepo access uses 0-based, half-open coordinates and is only used to fetch
      flanking residues for insertions.

    Insertions:
    - Insertions are detected by aligning ``ref`` and ``alt`` using longest common
      prefix/suffix matching (see ``_split_ref_alt``).
    - This allows correct placement of insertions that occur:
        * after the entire ref (e.g., "H" → "HH")
        * at a zero-length location (ref == "")
        * within the ref span (e.g., "EA" → "EAFQEA")
    - The insertion position is computed as ``start_pos + i``, where ``i`` is the
      length of the shared prefix.
    - Flanking residues are fetched from SeqRepo to produce HGVS-style
      "X{pos}_Y{pos+1}ins..." notation.

    Does not currently handle frameshifts, stop codons, or duplications (dup).

    :param seqrepo_access: Sequence accessor used to retrieve flanking residues
    :param gene: Gene symbol (e.g., "EGFR")
    :param accession: Protein accession (e.g., "NP_005219.2")
    :param ref: Reference amino acid sequence being replaced
    :param alt: Alternate amino acid sequence
    :param start_pos: 1-based start position of the ref sequence
    :param end_pos: 1-based end position of the ref sequence
    :return: HGVS-like protein consequence string
    """
    ref_len = len(ref)
    alt_len = len(alt)

    # --- substitution ---
    if ref_len == alt_len:
        if ref_len == 1:
            return f"{gene} {ref}{start_pos}{alt}"
        return f"{gene} {ref[0]}{start_pos}_{ref[-1]}{end_pos}delins{alt}"

    # --- insertion ---
    if alt_len > ref_len:
        i, ref_mid, alt_mid = _split_ref_alt(ref, alt)

        # true insertion iff no bases removed from ref
        if ref_mid != "":
            # fallback to delins
            if ref_len == 1:
                return f"{gene} {ref}{start_pos}delins{alt}"
            return f"{gene} {ref[0]}{start_pos}_{ref[-1]}{end_pos}delins{alt}"

        inserted = alt_mid
        insert_pos = start_pos + i  # 1-based position *after* which insertion occurs

        # flanking residues (convert to 0-based for seqrepo)
        left = seqrepo_access.get_sequence(accession, insert_pos - 2, insert_pos - 1)
        right = seqrepo_access.get_sequence(accession, insert_pos - 1, insert_pos)

        return f"{gene} {left}{insert_pos - 1}_{right}{insert_pos}ins{inserted}"

    # --- deletion ---
    if alt_len == 0:
        if ref_len == 1:
            return f"{gene} {ref}{start_pos}del"
        return f"{gene} {ref[0]}{start_pos}_{ref[-1]}{end_pos}del"

    # --- delins ---
    if alt_len < ref_len:
        if ref_len == 1:
            return f"{gene} {ref}{start_pos}delins{alt}"
        return f"{gene} {ref[0]}{start_pos}_{ref[-1]}{end_pos}delins{alt}"

    msg = "Unhandled variant type"
    raise ValueError(msg)


def get_normalized_protein_consequence_name(
    seqrepo_access: SeqRepoAccess,
    transcript_mappings: TranscriptMappings,
    allele: Allele,
) -> str:
    """Return a normalized, HGVS-like protein consequence name for a VRS Allele a la "<GENE> <description>"

    :param seqrepo_access: Sequence accessor for retrieving protein residues
    :param transcript_mappings: Mapping utility for protein → gene symbol
    :param allele: VRS Allele object
    :return: Normalized protein consequence string
    :raises ValueError: If the allele is not protein-based or gene cannot be resolved
    :raises NotImplementedError: For unsupported allele structures
    """
    ref, alt = _extract_ref_alt(allele)
    protein_accession, gene_name = _resolve_protein_and_gene(
        seqrepo_access, transcript_mappings, allele
    )

    start0, end0 = allele.location.start, allele.location.end
    start_pos = start0 + 1
    end_pos = end0

    return _format_protein_change(
        seqrepo_access,
        gene_name,
        protein_accession,
        ref,
        alt,
        start_pos,
        end_pos,
    )


def build_proteinsequenceconsequence_catvar(
    seqrepo_access: SeqRepoAccess,
    transcript_mappings: TranscriptMappings,
    allele: Allele,
) -> ProteinSequenceConsequence:
    """Construct a ProteinSequenceConsequence categorical variant.

    :param seqrepo_access: cool-seq-tool seqrepo handler
    :param transcript_mappings: cool-seq-tool mappings from protein accessions to genes
    :param allele: VRS allele
    :return: ProteinSequenceConsequence-based catvar with MetaKB name and ID
    """
    cv_id = f"metakb.cv:PSQ.{allele.id.split(':')[1]}"
    try:
        cv_name = get_normalized_protein_consequence_name(
            seqrepo_access, transcript_mappings, allele
        )
    except NotImplementedError:
        _logger.debug(
            "Unable to generate name for protein sequence consequence allele: %s",
            allele,
        )
        cv_name = allele.id  # acceptable default for now
    return ProteinSequenceConsequence(
        id=cv_id,
        name=cv_name,
        constraints=[
            Constraint(
                root=DefiningAlleleConstraint(
                    allele=allele,
                    relations=[
                        LIFTOVER_TO_RELATION,
                        TRANSLATION_OF_RELATION,
                    ],
                )
            )
        ],
    )


def build_featurecontext_catvar(feature: MappableConcept) -> CategoricalVariant:
    """Build a simple FeatureContextConstraint-based catvar

    :param feature: feature to use as basis of constraint
    :return: CatVar with a FeatureContextConstraint, and a MetaKB name and ID
    """
    if feature.conceptType != "Gene":
        raise ValueError
    feature_id = feature.id.removeprefix("normalize.gene.").replace(":", "_")
    cv_id = f"metakb.cv:FC.{feature_id}"
    cv_name = f"{feature.name} Mutation"
    return CategoricalVariant(
        id=cv_id,
        name=cv_name,
        constraints=[Constraint(root=FeatureContextConstraint(featureContext=feature))],
    )
