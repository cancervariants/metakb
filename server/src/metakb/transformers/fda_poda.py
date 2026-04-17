"""Transform data from the FDA Pediatric Oncology Drug Approvals curation to be imported into MetaKB"""

import hashlib
import json
import logging
import re
from pathlib import Path

from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.core.models import Coding, Extension, MappableConcept, code
from ga4gh.va_spec.base import (
    ConditionSet,
    Document,
    MembershipOperator,
    Statement,
    TherapyGroup,
)
from ga4gh.vrs.models import Allele
from tqdm import tqdm

from metakb.harvesters.fda_poda import FdaPodaHarvestedData
from metakb.schemas.data import TransformedData
from metakb.transformers import catvars as build_catvars
from metakb.transformers.base import Transformer
from metakb.transformers.identifiers import compute_combo_id

_logger = logging.getLogger(__name__)

PEDIATRIC_ONSET = MappableConcept(
    id="HP:0410280",
    name="Pediatric onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0410280"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of disease manifestations before adulthood, defined here as before the age of 16 years, but excluding neonatal or congenital onset.",
        )
    ],
    conceptType="Phenotype",
)
NEONATAL_ONSET = MappableConcept(
    id="HP:0003623",
    name="Neonatal onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0003623"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of signs or symptoms of disease within the first 28 days of life.",
        )
    ],
    conceptType="Phenotype",
)
CHILDHOOD_ONSET = MappableConcept(
    id="HP:0011463",
    name="Childhood onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0011463"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of disease at the age of between 1 and 5 years.",
        )
    ],
    conceptType="Phenotype",
)
INFANTILE_ONSET = MappableConcept(
    id="HP:0003593",
    name="Infantile onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/", code=code("HP:0003593")
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of signs or symptoms of disease between 28 days to one year of life.",
        )
    ],
    conceptType="Phenotype",
)
JUVENILE_ONSET = MappableConcept(
    id="HP:0003621",
    name="Juvenile onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0003621"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of signs or symptoms of disease between the age of 5 and 15 years.",
        )
    ],
    conceptType="Phenotype",
)
ADULT_ONSET = MappableConcept(
    id="HP:0003581",
    name="Adult onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0003581"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of disease manifestations in adulthood, defined here as at the age of 16 years or later.",
        )
    ],
    conceptType="Phenotype",
)


class FdaPodaTransformer(Transformer):
    """Transform curated FDA PODA statements into MetaKB data model, including assertion grouping"""

    async def transform(self, harvested_data_path: Path) -> TransformedData:
        """Transform MOA harvested JSON to common data model.

        Will store transformed results in ``processed_data`` instance variable.

        For each statement:
        * Build its base GKS equivalent
        * Try to normalize variant, disease, gene(, drug)
        * If they all normalize, also build the aggregate statement, supported by
          an evidence line to the base statement

        :param harvested_data: MOA harvested data
        """
        with harvested_data_path.open() as f:
            harvested_data = FdaPodaHarvestedData(**json.load(f))
        statements: list[Statement] = []
        assertions: dict[str, Statement] = {}
        for ev_item in tqdm(harvested_data.statements):
            if isinstance(ev_item.proposition.conditionQualifier.root, ConditionSet):
                self._ensure_conditionset_id(
                    ev_item.proposition.conditionQualifier.root
                )
                self._ensure_document_id(ev_item.specifiedBy.reportedIn)
                for doc in ev_item.reportedIn:
                    self._ensure_document_id(doc)
            therapeutic = ev_item.proposition.objectTherapeutic
            if isinstance(therapeutic.root, TherapyGroup):
                therapeutic.root.id = compute_combo_id(
                    self.src_data_store.src_name,
                    TherapyGroup,
                    therapeutic.root.membershipOperator,
                    [c.id for c in therapeutic.root.therapies],
                )

            ev_item.strength.extensions = [
                Extension(
                    name="metakb_display_value",
                    value="A",
                )
            ]
            statements.append(ev_item)
            await self._upsert_assertion_from_evidence(ev_item, assertions)
        return TransformedData(
            evidence=statements, assertions=list(assertions.values())
        )

    def _ensure_document_id(self, document: Document) -> None:
        """Affix an ID onto a Document. Modifies it in-place

        :param document: incoming document (must have a URL)
        """
        url = document.urls[0]
        h = hashlib.sha1(url.encode()).hexdigest()[:10]  # noqa: S324
        document.id = f"web:{h}"

    async def _normalize_variant(
        self, variant: CategoricalVariant
    ) -> CategoricalVariant | None:
        queries = [variant.name]
        result = None
        for query in queries:
            if match := re.match(r"(.*) (Mutation|MUTATION|mutation)", query):
                gene_name = match.groups()[0]
                normalized_gene = self._normalize_gene(MappableConcept(name=gene_name))
                if normalized_gene:
                    return build_catvars.build_featurecontext_catvar(normalized_gene)
            result = await self.vicc_normalizers.normalize_variation(query)
            if result and isinstance(result, Allele):
                return build_catvars.build_proteinsequenceconsequence_catvar(
                    self.vicc_normalizers.seqrepo_access,
                    self.vicc_normalizers.transcript_mappings,
                    result,
                )
        _logger.debug(
            "Failed to normalize variant: %s", variant.model_dump(exclude_none=True)
        )
        return None

    def _normalize_phenotype(
        self, phenotype: MappableConcept
    ) -> MappableConcept | ConditionSet | None:
        """Perform simple rule-based phenotype normalization for know age of onset terms.

        Overrides transformer base method (which doesn't do anything) to perform
        age of onset-specific logic.

        :param phenotype: mappableconcept w/ concepttype declared as "Phenotype" (this is not validated)
        :return: HPO term mapped from input, if available
        """
        if phenotype.name == "Pediatric":
            # this is a weird case -- going with the safest match for now, but
            # could be worth revisiting in the future
            return PEDIATRIC_ONSET
        operator = MembershipOperator.OR
        conditions = []
        if phenotype.name == "0 years and older":
            conditions = [
                NEONATAL_ONSET,
                CHILDHOOD_ONSET,
                JUVENILE_ONSET,
                ADULT_ONSET,
            ]
        elif phenotype.name in {
            "1 month and older",
            "6 months and older",
            "1 year and older",
            "2 years and older",
        }:
            conditions = [CHILDHOOD_ONSET, JUVENILE_ONSET, ADULT_ONSET]
        if phenotype.name == "12 years and older":
            conditions = [JUVENILE_ONSET, ADULT_ONSET]
        if conditions:
            return ConditionSet(
                id=compute_combo_id(
                    "metakb",
                    ConditionSet,
                    operator,
                    [c.id for c in conditions],
                ),
                membershipOperator=operator,
                conditions=conditions,
            )
        return None
