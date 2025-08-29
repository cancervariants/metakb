"""Test CIViC Transformation to common data model for Therapeutic Response."""

import pytest
import pytest_asyncio
from civicpy import civic as civicpy
from tests.conftest import (
    get_vicc_normalizer_failure_ext,
)

NORMALIZABLE_FILENAME = "civic_cdm.json"
NOT_NORMALIZABLE_FILE_NAME = "civic_cdm_normalization_failure.json"


@pytest.fixture(scope="module")
def fake_evidence():
    entrez_id = 999999999999999
    evidence_item_id = 123456789
    mpid = 473

    source = civicpy.Source(
        id=123456789,
        name="PubMed: Fake name",
        title="My fake civic source",
        citation="John Doe et al., 2022",
        citation_id="123456789",
        source_type="PUBMED",
        abstract="A really great abstract",
        asco_abstract_id=None,
        author_string="John Doe",
        full_journal_title="Drugs",
        journal="Drugs",
        pmc_id=None,
        publication_date="2022-9",
        source_url="http://www.ncbi.nlm.nih.gov/pubmed/123456789",
        clinical_trials=[],
        type="source",
    )

    disease = civicpy.Disease(
        id=3433,
        name="B-lymphoblastic Leukemia/lymphoma With PAX5 P80R",
        display_name="B-lymphoblastic Leukemia/lymphoma With PAX5 P80R",
        doid=None,
        disease_url=None,
        aliases=[],
        type="disease",
    )

    therapy = civicpy.Therapy(
        id=579,
        name="FOLFOX Regimen",
        ncit_id="C11197",
        therapy_url="https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&ns=ncit&code=C11197",
        aliases=[
            "CF/5-FU/L-OHP",
            "FOLFOX",
            "Fluorouracil/Leucovorin Calcium/Oxaliplatin",
        ],
        type="therapie",
    )

    disease = civicpy.Disease(
        id=3433,
        name="B-lymphoblastic Leukemia/lymphoma With PAX5 P80R",
        display_name="B-lymphoblastic Leukemia/lymphoma With PAX5 P80R",
        doid=None,
        disease_url=None,
        aliases=[],
        type="disease",
    )

    gene = civicpy.Gene(
        type="gene",
        id=6,
        variants=[],
        name="BRCA1. This should fail normalization.",
        entrez_id=entrez_id,
        description="This is a fake gene that fails normalization.",
        source_ids=[],
        sources=[],
        aliases=["Fake alias 1", "Fake alias 2"],
    )

    variant = civicpy.GeneVariant(
        type="variant",
        subtype="gene_variant",
        id=477,
        single_variant_molecular_profile_id=mpid,
        name="P968FS",
        gene_id=gene.id,
        gene=gene,
        feature_id=gene.id,
        feature=gene,
        entrez_name="BRCA1. This should fail normalization.",
        entrez_id=entrez_id,
        allele_registry_id="CA001889",
        clinvar_entries=["91602"],
        hgvs_expressions=[
            "NM_007294.3:c.2902_2903insTC",
            "NP_009225.1:p.Pro968Leufs",
            "NC_000017.10:g.41244645_41244646insGA",
            "ENST00000471181.2:c.2902_2903insTC",
        ],
        variant_aliases=["3021INSTC", "PRO968LEUFS", "RS398122670"],
        coordinates={
            "ensembl_version": 75,
            "reference_build": "GRCh37",
            "reference_bases": None,
            "variant_bases": "GA",
            "representative_transcript": "ENST00000471181.2",
            "chromosome": "17",
            "start": 41244645,
            "stop": 41244646,
            "representative_transcript2": None,
            "chromosome2": None,
            "start2": None,
            "stop2": None,
            "type": "coordinates",
        },
        variant_types=[
            {
                "id": 134,
                "name": "Frameshift Truncation",
                "so_id": "SO:0001910",
                "description": "A frameshift variant that causes the translational reading frame to be shortened relative to the reference feature.",
                "url": "http://www.sequenceontology.org/browser/current_svn/term/SO:0001910",
                "type": "variant_type",
            }
        ],
        variant_groups=[],
    )

    mp = civicpy.MolecularProfile(
        type="molecular_profile",
        id=mpid,
        variant_ids=[variant.id],
        variants=[variant],
        name="BRCA1 P968FS",
        molecular_profile_score=20.0,
        description=None,
        sources=[],
        source_ids=[],
        assertions=[],
        evidence_items=[evidence_item_id],
        aliases=["3021INSTC", "PRO968LEUFS", "RS398122670"],
        parsed_name=[],
    )

    return civicpy.Evidence(
        type="evidence",
        id=evidence_item_id,
        variant_origin="SOMATIC",
        therapy_interaction_type=None,
        status="accepted",
        significance="SENSITIVITYRESPONSE",
        rating=5,
        name="EID123456789",
        molecular_profile_id=mp.id,
        molecular_profile=mp,
        evidence_type="PREDICTIVE",
        evidence_level="A",
        evidence_direction="SUPPORTS",
        description="This is a fake evidence item.",
        assertion_ids=[],
        therapy_ids=[therapy.id],
        therapies=[therapy],
        source_id=source.id,
        source=source,
        phenotype_ids=[],
        phenotypes=[],
        disease_id=disease.id,
        disease=disease,
        assertions=[],
    )


