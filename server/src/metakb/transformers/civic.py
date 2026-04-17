"""A module for to transform CIViC."""

import logging
import re
from pathlib import Path
from uuid import uuid4

from civicpy import civic as civicpy
from civicpy.exports.civic_gks_record import (
    CivicGksEvidence,
    CivicGksRecordError,
    create_gks_record_from_assertion,
)
from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.core.models import Extension, iriReference
from ga4gh.va_spec.base import (
    ConditionSet,
    Document,
    EvidenceLine,
    Statement,
    TherapyGroup,
    VariantTherapeuticResponseProposition,
)
from ga4gh.vrs.models import Allele, CopyNumberChange
from pydantic.dataclasses import dataclass
from tqdm import tqdm

from metakb.schemas.data import TransformedData
from metakb.transformers.base import Transformer
from metakb.transformers.catvars import (
    build_copynumberchange_catvar,
    build_proteinsequenceconsequence_catvar,
)
from metakb.transformers.identifiers import compute_combo_id

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

    @staticmethod
    def _assertion_has_vcep_approval(item: civicpy.Assertion) -> bool:
        """Check if any of the assertion's approvals is from a VCEP-approved org.
        :param item: The civicpy Assertion to check
        :return: True if an approval was found where the organization that approved it is an SC-VCEP
        """
        return any(
            getattr(getattr(approval, "organization", None), "is_approved_vcep", False)
            for approval in (getattr(item, "approvals", None) or [])
        )

    async def transform(self, harvested_data_path: Path) -> TransformedData:
        """Transform CIViC evidence and assertions to common data model.

        Store result in ``transformed_data`` instance variable.

        For each statement:
        * Build its base GKS equivalent
        * Try to normalize variant, disease, gene(, drug)
        * If they all normalize, also build the aggregate statement, supported by
          an evidence line to the base statement
        """
        civicpy.load_cache(str(harvested_data_path), on_stale="ignore")
        accepted_evidence_items = civicpy.get_all_evidence(include_status=["accepted"])
        accepted_assertions = civicpy.get_all_assertions(include_status=["accepted"])
        statements = []
        assertions = {}
        for item in tqdm([*accepted_evidence_items, *accepted_assertions]):
            transformed_statement = self._civic_claim_to_statement(item)
            if not transformed_statement:
                _logger.warning(
                    "Unable to model civic statement %s (type: %s) as a GKS statement",
                    item,
                    type(item),
                )
                continue
            statements.append(transformed_statement)

            await self._upsert_assertion_from_evidence(
                transformed_statement, assertions
            )
        return TransformedData(
            evidence=statements, assertions=list(assertions.values())
        )

    def _ensure_evidenceline_id(self, evidence_line: EvidenceLine) -> None:
        """Ensure that an evidence line object has an ID

        Modifies object in-place with UUID

        :param evidence_line: evidence line underneath a civic assertion
        """
        if not evidence_line.hasEvidenceItems:
            raise ValueError
        for item in evidence_line.hasEvidenceItems:
            if isinstance(item, EvidenceLine):
                self._ensure_evidenceline_id(item)
        evidence_line.id = f"civic.evline:{uuid4()}"

    def _ensure_therapygroup_id(self, therapy_group: TherapyGroup) -> None:
        """Ensure that a therapy group has an ID

        Modifies incoming object in-place if necessary.

        :param therapy_group: therapy group object from CIViC
        """
        if therapy_group.id:
            _logger.info("CIViC therapy group # %s already has an ID", therapy_group.id)
            return
        therapy_group.id = compute_combo_id(
            self.src_data_store.src_name,
            TherapyGroup,
            therapy_group.membershipOperator,
            [th.id for th in therapy_group.therapies],
        )

    def _civic_claim_to_statement(
        self,
        item: civicpy.Evidence | CivicGksEvidence | civicpy.Assertion,
    ) -> Statement | None:
        """From the CIViC evidence item/assertion, create an ingestable VA-Spec statement

        civicpy gets us 99% of the way there, but we need to

        1) transform them into ``ga4gh.va_spec`` classes
        2) mint IDs for some combo elements that CIViC doesn't provide
        3) do the same for anything contained within an evidence line

        :param item: CIViC evidence item or assertion
        :return: completely transformed VA-Spec statement object
        :raise TypeError: if unrecognized item type is given
        """
        statement = None
        if isinstance(item, civicpy.Evidence):
            try:
                statement = Statement(**CivicGksEvidence(item).model_dump())
            except CivicGksRecordError:
                _logger.warning(
                    "Unable to convert civic evidence item %s to a Statement via CivicGksEvidence",
                    item.id,
                )
                return None
            statement.strength.extensions = [
                Extension(
                    name="metakb_display_value",
                    value=statement.strength.primaryCoding.code.root,
                )
            ]
            statement.strength.id = (
                f"civic.strength:{statement.strength.primaryCoding.code.root}"
            )
        elif isinstance(item, CivicGksEvidence):
            statement = Statement(**item.model_dump())
            statement.strength.extensions = [
                Extension(
                    name="metakb_display_value",
                    value=statement.strength.primaryCoding.code.root,
                )
            ]
            statement.strength.id = (
                f"civic.strength:{statement.strength.primaryCoding.code.root}"
            )
        elif isinstance(item, civicpy.Assertion):
            try:
                statement = create_gks_record_from_assertion(item)
                # TODO: Put VCEP approval flag in civicpy instead.
                # Added here for now to get the functionality in
                statement_exts = statement.extensions or []
                statement_exts.append(
                    Extension(
                        name="has_vcep_approval",
                        value=self._assertion_has_vcep_approval(item),
                    )
                )
                statement.extensions = statement_exts
                statement.strength.extensions = [
                    Extension(
                        name="metakb_display_value",
                        value=statement.strength.primaryCoding.code.root.removeprefix(
                            "Level "
                        ),
                    )
                ]
                statement.strength.id = (
                    f"amp_asco_cap:{statement.strength.primaryCoding.code.root}"
                )
                for evline in statement.hasEvidenceLines:
                    self._ensure_evidenceline_id(evline)
            except (NotImplementedError, CivicGksRecordError):
                _logger.warning(
                    "unable to convert CIViC assertion %s to a Statement: unsupported type",
                    item.id,
                )
                return None
        else:
            msg = f"Received unexpected item type while transforming CIViC claims to GKS: {type(item)}"
            raise TypeError(msg)

        if isinstance(statement.proposition, VariantTherapeuticResponseProposition):
            if isinstance(statement.proposition.objectTherapeutic.root, TherapyGroup):
                self._ensure_therapygroup_id(
                    statement.proposition.objectTherapeutic.root
                )
            if isinstance(statement.proposition.conditionQualifier.root, ConditionSet):
                self._ensure_conditionset_id(
                    statement.proposition.conditionQualifier.root
                )
        elif isinstance(statement.proposition.objectCondition.root, ConditionSet):
            self._ensure_conditionset_id(statement.proposition.objectCondition.root)

        if statement.hasEvidenceLines:
            for ev_line in statement.hasEvidenceLines:
                if ev_line.hasEvidenceItems:
                    ev_line.hasEvidenceItems = [
                        self._civic_claim_to_statement(i)
                        for i in ev_line.hasEvidenceItems
                    ]
            reported_in = []
            for doc in statement.reportedIn:
                if isinstance(doc, iriReference) and doc.root.startswith(
                    "https://civicdb.org"
                ):
                    reported_in.append(
                        Document(id=doc.root, name=statement.id, urls=[doc.root])
                    )
                else:
                    reported_in.append(doc)

            statement.reportedIn = reported_in
        return statement

    async def _normalize_variant(
        self, variant: CategoricalVariant
    ) -> CategoricalVariant | None:
        """Build the normalized equivalent of a GKS-ified molecular profile from CIVIC

        :param variant: CIViC molecular profile
        :return: Fully fleshed-out categorical variant entailed by normalization of the
            source variant, if successful
        :raise NotImplementedError: if variant normalizes to unrecognized/unsupported type
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
            cv = build_proteinsequenceconsequence_catvar(
                self.vicc_normalizers.seqrepo_access,
                self.vicc_normalizers.transcript_mappings,
                normalized_variation,
            )
        elif isinstance(normalized_variation, CopyNumberChange):
            cv = build_copynumberchange_catvar(normalized_variation)
        else:
            return None
        if len(cv.constraints) > 1:
            _logger.debug(
                "Civic molecular profile %s normalizes to a CV with >1 constraints; this is currently unsupported"
            )
            return None
        return cv

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
