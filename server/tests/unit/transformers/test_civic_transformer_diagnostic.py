"""Test CIViC Transformation to common data model for diagnostic."""

import json

import pytest
import pytest_asyncio
from tests.conftest import (
    TEST_TRANSFORMERS_DIR,
    get_civic_annotation_ext,
    get_vicc_normalizer_priority_ext,
)

from metakb.transformers.civic import CivicTransformer

DATA_DIR = TEST_TRANSFORMERS_DIR / "diagnostic"
FILENAME = "civic_cdm.json"


@pytest_asyncio.fixture(scope="module")
async def data(normalizers):
    """Create a CIViC Transformer test fixture."""
    harvester_path = DATA_DIR / "civic_harvester.json"
    c = CivicTransformer(
        data_dir=DATA_DIR, harvester_path=harvester_path, normalizers=normalizers
    )
    harvested_data = c.extract_harvested_data()
    await c.transform(harvested_data)
    c.create_json(DATA_DIR / FILENAME)
    with (DATA_DIR / FILENAME).open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def civic_mpid99():
    """Create a test fixture for CIViC MP 99."""
    return {
        "id": "civic.mpid:99",
        "type": "CategoricalVariant",
        "description": "PDGFRA D842 mutations are characterized broadly as imatinib resistance mutations. This is most well characterized in gastrointestinal stromal tumors, but other cell lines containing these mutations have been shown to be resistant as well. Exogenous expression of the A842V mutation resulted in constitutive tyrosine phosphorylation of PDGFRA in the absence of ligand in 293T cells and cytokine-independent proliferation of the IL-3-dependent Ba/F3 cell line, both evidence that this is an activating mutation. In imatinib resistant cell lines, a number of other therapeutics have demonstrated efficacy. These include; crenolanib, sirolimus, and midostaurin (PKC412).",
        "name": "PDGFRA D842V",
        "constraints": [
            {
                "allele": {
                    "id": "ga4gh:VA.Dy7soaZQU1vH9Eb93xG_pJyhu7xTDDC9",
                    "type": "Allele",
                    "name": "D842V",
                    "digest": "Dy7soaZQU1vH9Eb93xG_pJyhu7xTDDC9",
                    "expressions": [
                        {"syntax": "hgvs.p", "value": "NP_006197.1:p.Asp842Val"},
                        {"syntax": "hgvs.c", "value": "NM_006206.4:c.2525A>T"},
                        {"syntax": "hgvs.c", "value": "ENST00000257290.5:c.2525A>T"},
                        {"syntax": "hgvs.g", "value": "NC_000004.11:g.55152093A>T"},
                    ],
                    "location": {
                        "id": "ga4gh:SL.xuh2OFm73UN7_0uLySrRY2Xe3FW7KJ5h",
                        "type": "SequenceLocation",
                        "digest": "xuh2OFm73UN7_0uLySrRY2Xe3FW7KJ5h",
                        "sequenceReference": {
                            "type": "SequenceReference",
                            "refgetAccession": "SQ.XpQn9sZLGv_GU3uiWO7YHq9-_alGjrVX",
                        },
                        "start": 841,
                        "end": 842,
                        "sequence": "D",
                    },
                    "state": {"type": "LiteralSequenceExpression", "sequence": "V"},
                },
                "type": "DefiningAlleleConstraint",
            }
        ],
        "members": [
            {
                "id": "ga4gh:VA.TAskYi2zB3_dTtdyqyIxXKlYosf4cbJo",
                "type": "Allele",
                "name": "NM_006206.4:c.2525A>T",
                "digest": "TAskYi2zB3_dTtdyqyIxXKlYosf4cbJo",
                "expressions": [{"syntax": "hgvs.c", "value": "NM_006206.4:c.2525A>T"}],
                "location": {
                    "id": "ga4gh:SL.8w-z6Kgyuzx1yA51AQPX7QKCbuZgUIa1",
                    "type": "SequenceLocation",
                    "digest": "8w-z6Kgyuzx1yA51AQPX7QKCbuZgUIa1",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.P_hYEl9XPZMg9zb-vhiwr4SNXtkCutiu",
                    },
                    "start": 2659,
                    "end": 2660,
                    "sequence": "A",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "T"},
            },
            {
                "id": "ga4gh:VA.B6-IjSb5S6K46BbJWPAvSD5vWz4tqW1j",
                "type": "Allele",
                "name": "NC_000004.11:g.55152093A>T",
                "digest": "B6-IjSb5S6K46BbJWPAvSD5vWz4tqW1j",
                "expressions": [
                    {"syntax": "hgvs.g", "value": "NC_000004.11:g.55152093A>T"}
                ],
                "location": {
                    "id": "ga4gh:SL.aDuNtHik7usLDSaoVpVv883hG7u0uPGv",
                    "type": "SequenceLocation",
                    "digest": "aDuNtHik7usLDSaoVpVv883hG7u0uPGv",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.HxuclGHh0XCDuF8x6yQrpHUBL7ZntAHc",
                    },
                    "start": 54285925,
                    "end": 54285926,
                    "sequence": "A",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "T"},
            },
        ],
        "mappings": [
            {
                "coding": {
                    "code": "CA123194",
                    "system": "https://reg.clinicalgenome.org/redmine/projects/registry/genboree_registry/by_canonicalid?canonicalid=",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "13543",
                    "system": "https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "rs121908585",
                    "system": "https://www.ncbi.nlm.nih.gov/snp/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "id": "civic.vid:99",
                    "code": "99",
                    "system": "https://civicdb.org/variants/",
                },
                "relation": "exactMatch",
            },
        ],
        "aliases": ["ASP842VAL"],
        "extensions": [
            {
                "name": "CIViC representative coordinate",
                "value": {
                    "chromosome": "4",
                    "start": 55152093,
                    "stop": 55152093,
                    "reference_bases": "A",
                    "variant_bases": "T",
                    "representative_transcript": "ENST00000257290.5",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates",
                },
            },
            {
                "name": "CIViC Molecular Profile Score",
                "value": 100.5,
            },
            {
                "name": "Variant types",
                "value": [
                    {
                        "id": "SO:0001583",
                        "code": "SO:0001583",
                        "system": "http://www.sequenceontology.org/browser/current_svn/term/",
                        "name": "missense_variant",
                    }
                ],
            },
        ],
    }