@pytest_asyncio.fixture
async def data(civic_cdm_data):
    """Create a CIViC Transformer test fixture."""
    eid_2997 = civicpy.get_evidence_by_id(2997)
    eids = [816, 9851]
    evidence_items = [civicpy.get_evidence_by_id(eid) for eid in eids] + [eid_2997]

    # We only care about testing one evidence item
    assertion = civicpy.get_assertion_by_id(6)
    assertion.evidence_items = [eid_2997]
    assertion.evidence_ids = [2997]
    assertions = [assertion]

    return await civic_cdm_data(evidence_items, assertions, NORMALIZABLE_FILENAME)


@pytest_asyncio.fixture
async def not_normalizable_data(civic_cdm_data, fake_evidence):
    """Create a CIViC Transformer test fixture."""
    return await civic_cdm_data([fake_evidence], [], NOT_NORMALIZABLE_FILE_NAME)


@pytest.fixture(scope="module")
def statements(
    civic_eid2997_study_stmt,
    civic_eid816_study_stmt,
    civic_eid9851_study_stmt,
    civic_aid6_statement,
):
    """Create test fixture for CIViC therapeutic statements."""
    return [
        civic_eid2997_study_stmt,
        civic_eid816_study_stmt,
        civic_eid9851_study_stmt,
        civic_aid6_statement,
    ]


@pytest.fixture(scope="module")
def civic_tid579():
    """Create test fixture for CIViC therapy ID 579"""
    return {
        "id": "civic.tid:579",
        "conceptType": "Therapy",
        "name": "FOLFOX Regimen",
        "mappings": [
            {
                "coding": {
                    "id": "ncit:C11197",
                    "code": "C11197",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                },
                "relation": "exactMatch",
            },
        ],
        "extensions": [
            get_vicc_normalizer_failure_ext(),
            {
                "name": "aliases",
                "value": [
                    "CF/5-FU/L-OHP",
                    "FOLFOX",
                    "Fluorouracil/Leucovorin Calcium/Oxaliplatin",
                ],
            },
        ],
    }


@pytest.fixture(scope="module")
def civic_did3433():
    """Create test fixture for CIViC DID3433."""
    return {
        "id": "civic.did:3433",
        "conceptType": "Disease",
        "name": "B-lymphoblastic Leukemia/lymphoma With PAX5 P80R",
        "extensions": [
            get_vicc_normalizer_failure_ext(),
        ],
    }


@pytest.fixture(scope="session")
def civic_gid6_modified():
    """Create test fixture for CIViC GID6, which has been modified to fail normalization."""
    return {
        "id": "civic.gid:6",
        "conceptType": "Gene",
        "name": "BRCA1. This should fail normalization.",
        "mappings": [
            {
                "coding": {
                    "id": "ncbigene:999999999999999",
                    "code": "999999999999999",
                    "system": "https://www.ncbi.nlm.nih.gov/gene/",
                },
                "relation": "exactMatch",
            },
        ],
        "extensions": [
            get_vicc_normalizer_failure_ext(),
            {
                "name": "description",
                "value": "This is a fake gene that fails normalization.",
            },
            {
                "name": "aliases",
                "value": ["Fake alias 1", "Fake alias 2"],
            },
        ],
    }


