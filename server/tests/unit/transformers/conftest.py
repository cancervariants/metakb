import json
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
from civicpy import civic as civicpy
from tests.conftest import get_civic_annotation_ext, get_vicc_normalizer_priority_ext

from metakb.transformers.civic import CivicTransformer


@pytest.fixture(scope="session", autouse=True)
def civicpy_cache():
    cache_dir = Path(__file__).resolve().parents[2] / "data"
    cache_path = sorted(cache_dir.glob("civicpy_cache_*.pkl"))[-1]
    civicpy.load_cache(local_cache_path=cache_path, on_stale="ignore")


@pytest.fixture(scope="session")
def civic_eid26_proposition():
    """Create a test fixture for CIViC EID26 proposition."""
    return {
        "id": "proposition:_HXqJtIo6MSmwagQUSOot4wdKE7O4DyN",
        "predicate": "is_prognostic_of_worse_outcome_for",
        "subject": "ga4gh:VA.QSLb0bR-CRIFfKIENdHhcuUZwW3IS1aP",
        "object_qualifier": "ncit:C3171",
        "type": "prognostic_proposition",
    }


@pytest.fixture(scope="session")
def civic_did3():
    """Create test fixture for CIViC DID3."""
    return {
        "id": "civic.did:3",
        "conceptType": "Disease",
        "name": "Acute Myeloid Leukemia",
        "mappings": [
            {
                "coding": {
                    "id": "DOID:9119",
                    "system": "https://disease-ontology.org/?id=",
                    "code": "DOID:9119",
                },
                "relation": "exactMatch",
                "extensions": [
                    get_civic_annotation_ext(),
                    get_vicc_normalizer_priority_ext(is_priority=False),
                ],
            },
            {
                "coding": {
                    "name": "Acute Myeloid Leukemia",
                    "id": "ncit:C3171",
                    "code": "C3171",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                },
                "relation": "exactMatch",
                "extensions": [get_vicc_normalizer_priority_ext(is_priority=True)],
            },
            {
                "coding": {
                    "id": "MONDO_0018874",
                    "code": "MONDO:0018874",
                    "system": "https://purl.obolibrary.org/obo/",
                },
                "relation": "exactMatch",
                "extensions": [get_vicc_normalizer_priority_ext(is_priority=False)],
            },
        ],
    }


