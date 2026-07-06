"""Transform AMP/ASCO/CAP statements from the MCI project into MetaKB-ready format"""

import json
import logging
from pathlib import Path

from ga4gh.cat_vrs.models import (
    CategoricalVariant,
    Constraint,
    DefiningAlleleConstraint,
)
from ga4gh.cat_vrs.relations import LIFTOVER_TO_RELATION
from ga4gh.core.models import Extension, MappableConcept
from ga4gh.va_spec.base import (
    ClinicalVariantProposition,
    Condition,
    ConditionSet,
    MembershipOperator,
    # MembershipOperator,
    Statement,
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
)
from ga4gh.vrs.models import MoleculeType
from tqdm import tqdm

from metakb.harvesters.mci import MciHarvestedData
from metakb.schemas.data import TransformedData
from metakb.transformers import phenotypes
from metakb.transformers.base import Transformer
from metakb.transformers.identifiers import hash_proposition

_logger = logging.getLogger(__name__)


class MciTransformer(Transformer):
    """Transform MCI data."""

    async def transform(self, harvested_data_path: Path) -> TransformedData:
        """Transform MCI statements JSON dump to common data model.

        Will store transformed results in ``processed_data`` instance variable.

        Transformations/post-processing we have to do:

        * Collapse the evidence line and clinical significance assertion to reconstruct
          a non-AMP/ASCO/CAP statement (which is not supported by MetaKB).
        * Add ID to statement. This is unstable because it's dependent on a hash of the
          proposition -- we expect an upstream fix to this in the future.
        * Add IDs to all proposition entities. Add name to catvar.
        * Add "pediatric onset" phenotype to all diseases

        :param harvested_data: FDA-PODA harvested data
        :return: transformed statements
        """
        with harvested_data_path.open() as f:
            harvested_data = MciHarvestedData(**json.load(f))
        statements: list[Statement] = []
        assertions: dict[str, Statement] = {}
        for ev_item in tqdm(harvested_data.statements):
            if len(ev_item.hasEvidenceLines) != 1:
                _logger.info(
                    "Encountered MCI clin sig stmt with multiple evidence lines; unable to collate to a supported proposition type"
                )
                continue
            ev_line = ev_item.hasEvidenceLines[0]
            if ev_line.hasEvidenceItems:
                _logger.info(
                    "Encountered MCI clin sig stmt with evidence items underneath the evidence line. This is a drift in structure and will require additional work on the transformer to support ingestion."
                )
                continue
            proposition = ev_line.targetProposition
            ev_allele = proposition.subjectVariant.root
            proposition.subjectVariant = CategoricalVariant(
                id=f"mci.cv:{ev_allele.id.replace(':', '_')}",
                name=proposition.subjectVariant.root.expressions[0].value,
                constraints=[
                    Constraint(
                        root=DefiningAlleleConstraint(
                            allele=proposition.subjectVariant.root,
                            relations=[LIFTOVER_TO_RELATION],
                        )
                    )
                ],
            )
            proposition_disease: MappableConcept = proposition.objectCondition.root
            if not proposition_disease.id:
                if not proposition_disease.primaryCoding:
                    proposition_disease.id = f"mci.disease:{proposition_disease.name}"
                else:
                    proposition_disease.id = proposition_disease.primaryCoding.code.root
            proposition.objectCondition = Condition(
                root=ConditionSet(
                    conditions=[proposition_disease, phenotypes.PEDIATRIC_ONSET],
                    membershipOperator=MembershipOperator.AND,
                )
            )
            proposition = self._ensure_entity_ids(proposition)
            statement = Statement(
                id=f"mci.statement:{hash_proposition(proposition)}",
                strength=ev_line.strengthOfEvidenceProvided,
                proposition=proposition,
                direction=ev_line.directionOfEvidenceProvided,
                contributions=ev_item.contributions,
                extensions=ev_item.extensions,
                specifiedBy=ev_item.specifiedBy,
                reportedIn=ev_line.reportedIn,
            )
            statement.specifiedBy.id = "mci.method:1"
            statement.strength.id = (
                f"amp_asc_cap:{statement.strength.primaryCoding.code.root}"
            )
            statement.strength.extensions = [
                Extension(
                    name="metakb_display_value",
                    value=statement.strength.primaryCoding.code.root,
                )
            ]
            statements.append(statement)
            await self._upsert_assertion_from_evidence(statement, assertions)
        return TransformedData(
            evidence=statements, assertions=list(assertions.values())
        )

    def _ensure_condition_id(self, condition: Condition) -> Condition:
        """Ensure that a condition has a populated root identifier

        Used to create IDs for loading in the DB and for generating higher level
        hashed IDs
        """
        if not condition.root.id:
            if isinstance(condition.root, MappableConcept):
                if condition.root.primaryCoding:
                    condition.root.id = condition.root.primaryCoding.code.root
                else:
                    condition.root.id = condition.root.name
            else:
                self._ensure_conditionset_id(condition.root)
        return condition

    def _ensure_entity_ids(
        self, prop: ClinicalVariantProposition
    ) -> ClinicalVariantProposition:
        prop.geneContextQualifier.id = f"mci.gene:{prop.geneContextQualifier.name}"
        if isinstance(
            prop, (VariantDiagnosticProposition, VariantPrognosticProposition)
        ):
            prop.objectCondition = self._ensure_condition_id(prop.objectCondition)
        else:
            msg = "Encountered unexpected proposition type -- has the underlying data changed?"
            _logger.exception("Unexpected proposition type: %s", prop)
            raise TypeError(msg)
        return prop

    async def _normalize_variant(
        self, variant: CategoricalVariant
    ) -> CategoricalVariant | None:
        """Normalize MCI-provided variant."""
        if not len(variant.constraints) == 1:
            raise ValueError
        if not isinstance(variant.constraints[0].root, DefiningAlleleConstraint):
            raise TypeError
        allele = variant.constraints[0].root.allele
        if allele.location.sequenceReference.moleculeType in {
            MoleculeType.RNA,
            MoleculeType.GENOMIC,
        }:
            cv_id = f"metakb.cv:DAC.{allele.id.split(':')[1]}"
        else:
            raise ValueError
        return CategoricalVariant(
            id=cv_id, name=variant.name, constraints=variant.constraints
        )