@pytest.fixture(scope="module")
def civic_mpid473():
    """Create CIViC MPID 473"""
    return {
        "id": "civic.mpid:473",
        "type": "CategoricalVariant",
        "name": "BRCA1 P968FS",
        "mappings": [
            {
                "coding": {
                    "code": "CA001889",
                    "system": "https://reg.clinicalgenome.org/redmine/projects/registry/genboree_registry/by_canonicalid?canonicalid=",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "91602",
                    "system": "https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "rs398122670",
                    "system": "https://www.ncbi.nlm.nih.gov/snp/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "id": "civic.vid:477",
                    "code": "477",
                    "system": "https://civicdb.org/links/variant/",
                    "extensions": [
                        {"name": "subtype", "value": "gene_variant"},
                        {
                            "name": "variant_types",
                            "value": [
                                {
                                    "coding": {
                                        "id": "civic.variant_type:134",
                                        "name": "Frameshift Truncation",
                                        "system": "http://www.sequenceontology.org/browser/current_svn/term/",
                                        "code": "SO:0001910",
                                    },
                                    "relation": "exactMatch",
                                }
                            ],
                        },
                    ],
                    "name": "P968FS",
                },
                "relation": "exactMatch",
            },
            {
                "coding": {
                    "id": "civic.mpid:473",
                    "system": "https://civicdb.org/links/molecular_profile/",
                    "code": "473",
                },
                "relation": "exactMatch",
            },
        ],
        "aliases": [
            "3021INSTC",
            "PRO968LEUFS",
        ],
        "extensions": [
            get_vicc_normalizer_failure_ext(),
            {
                "name": "CIViC representative coordinate",
                "value": {
                    "chromosome": "17",
                    "start": 41244645,
                    "stop": 41244646,
                    "reference_bases": None,
                    "variant_bases": "GA",
                    "representative_transcript": "ENST00000471181.2",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates",
                },
            },
            {
                "name": "CIViC Molecular Profile Score",
                "value": 20.0,
            },
            {
                "name": "expressions",
                "value": [
                    {"syntax": "hgvs.c", "value": "NM_007294.3:c.2902_2903insTC"},
                    {"syntax": "hgvs.p", "value": "NP_009225.1:p.Pro968Leufs"},
                    {
                        "syntax": "hgvs.g",
                        "value": "NC_000017.10:g.41244645_41244646insGA",
                    },
                    {"syntax": "hgvs.c", "value": "ENST00000471181.2:c.2902_2903insTC"},
                ],
            },
        ],
    }


@pytest.fixture(scope="session")
def civic_source123456789():
    """Create fixture for a fake civic source 123456789"""
    return {
        "id": "civic.sid:123456789",
        "name": "John Doe et al., 2022",
        "title": "My fake civic source",
        "pmid": "123456789",
        "type": "Document",
        "urls": [
            "https://civicdb.org/links/source/123456789",
            "http://www.ncbi.nlm.nih.gov/pubmed/123456789",
        ],
    }


@pytest.fixture(scope="module")
def civic_not_normalizable_stmt(
    civic_tid579,
    civic_did3433,
    civic_gid6_modified,
    civic_mpid473,
    civic_method,
    civic_source123456789,
):
    """Create test fixture for fake civic statement that fails to normalize gene,
    variant, disease, and therapy.
    """
    return {
        "id": "civic.eid:123456789",
        "type": "Statement",
        "description": "This is a fake evidence item.",
        "direction": "supports",
        "strength": {
            "name": "Validated association",
            "primaryCoding": {
                "system": "https://civic.readthedocs.io/en/latest/model/evidence/level.html",
                "code": "A",
            },
            "mappings": [
                {
                    "coding": {
                        "system": "https://go.osu.edu/evidence-codes",
                        "code": "e000001",
                        "name": "authoritative evidence",
                    },
                    "relation": "exactMatch",
                }
            ],
        },
        "proposition": {
            "type": "VariantTherapeuticResponseProposition",
            "predicate": "predictsSensitivityTo",
            "objectTherapeutic": civic_tid579,
            "conditionQualifier": civic_did3433,
            "alleleOriginQualifier": {
                "name": "somatic",
                "extensions": [{"name": "civic_variant_origin", "value": "SOMATIC"}],
            },
            "geneContextQualifier": civic_gid6_modified,
            "subjectVariant": civic_mpid473,
        },
        "specifiedBy": civic_method,
        "reportedIn": [
            civic_source123456789,
            "https://civicdb.org/links/evidence/123456789",
        ],
    }


def test_civic_cdm(data, statements, check_transformed_cdm, tmp_path):
    """Test that civic transformation works correctly."""
    check_transformed_cdm(data, statements, tmp_path / NORMALIZABLE_FILENAME)


def test_civic_cdm_not_normalizable(
    not_normalizable_data, civic_not_normalizable_stmt, check_transformed_cdm, tmp_path
):
    """Test that civic transformation works correctly for CIViC records that cannot
    normalize (gene, disease, variant, and therapy)
    """
    check_transformed_cdm(
        not_normalizable_data,
        [civic_not_normalizable_stmt],
        tmp_path / NOT_NORMALIZABLE_FILE_NAME,
    )