@pytest.fixture(scope="module")
def civic_gid38():
    """Create test fixture for CIViC GID38."""
    return {
        "id": "civic.gid:38",
        "conceptType": "Gene",
        "name": "PDGFRA",
        "mappings": [
            {
                "coding": {
                    "id": "ncbigene:5156",
                    "code": "5156",
                    "system": "https://www.ncbi.nlm.nih.gov/gene/",
                },
                "relation": "exactMatch",
                "extensions": [
                    get_vicc_normalizer_priority_ext(is_priority=False),
                    get_civic_annotation_ext(),
                ],
            },
            {
                "coding": {
                    "name": "PDGFRA",
                    "id": "hgnc:8803",
                    "code": "HGNC:8803",
                    "system": "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/",
                },
                "relation": "exactMatch",
                "extensions": [get_vicc_normalizer_priority_ext(is_priority=True)],
            },
        ],
        "extensions": [
            {
                "name": "description",
                "value": "Commonly mutated in GI tract tumors, PDGFR family genes (mutually exclusive to KIT mutations) are a hallmark of gastrointestinal stromal tumors. Gene fusions involving the PDGFRA kinase domain are highly correlated with eosinophilia, and the WHO classifies myeloid and lymphoid neoplasms with these characteristics as a distinct disorder. Mutations in the 842 region of PDGFRA have been often found to confer resistance to the tyrosine kinase inhibitor, imatinib.",
            },
            {
                "name": "aliases",
                "value": ["CD140A", "PDGFR-2", "PDGFR2", "PDGFRA"],
            },
        ],
    }


