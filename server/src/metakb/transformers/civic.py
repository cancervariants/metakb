"""A module for to transform CIViC."""

import logging
import re

from civicpy import civic as civicpy
from civicpy.exports.civic_gks_record import (
    CivicGksEvidence,
    CivicGksRecordError,
    create_gks_record_from_assertion,
)
from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.va_spec.base import Statement
from ga4gh.vrs.models import Allele, CopyNumberChange
from pydantic.dataclasses import dataclass
from tqdm import tqdm

from metakb.transformers.base import TransformedData, Transformer
from metakb.transformers.catvars import (
    build_copynumberchange_catvar,
    build_proteinsequenceconsequence_catvar,
)

_logger = logging.getLogger(__name__)

MP_NAME_PATTERN = (
    r"(?P<gene>\w+)(?:\s+(?P<p_change>\w+))?(?:\s+(?P<c_change>\(?c\..*\)?))?"
)

# Variant names that are known to not be supported in the variation-normalizer
UNABLE_TO_NORMALIZE_VAR_NAMES = {
    "mutation",
    "exon",
    "overexpression",
    "frameshift",
    "promoter",
    "deletion",
    "type",
    "insertion",
    "expression",
    "duplication",
    "copy",
    "underexpression",
    "number",
    "variation",
    "repeat",
    "rearrangement",
    "activation",
    "mislocalization",
    "translocation",
    "wild",
    "polymorphism",
    "frame",
    "shift",
    "loss",
    "function",
    "levels",
    "inactivation",
    "snp",
    "fusion",
    "dup",
    "truncation",
    "homozygosity",
    "gain",
    "phosphorylation",
}


@dataclass
class MolecularProfileNameComponents:
    """Define components for molecular profile name"""

    gene: str
    p_change: str | None
    c_change: str | None