@pytest.fixture(scope="session")
def civic_mpid65(civic_vid65, psc_relations):
    """Create a test fixture for CIViC VID65."""
    return {
        "id": "civic.mpid:65",
        "type": "CategoricalVariant",
        "description": "KIT D816V is a mutation observed in acute myeloid leukemia (AML). This variant has been linked to poorer prognosis and worse outcome in AML patients.",
        "name": "KIT D816V",
        "constraints": [
            {
                "allele": civic_vid65,
                "type": "DefiningAlleleConstraint",
                "relations": psc_relations,
            }
        ],
        "members": [
            {
                "id": "ga4gh:VA.MQQ62X5KMlj9gDKjOkE1lIZjAY9k_7g4",
                "type": "Allele",
                "name": "NM_000222.2:c.2447A>T",
                "digest": "MQQ62X5KMlj9gDKjOkE1lIZjAY9k_7g4",
                "expressions": [{"syntax": "hgvs.c", "value": "NM_000222.2:c.2447A>T"}],
                "location": {
                    "id": "ga4gh:SL.vfWDYUfL2sqohE0wtojKCZ6PlLAPPvjl",
                    "type": "SequenceLocation",
                    "digest": "vfWDYUfL2sqohE0wtojKCZ6PlLAPPvjl",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.5UOthuwxqhwdsrbA4bVonC2ps_Njx1gh",
                    },
                    "start": 2504,
                    "end": 2505,
                    "sequence": "A",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "T"},
            },
            {
                "id": "ga4gh:VA.MQQ62X5KMlj9gDKjOkE1lIZjAY9k_7g4",
                "type": "Allele",
                "name": "ENST00000288135.5:c.2447A>T",
                "digest": "MQQ62X5KMlj9gDKjOkE1lIZjAY9k_7g4",
                "expressions": [
                    {"syntax": "hgvs.c", "value": "ENST00000288135.5:c.2447A>T"}
                ],
                "location": {
                    "id": "ga4gh:SL.vfWDYUfL2sqohE0wtojKCZ6PlLAPPvjl",
                    "type": "SequenceLocation",
                    "digest": "vfWDYUfL2sqohE0wtojKCZ6PlLAPPvjl",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.5UOthuwxqhwdsrbA4bVonC2ps_Njx1gh",
                    },
                    "start": 2504,
                    "end": 2505,
                    "sequence": "A",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "T"},
            },
            {
                "id": "ga4gh:VA.UQJIH49-agpdZzdyGiM4NQE_njoQy0m6",
                "type": "Allele",
                "name": "NC_000004.11:g.55599321A>T",
                "digest": "UQJIH49-agpdZzdyGiM4NQE_njoQy0m6",
                "expressions": [
                    {"syntax": "hgvs.g", "value": "NC_000004.11:g.55599321A>T"}
                ],
                "location": {
                    "id": "ga4gh:SL.aAqDEdLIeXIQOX6LaJaaiOuC7lgo_DZk",
                    "type": "SequenceLocation",
                    "digest": "aAqDEdLIeXIQOX6LaJaaiOuC7lgo_DZk",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.HxuclGHh0XCDuF8x6yQrpHUBL7ZntAHc",
                    },
                    "start": 54733154,
                    "end": 54733155,
                    "sequence": "A",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "T"},
            },
        ],
        "mappings": [
            {
                "coding": {
                    "code": "CA123513",
                    "system": "https://reg.clinicalgenome.org/redmine/projects/registry/genboree_registry/by_canonicalid?canonicalid=",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "13852",
                    "system": "https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "rs121913507",
                    "system": "https://www.ncbi.nlm.nih.gov/snp/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "id": "civic.vid:65",
                    "code": "65",
                    "name": "D816V",
                    "system": "https://civicdb.org/links/variant/",
                    "extensions": [
                        {"name": "subtype", "value": "gene_variant"},
                        {
                            "name": "variant_types",
                            "value": [
                                {
                                    "coding": {
                                        "id": "civic.variant_type:47",
                                        "name": "Missense Variant",
                                        "system": "http://www.sequenceontology.org/browser/current_svn/term/",
                                        "code": "SO:0001583",
                                    },
                                    "relation": "exactMatch",
                                }
                            ],
                        },
                    ],
                },
                "relation": "exactMatch",
            },
            {
                "coding": {
                    "id": "civic.mpid:65",
                    "code": "65",
                    "system": "https://civicdb.org/links/molecular_profile/",
                },
                "relation": "exactMatch",
            },
        ],
        "aliases": ["ASP816VAL"],
        "extensions": [
            {
                "name": "expressions",
                "value": [
                    {"syntax": "hgvs.p", "value": "NP_000213.1:p.Asp816Val"},
                    {"syntax": "hgvs.c", "value": "NM_000222.2:c.2447A>T"},
                    {"syntax": "hgvs.c", "value": "ENST00000288135.5:c.2447A>T"},
                    {"syntax": "hgvs.g", "value": "NC_000004.11:g.55599321A>T"},
                ],
            },
            {
                "name": "CIViC representative coordinate",
                "value": {
                    "chromosome": "4",
                    "start": 55599321,
                    "stop": 55599321,
                    "reference_bases": "A",
                    "variant_bases": "T",
                    "representative_transcript": "ENST00000288135.5",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates",
                },
            },
            {
                "name": "CIViC Molecular Profile Score",
                "value": 67.0,
            },
        ],
    }