@pytest.fixture(scope="module")
def civic_did2():
    """Create test fixture for CIViC DID2."""
    return {
        "id": "civic.did:2",
        "conceptType": "Disease",
        "name": "Gastrointestinal Stromal Tumor",
        "mappings": [
            {
                "coding": {
                    "id": "DOID:9253",
                    "code": "DOID:9253",
                    "system": "https://disease-ontology.org/?id=",
                },
                "relation": "exactMatch",
                "extensions": [
                    get_civic_annotation_ext(),
                    get_vicc_normalizer_priority_ext(is_priority=False),
                ],
            },
            {
                "coding": {
                    "name": "Gastrointestinal Stromal Tumor",
                    "id": "ncit:C3868",
                    "code": "C3868",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                },
                "relation": "exactMatch",
                "extensions": [get_vicc_normalizer_priority_ext(is_priority=True)],
            },
            {
                "coding": {
                    "id": "MONDO_0011719",
                    "code": "MONDO:0011719",
                    "system": "https://purl.obolibrary.org/obo/",
                },
                "relation": "exactMatch",
                "extensions": [get_vicc_normalizer_priority_ext(is_priority=False)],
            },
        ],
    }


@pytest.fixture(scope="module")
def civic_eid2_study_stmt(civic_method, civic_mpid99, civic_gid38, civic_did2):
    """Create a test fixture for CIViC EID2 study statement."""
    return {
        "id": "civic.eid:2",
        "description": "GIST tumors harboring PDGFRA D842V mutation are more likely to be benign than malignant.",
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
            "type": "VariantDiagnosticProposition",
            "predicate": "isDiagnosticExclusionCriterionFor",
            "alleleOriginQualifier": {"name": "somatic"},
            "subjectVariant": civic_mpid99,
            "geneContextQualifier": civic_gid38,
            "objectCondition": civic_did2,
        },
        "specifiedBy": civic_method,
        "reportedIn": [
            {
                "id": "civic.source:52",
                "name": "Lasota et al., 2004",
                "title": "A great majority of GISTs with PDGFRA mutations represent gastric tumors of low or no malignant potential.",
                "pmid": 15146165,
                "type": "Document",
            }
        ],
        "type": "Statement",
    }


