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
    Condition,
    ConditionSet,
    MembershipOperator,
    Statement,
    VariantDiagnosticProposition,
)
from ga4gh.vrs.models import Allele, MoleculeType
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
            if not isinstance(proposition, VariantDiagnosticProposition):
                _logger.error(
                    "Ev line proposition is not a diagnostic claim -- this is not currently supported by the MCI transformer: %s",
                    ev_item,
                )
                continue
            proposition.subjectVariant = self._transform_variant(
                proposition.subjectVariant.root
            )
            proposition.objectCondition = self._transform_disease(
                proposition.objectCondition.root
            )
            proposition.geneContextQualifier = self._transform_gene(
                proposition.geneContextQualifier
            )
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

    def _transform_disease(self, disease: MappableConcept) -> Condition:
        """Add pediatric_onset phenotype to MCI disease

        These items weren't originally curated to include this phenotype, but for the purposes
        of MetaKB, we can infer them with a generic pediatric onset phenotype.
        """
        if not disease.id:
            if not disease.primaryCoding:
                disease.id = f"mci.disease:{disease.name}"
            else:
                disease.id = disease.primaryCoding.code.root
        conditionset = ConditionSet(
            conditions=[disease, phenotypes.PEDIATRIC_ONSET],
            membershipOperator=MembershipOperator.AND,
        )

        self._ensure_conditionset_id(conditionset)
        return Condition(root=conditionset)

    def _transform_variant(self, variant: Allele) -> CategoricalVariant:
        """Format incoming variant as a MetaKB-compliant catvar

        * impute an ID
        * pull a name from the variant expressions array
        * fill in relations per transformer policy (this is WIP)
        """
        if len(variant.expressions or []) < 1:
            raise ValueError
        return CategoricalVariant(
            id=f"mci.cv:{variant.id.replace(':', '_')}",
            name=variant.expressions[0].value,
            constraints=[
                Constraint(
                    root=DefiningAlleleConstraint(
                        allele=variant,
                        relations=[LIFTOVER_TO_RELATION],
                    )
                )
            ],
        )

    def _transform_gene(self, gene: MappableConcept) -> MappableConcept:
        """Ensure gene has a simple ID so that it can be registered in the MetaKB DB"""
        gene.id = f"mci.gene:{gene.name}"
        return gene

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