class CivicTransformer(Transformer):
    """A class for transforming CIViC to the common data model."""

    async def transform(self) -> None:
        """Transform CIViC evidence and assertions to common data model.

        Store result in ``transformed_data`` instance variable.

        For each statement:
        * Build its base GKS equivalent
        * Try to normalize variant, disease, gene(, drug)
        * If they all normalize, also build the aggregate statement, supported by
          an evidence line to the base statement
        """
        accepted_evidence_items = civicpy.get_all_evidence(include_status=["accepted"])
        accepted_assertions = civicpy.get_all_assertions(include_status=["accepted"])
        pbar = tqdm(
            total=len(accepted_evidence_items) + len(accepted_assertions),
        )
        statements = []
        for item in accepted_evidence_items:
            transformed_statement = self._evitem_to_vaspec(item)
            if not transformed_statement:
                _logger.warning(
                    "Unable to model civic evidence item %s as a GKS statement",
                    item,
                )
                continue
            statements.append(transformed_statement)
            if aggregate_statement := await self._create_aggregate_statement(
                transformed_statement
            ):
                # include this statement as an item within an existing evidence line
                # if there is already an aggregate statement for this set of entities
                for existing_statement in statements:
                    if (
                        existing_statement.proposition
                        == aggregate_statement.proposition
                    ):
                        existing_statement.hasEvidenceLines[0].hasEvidenceItems.append(
                            transformed_statement
                        )
                        break
                else:
                    statements.append(aggregate_statement)
            pbar.update(1)
        for item in accepted_assertions:
            try:
                gks_assertion = create_gks_record_from_assertion(item)
                transformed_assertion = Statement(**gks_assertion.model_dump())
            except (NotImplementedError, CivicGksRecordError):
                _logger.warning(
                    "unable to model CIViC assertion %s as a GKS statement", item.id
                )
                continue
            statements.append(transformed_assertion)
            if aggregate_statement := await self._create_aggregate_statement(
                transformed_assertion
            ):
                # include this statement as an item within an existing evidence line
                # if there is already an aggregate statement for this set of entities
                for existing_statement in statements:
                    if (
                        existing_statement.proposition
                        == aggregate_statement.proposition
                    ):
                        existing_statement.hasEvidenceLines[0].hasEvidenceItems.append(
                            transformed_assertion
                        )
                        break
                else:
                    statements.append(aggregate_statement)
            pbar.update(1)
        pbar.close()
        self.processed_data = TransformedData(statements=statements)

    @staticmethod
    def _evitem_to_vaspec(
        evidence_item: civicpy.Evidence | CivicGksEvidence,
    ) -> Statement | None:
        """Convert CIViC ev item to a va-spec-python object

        :param evidence_item: ev item from civic
        :return: valid ``Statement`` if able to convert
        """
        if isinstance(evidence_item, civicpy.Evidence):
            try:
                return Statement(**CivicGksEvidence(evidence_item).model_dump())
            except CivicGksRecordError:
                return None
        return Statement(**evidence_item.model_dump())

    async def _normalize_variant(
        self, variant: CategoricalVariant
    ) -> CategoricalVariant | None:
        """Build the normalized equivalent of a GKS-ified molecular profile from CIVIC

        :param variant: CIViC molecular profile
        :return: Categorical Variant or Protein Sequence Consequence with additional
            info, such as normalizer info.
            A Protein Sequence Consequence will be returned only if the molecular
            profile is a protein variant and it successfully normalizes, otherwise a
            Categorical Variant will be returned.
        """
        normalized_variation = None

        parsed_mp_components = self._parse_mp_name(variant.name)
        if not parsed_mp_components:
            _logger.warning(
                "Unable to parse molecular profile %i name %s",
                variant.id,
                variant.name,
            )
            return None

        pdot_expression = f"{parsed_mp_components.gene} {parsed_mp_components.p_change}"
        if not self._is_supported_variant_query(
            parsed_mp_components, pdot_expression, variant.id
        ):
            return None

        normalized_variation = await self.vicc_normalizers.normalize_variation(
            pdot_expression
        )

        if not normalized_variation:
            _logger.debug(
                "Variation Normalizer query `%s` from MPID %s appeared valid and supported, but failed to normalize",
                pdot_expression,
                variant.id,
            )
            return None

        if isinstance(normalized_variation, Allele):
            return build_proteinsequenceconsequence_catvar(normalized_variation)
        if isinstance(normalized_variation, CopyNumberChange):
            return build_copynumberchange_catvar(normalized_variation)
        raise NotImplementedError

    @staticmethod
    def _parse_mp_name(
        molecular_profile_name: str,
    ) -> MolecularProfileNameComponents | None:
        """Extract components from molecular profile name

        :param molecular_profile_name: CIViC Molecular Profile name
        :return: Molecular profile name components if pattern matches, otherwise None
        """
        match = re.match(MP_NAME_PATTERN, molecular_profile_name)
        return MolecularProfileNameComponents(**match.groupdict()) if match else None

    @staticmethod
    def _is_supported_variant_query(
        parsed_components: MolecularProfileNameComponents,
        variant_expr: str,
        variant_id: str,
    ) -> bool:
        """Validate whether the variant appears to be normalizable as a known CatVar

        For now, this is a yes/no check. In the future, when more kinds of catvars are
        supported, I think this should change into a "variant classifier" that returns
        what kind of variant the name appears to be, and then that can be checked against
        a list of supported/unsupported variants and dispatched accordingly.

        :param parsed_components:
        :param variant_expr: expression parsed from molecular profile name
        :param variant_id: CIViC molecular profile ID. Used for logging.
        :return: whether variant is supported or not
        """
        if parsed_components.c_change:
            msg = f"cDNA variant (ID: {variant_id}) not yet supported. This will be added in issue-225"
            _logger.warning(msg)
            return False

        pdot_change_expr_lower = variant_expr.lower()
        if (
            # is frameshift mutation
            (pdot_change_expr_lower.endswith("fs"))
            # has unsupported chars in gene or p. change
            or any(c in pdot_change_expr_lower for c in ("-", "/"))
            # contains a keyword indicating a known normalization failure
            or bool(set(pdot_change_expr_lower.split()) & UNABLE_TO_NORMALIZE_VAR_NAMES)
        ):
            _logger.debug(
                "Variation Normalizer does not support variant ID %s: '%s'",
                variant_id,
                variant_expr,
            )
            return False
        return True