@pytest.fixture(scope="module")
def civic_mpid113():
    """Create a test fixture for CIViC MP 113."""
    return {
        "id": "civic.mpid:113",
        "type": "CategoricalVariant",
        "description": "RET M819T is the most common somatically acquired mutation in medullary thyroid cancer (MTC). While there currently are no RET-specific inhibiting agents, promiscuous kinase inhibitors have seen some success in treating RET overactivity. Data suggests however, that the M918T mutation may lead to drug resistance, especially against the VEGFR-inhibitor motesanib. It has also been suggested that RET M819T leads to more aggressive MTC with a poorer prognosis.",
        "name": "RET M918T",
        "constraints": [
            {
                "allele": {
                    "id": "ga4gh:VA.hEybNB_CeKflfFhT5AKOU5i1lgZPP-aS",
                    "type": "Allele",
                    "name": "M918T",
                    "digest": "hEybNB_CeKflfFhT5AKOU5i1lgZPP-aS",
                    "expressions": [
                        {"syntax": "hgvs.p", "value": "NP_065681.1:p.Met918Thr"},
                        {"syntax": "hgvs.c", "value": "NM_020975.4:c.2753T>C"},
                        {"syntax": "hgvs.c", "value": "ENST00000355710.3:c.2753T>C"},
                        {"syntax": "hgvs.g", "value": "NC_000010.10:g.43617416T>C"},
                    ],
                    "location": {
                        "id": "ga4gh:SL.oIeqSfOEuqO7KNOPt8YUIa9vo1f6yMao",
                        "type": "SequenceLocation",
                        "digest": "oIeqSfOEuqO7KNOPt8YUIa9vo1f6yMao",
                        "sequenceReference": {
                            "type": "SequenceReference",
                            "refgetAccession": "SQ.jMu9-ItXSycQsm4hyABeW_UfSNRXRVnl",
                        },
                        "start": 917,
                        "end": 918,
                        "sequence": "M",
                    },
                    "state": {"type": "LiteralSequenceExpression", "sequence": "T"},
                },
                "type": "DefiningAlleleConstraint",
            }
        ],
        "members": [
            {
                "id": "ga4gh:VA.TZBjEPHhLRYxssQopcOQLWEBQrwzhH3T",
                "type": "Allele",
                "name": "NM_020975.4:c.2753T>C",
                "digest": "TZBjEPHhLRYxssQopcOQLWEBQrwzhH3T",
                "expressions": [{"syntax": "hgvs.c", "value": "NM_020975.4:c.2753T>C"}],
                "location": {
                    "id": "ga4gh:SL.LD_QnJ8V1MR3stLat01acwyO4fWrUGco",
                    "type": "SequenceLocation",
                    "digest": "LD_QnJ8V1MR3stLat01acwyO4fWrUGco",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.jHlgYyFWJThVNL_o5UXEBwcQVNEPc62c",
                    },
                    "start": 2942,
                    "end": 2943,
                    "sequence": "T",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "C"},
            },
            {
                "id": "ga4gh:VA.ON-Q17mJBYx3unmQ8GiqllzEphxR-Fie",
                "type": "Allele",
                "name": "NC_000010.10:g.43617416T>C",
                "digest": "ON-Q17mJBYx3unmQ8GiqllzEphxR-Fie",
                "expressions": [
                    {"syntax": "hgvs.g", "value": "NC_000010.10:g.43617416T>C"}
                ],
                "location": {
                    "id": "ga4gh:SL.wIzpygPWdaZBkoKcIg461KaERW7XfyZS",
                    "type": "SequenceLocation",
                    "digest": "wIzpygPWdaZBkoKcIg461KaERW7XfyZS",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.ss8r_wB0-b9r44TQTMmVTI92884QvBiB",
                    },
                    "start": 43121967,
                    "end": 43121968,
                    "sequence": "T",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "C"},
            },
        ],
        "mappings": [
            {
                "coding": {
                    "code": "CA009082",
                    "system": "https://reg.clinicalgenome.org/redmine/projects/registry/genboree_registry/by_canonicalid?canonicalid=",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "13919",
                    "system": "https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "rs74799832",
                    "system": "https://www.ncbi.nlm.nih.gov/snp/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "id": "civic.vid:113",
                    "code": "113",
                    "system": "https://civicdb.org/variants/",
                },
                "relation": "exactMatch",
            },
        ],
        "aliases": ["MET918THR"],
        "extensions": [
            {
                "name": "CIViC representative coordinate",
                "value": {
                    "chromosome": "10",
                    "start": 43617416,
                    "stop": 43617416,
                    "reference_bases": "T",
                    "variant_bases": "C",
                    "representative_transcript": "ENST00000355710.3",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates",
                },
            },
            {
                "name": "CIViC Molecular Profile Score",
                "value": 86.0,
            },
            {
                "name": "Variant types",
                "value": [
                    {
                        "id": "SO:0001583",
                        "code": "SO:0001583",
                        "system": "http://www.sequenceontology.org/browser/current_svn/term/",
                        "name": "missense_variant",
                    }
                ],
            },
        ],
    }


