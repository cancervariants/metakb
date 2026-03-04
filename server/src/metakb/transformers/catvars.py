"""Construct Categorical Variants from constituent parts for evidence aggregation.

Provide constructor functions and also define rules/methods for minting IDs.
"""

from cool_seq_tool.handlers import SeqRepoAccess
from cool_seq_tool.sources import TranscriptMappings
from ga4gh.cat_vrs.models import (
    CategoricalVariant,
    Constraint,
    CopyChangeConstraint,
    DefiningAlleleConstraint,
    DefiningLocationConstraint,
    FeatureContextConstraint,
    Relation,
)
from ga4gh.cat_vrs.recipes import CategoricalCnv, ProteinSequenceConsequence, SystemUri
from ga4gh.core.models import Coding, MappableConcept, code
from ga4gh.vrs.models import Allele, CopyNumberChange

LIFTOVER_TO_RELATION = MappableConcept(
    primaryCoding=Coding(
        system=SystemUri.GKS_ALLELE_RELATION, code=code(Relation.LIFTOVER_TO)
    )
)
TRANSLATION_OF_RELATION = MappableConcept(
    primaryCoding=Coding(
        system=SystemUri.SEQUENCE_ONTOLOGY,
        code=code(Relation.TRANSLATION_OF),
    ),
)


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


def get_normalized_protein_consequence_name(
    seqrepo_access: SeqRepoAccess,
    transcript_mappings: TranscriptMappings,
    allele: Allele,
) -> str:
    """Return normalized protein consequence name for a VRS Allele.

    The output format is ``"<gene name> <REF><POS><ALT>"``.

    :param seqrepo_access: cool-seq-tool seqrepo handler
    :param transcript_mappings: cool-seq-tool mappings from protein accessions to genes
    :param allele: VRS Allele
    :raises ValueError: If allele does not appear to be on a protein sequence, or
        if a gene association cannot be determined
    :raises NotImplementedError: If normalization for this allele is unsupported.
        For now, this includes alleles lacking ``location.sequence`` and edit types
        where ``len(location.sequence) != len(state.sequence)``.
    :return: Normalized protein consequence string
    """
    location_seq = allele.location.sequence
    if location_seq is None:
        msg = (
            "Protein consequence normalization requires location.sequence to be "
            "present on the input allele."
        )
        raise NotImplementedError(msg)

    ref = getattr(location_seq, "root", location_seq)
    if not hasattr(allele.state, "sequence"):
        msg = (
            "Protein consequence normalization currently supports sequence-based "
            "Allele states only."
        )
        raise NotImplementedError(msg)
    alt = getattr(allele.state.sequence, "root", allele.state.sequence)
    if len(ref) != len(alt):
        msg = (
            "Protein consequence normalization currently supports SNP-like edits "
            "only (equal ref/alt lengths)."
        )
        raise NotImplementedError(msg)

    refget_accession = getattr(
        allele.location.sequenceReference.refgetAccession,
        "root",
        allele.location.sequenceReference.refgetAccession,
    )
    alias_candidates: set[str] = set()
    for query in (f"ga4gh:{refget_accession}", refget_accession):
        aliases, _ = seqrepo_access.translate_alias(query)
        alias_candidates.update(aliases)
        identifiers, _ = seqrepo_access.translate_identifier(query)
        alias_candidates.update(identifiers)

    def _is_protein_alias(alias: str) -> bool:
        if seqrepo_access.extract_sequence_type(alias) == "p":
            return True
        accession = alias.split(":", 1)[1] if ":" in alias else alias
        return accession.startswith(("NP_", "XP_", "ENSP"))

    protein_aliases = [alias for alias in alias_candidates if _is_protein_alias(alias)]
    if not protein_aliases:
        msg = (
            f"Allele {allele.id} sequence reference {refget_accession} is not a "
            "protein sequence."
        )
        raise ValueError(msg)

    gene_name = None
    for protein_alias in protein_aliases:
        accession = (
            protein_alias.split(":", 1)[1] if ":" in protein_alias else protein_alias
        )
        gene_symbol = transcript_mappings.get_gene_symbol_from_refeq_protein(
            accession
        ) or transcript_mappings.get_gene_symbol_from_ensembl_protein(accession)
        if gene_symbol:
            gene_name = gene_symbol
            break

    if not gene_name:
        msg = f"Unable to determine gene association for allele {allele.id}"
        raise ValueError(msg)

    # VRS SequenceLocation uses inter-residue coordinates, so convert to residue.
    pos = allele.location.start + 1
    return f"{gene_name} {ref}{pos}{alt}"


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
    cv_name = get_normalized_protein_consequence_name(
        seqrepo_access, transcript_mappings, allele
    )
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