@pytest.fixture(scope="session")
def civic_gid29():
    """Create test fixture for CIViC GID29."""
    return {
        "id": "civic.gid:29",
        "conceptType": "Gene",
        "name": "KIT",
        "extensions": [
            {
                "name": "description",
                "value": "c-KIT activation has been shown to have oncogenic activity in gastrointestinal stromal tumors (GISTs), melanomas, lung cancer, and other tumor types. The targeted therapeutics nilotinib and sunitinib have shown efficacy in treating KIT overactive patients, and are in late-stage trials in melanoma and GIST. KIT overactivity can be the result of many genomic events from genomic amplification to overexpression to missense mutations. Missense mutations have been shown to be key players in mediating clinical response and acquired resistance in patients being treated with these targeted therapeutics.",
            },
            {
                "name": "aliases",
                "value": ["MASTC", "KIT", "SCFR", "PBT", "CD117", "C-Kit"],
            },
        ],
        "mappings": [
            {
                "coding": {
                    "system": "https://www.ncbi.nlm.nih.gov/gene/",
                    "id": "ncbigene:3815",
                    "code": "3815",
                },
                "relation": "exactMatch",
                "extensions": [
                    get_vicc_normalizer_priority_ext(is_priority=False),
                    get_civic_annotation_ext(),
                ],
            },
            {
                "coding": {
                    "system": "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/",
                    "id": "hgnc:6342",
                    "code": "HGNC:6342",
                    "name": "KIT",
                },
                "relation": "exactMatch",
                "extensions": [get_vicc_normalizer_priority_ext(is_priority=True)],
            },
        ],
    }


@pytest.fixture(scope="session")
def pmid_16384925():
    """Create a test fixture for PMID 16384925."""
    return {
        "id": "civic.source:69",
        "name": "Cairoli et al., 2006",
        "title": "Prognostic impact of c-KIT mutations in core binding factor leukemias: an Italian retrospective study.",
        "pmid": "16384925",
        "type": "Document",
    }


@pytest.fixture(scope="session")
def civic_eid26_study_stmt(
    civic_mpid65, civic_gid29, civic_did3, civic_method, pmid_16384925
):
    """Create a test fixture for CIViC EID26 study statement."""
    return {
        "id": "civic.eid:26",
        "description": "In acute myloid leukemia patients, D816 mutation is associated with earlier relapse and poorer prognosis than wildtype KIT.",
        "direction": "supports",
        "strength": {
            "name": "Clinical evidence",
            "primaryCoding": {
                "system": "https://civic.readthedocs.io/en/latest/model/evidence/level.html",
                "code": "B",
            },
            "mappings": [
                {
                    "coding": {
                        "system": "https://go.osu.edu/evidence-codes",
                        "code": "e000005",
                        "name": "clinical cohort evidence",
                    },
                    "relation": "exactMatch",
                }
            ],
        },
        "proposition": {
            "type": "VariantPrognosticProposition",
            "predicate": "associatedWithWorseOutcomeFor",
            "alleleOriginQualifier": {
                "name": "somatic",
                "extensions": [{"name": "civic_variant_origin", "value": "SOMATIC"}],
            },
            "subjectVariant": civic_mpid65,
            "geneContextQualifier": civic_gid29,
            "objectCondition": civic_did3,
        },
        "specifiedBy": civic_method,
        "reportedIn": [pmid_16384925, "https://civicdb.org/links/evidence/26"],
        "type": "Statement",
    }


@pytest_asyncio.fixture
async def civic_cdm_data(normalizers, tmp_path):
    """Get CIViC CDM data."""

    async def _civic_cdm_data(
        evidence_items, assertions, file_name=None, create_json=True
    ):
        with (
            patch.object(
                civicpy,
                "get_all_evidence",
                return_value=evidence_items,
            ),
            patch.object(civicpy, "get_all_assertions", return_value=assertions),
        ):
            t = CivicTransformer(data_dir=tmp_path, normalizers=normalizers)
            await t.transform()

            if create_json:
                t.create_json(tmp_path / file_name)
                with (tmp_path / file_name).open() as f:
                    return json.load(f)

            return t

    return _civic_cdm_data