@pytest.fixture(scope="module")
def civic_gid42():
    """Create test fixture for CIViC GID42."""
    return {
        "id": "civic.gid:42",
        "conceptType": "Gene",
        "name": "RET",
        "mappings": [
            {
                "coding": {
                    "id": "ncbigene:5979",
                    "code": "5979",
                    "system": "https://www.ncbi.nlm.nih.gov/gene/",
                },
                "relation": "exactMatch",
                "extensions": [
                    get_vicc_normalizer_priority_ext(is_priority=False),
                    get_civic_annotation_ext(),
                ],
            },
            {
                "coding": {
                    "name": "RET",
                    "id": "hgnc:9967",
                    "code": "HGNC:9967",
                    "system": "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/",
                },
                "relation": "exactMatch",
                "extensions": [get_vicc_normalizer_priority_ext(is_priority=True)],
            },
        ],
        "extensions": [
            {
                "name": "description",
                "value": "RET mutations and the RET fusion RET-PTC lead to activation of this tyrosine kinase receptor and are associated with thyroid cancers. RET point mutations are the most common mutations identified in medullary thyroid cancer (MTC) with germline and somatic mutations in RET associated with hereditary and sporadic forms, respectively. The most common somatic form mutation is M918T (exon 16) and a variety of other mutations effecting exons 10, 11 and 15 have been described. The prognostic significance of these mutations have been hotly debated in the field, however, data suggests that some RET mutation may confer drug resistance. Highly selective and well-tolerated RET inhibitors, selpercatinib (LOXO-292) and pralsetinib (BLU-667), have been FDA approved recently for the treatment of RET fusion-positive non-small-cell lung cancer, RET fusion-positive thyroid cancer and RET-mutant medullary thyroid cancer.",
            },
            {
                "name": "aliases",
                "value": [
                    "CDHF12",
                    "CDHR16",
                    "HSCR1",
                    "MEN2A",
                    "MEN2B",
                    "MTC1",
                    "PTC",
                    "RET",
                    "RET-ELE1",
                ],
            },
        ],
    }


@pytest.fixture(scope="module")
def civic_did15():
    """Create test fixture for CIViC DID15."""
    return {
        "id": "civic.did:15",
        "conceptType": "Disease",
        "name": "Medullary Thyroid Carcinoma",
        "mappings": [
            {
                "coding": {
                    "id": "DOID:3973",
                    "code": "DOID:3973",
                    "system": "https://disease-ontology.org/?id=",
                },
                "relation": "exactMatch",
                "extensions": [
                    get_civic_annotation_ext(),
                    get_vicc_normalizer_priority_ext(is_priority=False),
                ],
            },
            {
                "coding": {
                    "name": "Thyroid Gland Medullary Carcinoma",
                    "id": "ncit:C3879",
                    "code": "C3879",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                },
                "relation": "exactMatch",
                "extensions": [get_vicc_normalizer_priority_ext(is_priority=True)],
            },
            {
                "coding": {
                    "id": "MONDO_0015277",
                    "code": "MONDO:0015277",
                    "system": "https://purl.obolibrary.org/obo/",
                },
                "relation": "exactMatch",
                "extensions": [get_vicc_normalizer_priority_ext(is_priority=False)],
            },
        ],
    }


@pytest.fixture(scope="module")
def civic_eid74_study_stmt(civic_method, civic_mpid113, civic_gid42, civic_did15):
    """Create a test fixture for CIViC EID74 study statement."""
    return {
        "id": "civic.eid:74",
        "description": "In patients with medullary carcinoma, the presence of RET M918T mutation is associated with increased probability of lymph node metastases.",
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
            "type": "VariantDiagnosticProposition",
            "predicate": "isDiagnosticInclusionCriterionFor",
            "alleleOriginQualifier": {"name": "somatic"},
            "subjectVariant": civic_mpid113,
            "geneContextQualifier": civic_gid42,
            "objectCondition": civic_did15,
        },
        "specifiedBy": civic_method,
        "reportedIn": [
            {
                "id": "civic.source:44",
                "name": "Elisei et al., 2008",
                "title": "Prognostic significance of somatic RET oncogene mutations in sporadic medullary thyroid cancer: a 10-year follow-up study.",
                "pmid": 18073307,
                "type": "Document",
            }
        ],
        "type": "Statement",
    }


@pytest.fixture(scope="module")
def statements(civic_eid2_study_stmt, civic_eid74_study_stmt):
    """Create test fixture for CIViC Diagnostic statements."""
    return [civic_eid2_study_stmt, civic_eid74_study_stmt]


def test_civic_cdm(data, statements, check_transformed_cdm):
    """Test that civic transformation works correctly."""
    check_transformed_cdm(data, statements, DATA_DIR / FILENAME)
