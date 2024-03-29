"""Module for pytest fixtures."""
import os

import pytest
import asyncio

from metakb.query import QueryHandler
from metakb.normalizers import VICCNormalizers
from metakb.schemas import SourceName


@pytest.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def civic_eid2997_statement():
    """Create CIVIC EID2997 Statement test fixture."""
    return {
        "id": "civic.eid:2997",
        "type": "Statement",
        "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:A",
        "proposition": "proposition:Zfp_VG0uvxwteCcJYO6_AJv1KDmJlFjs",
        "variation_origin": "somatic",
        "variation_descriptor": "civic.vid:33",
        "therapy_descriptor": "civic.tid:146",
        "disease_descriptor": "civic.did:8",
        "method": "method:1",
        "supported_by": ["pmid:23982599"]
    }


@pytest.fixture(scope="module")
def civic_eid2997_proposition():
    """Create a test fixture for EID2997 proposition."""
    return {
        "id": "proposition:Zfp_VG0uvxwteCcJYO6_AJv1KDmJlFjs",
        "type": "therapeutic_response_proposition",
        "predicate": "predicts_sensitivity_to",
        "subject": "ga4gh:VA.kgjrhgf84CEndyLjKdAO0RxN-e3pJjxA",
        "object_qualifier": "ncit:C2926",
        "object": "rxcui:1430438",
    }


@pytest.fixture(scope="module")
def civic_vid33():
    """Create a test fixture for CIViC VID33."""
    return {
        "id": "civic.vid:33",
        "type": "VariationDescriptor",
        "label": "L858R",
        "variation_id": "ga4gh:VA.kgjrhgf84CEndyLjKdAO0RxN-e3pJjxA",
        "variation": {
            "_id": "ga4gh:VA.kgjrhgf84CEndyLjKdAO0RxN-e3pJjxA",
            "location": {
                "_id": "ga4gh:VSL.Sfs_3PlVEYp9BxBsHsFfU1tvhfDq361f",
                "interval": {
                    "end": {"value": 858, "type": "Number"},
                    "start": {"value": 857, "type": "Number"},
                    "type": "SequenceInterval"
                },
                "sequence_id": "ga4gh:SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "R",
                "type": "LiteralSequenceExpression"
            },
            "type": "Allele"
        },
        "xrefs": [
            "clinvar:376280",
            "clinvar:376282",
            "clinvar:16609",
            "caid:CA126713",
            "dbsnp:121434568"
        ],
        "alternate_labels": [
            "LEU858ARG"
        ],
        "extensions": [
            {
                "name": "civic_representative_coordinate",
                "value": {
                    "chromosome": "7",
                    "start": 55259515,
                    "stop": 55259515,
                    "reference_bases": "T",
                    "variant_bases": "G",
                    "representative_transcript": "ENST00000275493.2",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates"
                },
                "type": "Extension"
            }
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs.p",
                "value": "NP_005219.2:p.Leu858Arg",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.c",
                "value": "ENST00000275493.2:c.2573T>G",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.c",
                "value": "NM_005228.4:c.2573T>G",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000007.13:g.55259515T>G",
                "type": "Expression"
            }
        ],
        "gene_context": "civic.gid:19"
    }


@pytest.fixture(scope="module")
def civic_gid19():
    """Create test fixture for CIViC GID19."""
    return {
        "id": "civic.gid:19",
        "type": "GeneDescriptor",
        "label": "EGFR",
        "description": "EGFR is widely recognized for its importance in cancer. Amplification and mutations have been shown to be driving events in many cancer types. Its role in non-small cell lung cancer, glioblastoma and basal-like breast cancers has spurred many research and drug development efforts. Tyrosine kinase inhibitors have shown efficacy in EGFR amplfied tumors, most notably gefitinib and erlotinib. Mutations in EGFR have been shown to confer resistance to these drugs, particularly the variant T790M, which has been functionally characterized as a resistance marker for both of these drugs. The later generation TKI's have seen some success in treating these resistant cases, and targeted sequencing of the EGFR locus has become a common practice in treatment of non-small cell lung cancer. Overproduction of ligands is another possible mechanism of activation of EGFR. ERBB ligands include EGF, TGF-a, AREG, EPG, BTC, HB-EGF, EPR and NRG1-4 (for detailed information please refer to the respective ligand section).",  # noqa: E501
        "gene_id": "hgnc:3236",
        "alternate_labels": [
            "EGFR",
            "ERBB",
            "ERBB1",
            "ERRP",
            "HER1",
            "NISBD2",
            "PIG61",
            "mENA"
        ],
        "xrefs": [
            "ncbigene:1956"
        ]
    }


@pytest.fixture(scope="module")
def civic_tid146():
    """Create test fixture for CIViC TID146."""
    return {
        "id": "civic.tid:146",
        "type": "TherapyDescriptor",
        "label": "Afatinib",
        "therapy_id": "rxcui:1430438",
        "alternate_labels": [
            "BIBW2992",
            "BIBW 2992",
            "(2e)-N-(4-(3-Chloro-4-Fluoroanilino)-7-(((3s)-Oxolan-3-yl)Oxy)Quinoxazolin-6-yl)-4-(Dimethylamino)But-2-Enamide"  # noqa: E501
        ],
        "xrefs": [
            "ncit:C66940"
        ],
        "extensions": [
            {
                "type": "Extension",
                "name": "regulatory_approval",
                "value": {
                    "approval_rating": "FDA",
                    "has_indications": [
                        {
                            "id": "hemonc:25316",
                            "type": "DiseaseDescriptor",
                            "label": "Non-small cell lung cancer squamous",
                            "disease_id": None
                        },
                        {
                            "id": "hemonc:642",
                            "type": "DiseaseDescriptor",
                            "label": "Non-small cell lung cancer",
                            "disease_id": "ncit:C2926"
                        }
                    ]
                }
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_did8():
    """Create test fixture for CIViC DID8."""
    return {
        "id": "civic.did:8",
        "type": "DiseaseDescriptor",
        "label": "Lung Non-small Cell Carcinoma",
        "disease_id": "ncit:C2926",
        "xrefs": [
            "DOID:3908"
        ]
    }


@pytest.fixture(scope="module")
def pmid_23982599():
    """Create test fixture for CIViC EID2997 document."""
    return {
        "id": "pmid:23982599",
        "type": "Document",
        "label": "Dungo et al., 2013, Drugs",
        "description": "Afatinib: first global approval."
    }


@pytest.fixture(scope="module")
def civic_eid1409_statement():
    """Create test fixture for CIViC Evidence 1406."""
    return {
        "id": "civic.eid:1409",
        "description": "Phase 3 randomized clinical trial comparing vemurafenib with dacarbazine in 675 patients with previously untreated, metastatic melanoma with the BRAF V600E mutation. At 6 months, overall survival was 84% (95% confidence interval [CI], 78 to 89) in the vemurafenib group and 64% (95% CI, 56 to 73) in the dacarbazine group. A relative reduction of 63% in the risk of death and of 74% in the risk of either death or disease progression was observed with vemurafenib as compared with dacarbazine (P<0.001 for both comparisons).",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:A",
        "proposition": "proposition:wsW_PurZodw_qHg1Iw8iAR1CUQte1CLA",
        "variation_origin": "somatic",
        "variation_descriptor": "civic.vid:12",
        "therapy_descriptor": "civic.tid:4",
        "disease_descriptor": "civic.did:206",
        "method": "method:1",
        "supported_by": ["pmid:21639808"],
        "type": "Statement"
    }


@pytest.fixture(scope="module")
def civic_aid6_statement():
    """Create CIViC AID 6 test fixture."""
    return {
        "id": "civic.aid:6",
        "description": "L858R is among the most common sensitizing EGFR mutations in NSCLC, and is assessed via DNA mutational analysis, including Sanger sequencing and next generation sequencing methods. Tyrosine kinase inhibitor afatinib is FDA approved as a first line systemic therapy in NSCLC with sensitizing EGFR mutation.",  # noqa: E501
        "direction": "supports",
        "evidence_level": "amp_asco_cap_2017_level:1A",
        "proposition": "proposition:Zfp_VG0uvxwteCcJYO6_AJv1KDmJlFjs",
        "variation_origin": "somatic",
        "variation_descriptor": "civic.vid:33",
        "therapy_descriptor": "civic.tid:146",
        "disease_descriptor": "civic.did:8",
        "method": "method:2",
        "supported_by": [
            "document:9WsQBGXOmTFRXBUanTaIec8Gvgg8bsMA", "civic.eid:2997",
            "civic.eid:2629", "civic.eid:982",
            "civic.eid:968", "civic.eid:883",
            "civic.eid:879"
        ],
        "type": "Statement"
    }


@pytest.fixture(scope="module")
def civic_aid6_document():
    """Create test fixture for civic aid6 document."""
    return {
        "id": "document:9WsQBGXOmTFRXBUanTaIec8Gvgg8bsMA",
        "document_id": "https://www.nccn.org/professionals/"
                       "physician_gls/default.aspx",
        "label": "NCCN Guidelines: Non-Small Cell Lung Cancer version 3.2018",
        "type": "Document"
    }


@pytest.fixture(scope="module")
def civic_eid2_statement():
    """Create a test fixture for CIViC EID2 statement."""
    return {
        "id": "civic.eid:2",
        "type": "Statement",
        "description": "GIST tumors harboring PDGFRA D842V mutation are more likely to be benign than malignant.",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:B",
        "proposition": "proposition:KVuJMXiPm-oK4vvijE9Cakvucayay3jE",
        "variation_origin": "somatic",
        "variation_descriptor": "civic.vid:99",
        "disease_descriptor": "civic.did:2",
        "method": "method:1",
        "supported_by": ["pmid:15146165"]
    }


@pytest.fixture(scope="module")
def civic_eid2_proposition():
    """Create a test fixture for CIViC EID2 proposition."""
    return {
        "id": "proposition:KVuJMXiPm-oK4vvijE9Cakvucayay3jE",
        "type": "diagnostic_proposition",
        "predicate": "is_diagnostic_exclusion_criterion_for",
        "subject": "ga4gh:VA.bjWVYvXPaPbIRAfZvE0Uw_P-i36PGkAz",
        "object_qualifier": "ncit:C3868"
    }


@pytest.fixture(scope="module")
def civic_vid99():
    """Create a test fixture for CIViC VID99."""
    return {
        "id": "civic.vid:99",
        "type": "VariationDescriptor",
        "label": "D842V",
        "variation_id": "ga4gh:VA.bjWVYvXPaPbIRAfZvE0Uw_P-i36PGkAz",
        "variation": {
            "_id": "ga4gh:VA.bjWVYvXPaPbIRAfZvE0Uw_P-i36PGkAz",
            "location": {
                "_id": "ga4gh:VSL.CvhzuX1-CV0in3YTnaq9xZGAPxmrkrFC",
                "interval": {
                    "start": {"value": 841, "type": "Number"},
                    "end": {"value": 842, "type": "Number"},
                    "type": "SequenceInterval"
                },
                "sequence_id": "ga4gh:SQ.XpQn9sZLGv_GU3uiWO7YHq9-_alGjrVX",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "V",
                "type": "LiteralSequenceExpression"
            },
            "type": "Allele"
        },
        "xrefs": [
            "clinvar:13543",
            "caid:CA123194",
            "dbsnp:121908585"
        ],
        "alternate_labels": [
            "ASP842VAL"
        ],
        "extensions": [
            {
                "name": "civic_representative_coordinate",
                "value": {
                    "chromosome": "4",
                    "start": 55152093,
                    "stop": 55152093,
                    "reference_bases": "A",
                    "variant_bases": "T",
                    "representative_transcript": "ENST00000257290.5",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates"
                },
                "type": "Extension"
            }
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs.c",
                "value": "NM_006206.4:c.2525A>T",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.p",
                "value": "NP_006197.1:p.Asp842Val",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.c",
                "value": "ENST00000257290.5:c.2525A>T",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000004.11:g.55152093A>T",
                "type": "Expression"
            }
        ],
        "gene_context": "civic.gid:38"
    }


@pytest.fixture(scope="module")
def civic_did2():
    """Create a test fixture for CIViC DID2."""
    return {
        "id": "civic.did:2",
        "type": "DiseaseDescriptor",
        "label": "Gastrointestinal Stromal Tumor",
        "disease_id": "ncit:C3868",
        "xrefs": [
            "DOID:9253"
        ]
    }


@pytest.fixture(scope="module")
def civic_gid38():
    """Create a test fixture for CIViC GID38."""
    return {
        "id": "civic.gid:38",
        "type": "GeneDescriptor",
        "label": "PDGFRA",
        "description": "Commonly mutated in GI tract tumors, PDGFR family genes (mutually exclusive to KIT mutations) are a hallmark of gastrointestinal stromal tumors. Gene fusions involving the PDGFRA kinase domain are highly correlated with eosinophilia, and the WHO classifies myeloid and lymphoid neoplasms with these characteristics as a distinct disorder. Mutations in the 842 region of PDGFRA have been often found to confer resistance to the tyrosine kinase inhibitor, imatinib.",  # noqa: E501
        "gene_id": "hgnc:8803",
        "alternate_labels": [
            "PDGFRA",
            "PDGFR2",
            "PDGFR-2",
            "CD140A"
        ],
        "xrefs": [
            "ncbigene:5156"
        ]
    }


@pytest.fixture(scope="module")
def civic_eid74_statement():
    """Create a test fixture for CIViC EID74 statement."""
    return {
        "id": "civic.eid:74",
        "description": "In patients with medullary carcinoma, the presence of RET M918T mutation is associated with increased probability of lymph node metastases.",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:B",
        "proposition": "proposition:Vyzbpg-s6mw27yJfYBFxGyQeuEJacP4l",
        "variation_origin": "somatic",
        "variation_descriptor": "civic.vid:113",
        "disease_descriptor": "civic.did:15",
        "method": "method:1",
        "supported_by": ["pmid:18073307"],
        "type": "Statement"
    }


@pytest.fixture(scope="module")
def civic_eid74_proposition():
    """Create a test fixture for CIViC EID74 proposition."""
    return {
        "id": "proposition:Vyzbpg-s6mw27yJfYBFxGyQeuEJacP4l",
        "type": "diagnostic_proposition",
        "predicate": "is_diagnostic_inclusion_criterion_for",
        "subject": "ga4gh:VA.GweduWrfxV58YnSvUBfHPGOA-KCH_iIl",
        "object_qualifier": "ncit:C3879"
    }


@pytest.fixture(scope="module")
def civic_vid113():
    """Create a test fixture for CIViC VID113."""
    return {
        "id": "civic.vid:113",
        "type": "VariationDescriptor",
        "label": "M918T",
        "variation_id": "ga4gh:VA.GweduWrfxV58YnSvUBfHPGOA-KCH_iIl",
        "variation": {
            "_id": "ga4gh:VA.GweduWrfxV58YnSvUBfHPGOA-KCH_iIl",
            "location": {
                "_id": "ga4gh:VSL.zkwClPQjjO0FqXWN46QRuiGgodhPjxqT",
                "interval": {
                    "end": {"value": 918, "type": "Number"},
                    "start": {"value": 917, "type": "Number"},
                    "type": "SequenceInterval"
                },
                "sequence_id": "ga4gh:SQ.jMu9-ItXSycQsm4hyABeW_UfSNRXRVnl",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "T",
                "type": "LiteralSequenceExpression"
            },
            "type": "Allele"
        },
        "xrefs": [
            "clinvar:13919",
            "caid:CA009082",
            "dbsnp:74799832"
        ],
        "alternate_labels": [
            "MET918THR"
        ],
        "extensions": [
            {
                "name": "civic_representative_coordinate",
                "value": {
                    "chromosome": "10",
                    "start": 43617416,
                    "stop": 43617416,
                    "reference_bases": "T",
                    "variant_bases": "C",
                    "representative_transcript": "ENST00000355710.3",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates"
                },
                "type": "Extension"
            }
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs.c",
                "value": "NM_020975.4:c.2753T>C",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.p",
                "value": "NP_065681.1:p.Met918Thr",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.c",
                "value": "ENST00000355710.3:c.2753T>C",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000010.10:g.43617416T>C",
                "type": "Expression"
            }
        ],
        "gene_context": "civic.gid:42"
    }


@pytest.fixture(scope="module")
def civic_did15():
    """Create test fixture for CIViC DID15."""
    return {
        "id": "civic.did:15",
        "type": "DiseaseDescriptor",
        "label": "Thyroid Gland Medullary Carcinoma",
        "disease_id": "ncit:C3879",
        "xrefs": [
            "DOID:3973"
        ]
    }


@pytest.fixture(scope="module")
def civic_gid42():
    """Create test fixture for CIViC GID42."""
    return {
        "id": "civic.gid:42",
        "type": "GeneDescriptor",
        "label": "RET",
        "description": "RET mutations and the RET fusion RET-PTC lead to activation of this tyrosine kinase receptor and are associated with thyroid cancers. RET point mutations are the most common mutations identified in medullary thyroid cancer (MTC) with germline and somatic mutations in RET associated with hereditary and sporadic forms, respectively. The most common somatic form mutation is M918T (exon 16) and a variety of other mutations effecting exons 10, 11 and 15 have been described. The prognostic significance of these mutations have been hotly debated in the field, however, data suggests that some RET mutation may confer drug resistence. No RET-specific agents are currently clinically available but several promiscuous kinase inhibitors that target RET, among others, have been approved for MTC treatment.",  # noqa: E501
        "gene_id": "hgnc:9967",
        "alternate_labels": [
            "RET",
            "RET-ELE1",
            "PTC",
            "MTC1",
            "MEN2B",
            "MEN2A",
            "HSCR1",
            "CDHR16",
            "CDHF12"
        ],
        "xrefs": [
            "ncbigene:5979"
        ]
    }


@pytest.fixture(scope="module")
def civic_aid9_statement():
    """Create a test fixture for CIViC AID9 statement."""
    return {
        "id": "civic.aid:9",
        "description": "ACVR1 G328V mutations occur within the kinase domain, leading to activation of downstream signaling. Exclusively seen in high-grade pediatric gliomas, supporting diagnosis of diffuse intrinsic pontine glioma.",  # noqa: E501
        "direction": "supports",
        "evidence_level": "amp_asco_cap_2017_level:2C",
        "proposition": "proposition:Pjri4dU2VaEKcdKtVkoAUJ8bHFXnW2My",
        "variation_origin": "somatic",
        "variation_descriptor": "civic.vid:1686",
        "disease_descriptor": "civic.did:2950",
        "method": "method:2",
        "supported_by": ["civic.eid:4846",
                         "civic.eid:6955"],
        "type": "Statement"
    }


@pytest.fixture(scope="module")
def civic_aid9_proposition():
    """Create a test fixture for CIViC AID9 proposition."""
    return {
        "id": "proposition:Pjri4dU2VaEKcdKtVkoAUJ8bHFXnW2My",
        "predicate": "is_diagnostic_inclusion_criterion_for",
        "subject": "ga4gh:VA.yuvNtv-SpNOzcGsKsNnnK0n026rbfp6T",
        "object_qualifier": "DOID:0080684",
        "type": "diagnostic_proposition"
    }


@pytest.fixture(scope="module")
def civic_vid1686():
    """Create a test fixture for CIViC VID1686."""
    return {
        "id": "civic.vid:1686",
        "type": "VariationDescriptor",
        "label": "G328V",
        "variation_id": "ga4gh:VA.yuvNtv-SpNOzcGsKsNnnK0n026rbfp6T",
        "variation": {
            "_id": "ga4gh:VA.yuvNtv-SpNOzcGsKsNnnK0n026rbfp6T",
            "location": {
                "_id": "ga4gh:VSL.w84KcAESJfbxvPCwCvYpQajlkdPrfS12",
                "interval": {
                    "end": {"value": 328, "type": "Number"},
                    "start": {"value": 327, "type": "Number"},
                    "type": "SequenceInterval"
                },
                "sequence_id": "ga4gh:SQ.6CnHhDq_bDCsuIBf0AzxtKq_lXYM7f0m",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "V",
                "type": "LiteralSequenceExpression"
            },
            "type": "Allele"
        },
        "xrefs": [
            "clinvar:376363",
            "caid:CA16602802",
            "dbsnp:387906589"
        ],
        "alternate_labels": [
            "GLY328VAL"
        ],
        "extensions": [
            {
                "name": "civic_representative_coordinate",
                "value": {
                    "chromosome": "2",
                    "start": 158622516,
                    "stop": 158622516,
                    "reference_bases": "C",
                    "variant_bases": "A",
                    "representative_transcript": "ENST00000434821.1",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates"
                },
                "type": "Extension"
            }
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs.c",
                "value": "NM_001105.4:c.983G>T",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.p",
                "value": "NP_001096.1:p.Gly328Val",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000002.11:g.158622516C>A",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.c",
                "value": "ENST00000434821.1:c.983G>T",
                "type": "Expression"
            }
        ],
        "gene_context": "civic.gid:154"
    }


@pytest.fixture(scope="module")
def civic_did2950():
    """Create a test fixture for CIViC DID2950."""
    return {
        "id": "civic.did:2950",
        "type": "DiseaseDescriptor",
        "label": "Diffuse Midline Glioma, H3 K27M-mutant",
        "disease_id": "DOID:0080684",
        "xrefs": [
            "DOID:0080684"
        ]
    }


@pytest.fixture(scope="module")
def civic_gid154():
    """Create a test fixture for CIViC GID154."""
    return {
        "id": "civic.gid:154",
        "type": "GeneDescriptor",
        "label": "ACVR1",
        "gene_id": "hgnc:171",
        "alternate_labels": [
            "ACVR1",
            "TSRI",
            "SKR1",
            "FOP",
            "ALK2",
            "ACVRLK2",
            "ACVR1A",
            "ACTRI"
        ],
        "xrefs": [
            "ncbigene:90"
        ]
    }


@pytest.fixture(scope="module")
def civic_eid26_statement():
    """Create a test fixture for CIViC EID26 statement."""
    return {
        "id": "civic.eid:26",
        "description": "In acute myloid leukemia patients, D816 mutation is associated with earlier relapse and poorer prognosis than wildtype KIT.",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:B",
        "proposition": "proposition:_HXqJtIo6MSmwagQUSOot4wdKE7O4DyN",
        "variation_origin": "somatic",
        "variation_descriptor": "civic.vid:65",
        "disease_descriptor": "civic.did:3",
        "method": "method:1",
        "supported_by": ["pmid:16384925"],
        "type": "Statement"
    }


@pytest.fixture(scope="module")
def civic_eid26_proposition():
    """Create a test fixture for CIViC EID26 proposition."""
    return {
        "id": "proposition:_HXqJtIo6MSmwagQUSOot4wdKE7O4DyN",
        "predicate": "is_prognostic_of_worse_outcome_for",
        "subject": "ga4gh:VA.QSLb0bR-CRIFfKIENdHhcuUZwW3IS1aP",
        "object_qualifier": "ncit:C3171",
        "type": "prognostic_proposition"
    }


@pytest.fixture(scope="module")
def civic_vid65():
    """Create a test fixture for CIViC VID65."""
    return {
        "id": "civic.vid:65",
        "type": "VariationDescriptor",
        "label": "D816V",
        "variation_id": "ga4gh:VA.QSLb0bR-CRIFfKIENdHhcuUZwW3IS1aP",
        "variation": {
            "_id": "ga4gh:VA.QSLb0bR-CRIFfKIENdHhcuUZwW3IS1aP",
            "location": {
                "_id": "ga4gh:VSL.67qWY-IcFDjFx5DttZ1-5ZMm3v_SC7jI",
                "interval": {
                    "end": {"value": 820, "type": "Number"},
                    "start": {"value": 819, "type": "Number"},
                    "type": "SequenceInterval"
                },
                "sequence_id": "ga4gh:SQ.TcMVFj5kDODDWpiy1d_1-3_gOf4BYaAB",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "V",
                "type": "LiteralSequenceExpression"
            },
            "type": "Allele"
        },
        "xrefs": [
            "clinvar:13852",
            "caid:CA123513",
            "dbsnp:121913507"
        ],
        "alternate_labels": [
            "ASP816VAL"
        ],
        "extensions": [
            {
                "name": "civic_representative_coordinate",
                "value": {
                    "chromosome": "4",
                    "start": 55599321,
                    "stop": 55599321,
                    "reference_bases": "A",
                    "variant_bases": "T",
                    "representative_transcript": "ENST00000288135.5",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates"
                },
                "type": "Extension"
            }
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs.c",
                "value": "NM_000222.2:c.2447A>T",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.p",
                "value": "NP_000213.1:p.Asp816Val",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.c",
                "value": "ENST00000288135.5:c.2447A>T",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000004.11:g.55599321A>T",
                "type": "Expression"
            }
        ],
        "gene_context": "civic.gid:29"
    }


@pytest.fixture(scope="module")
def civic_did3():
    """Create test fixture for CIViC DID3."""
    return {
        "id": "civic.did:3",
        "type": "DiseaseDescriptor",
        "label": "Acute Myeloid Leukemia",
        "disease_id": "ncit:C3171",
        "xrefs": [
            "DOID:9119"
        ]
    }


@pytest.fixture(scope="module")
def civic_gid29():
    """Create test fixture for CIViC GID29."""
    return {
        "id": "civic.gid:29",
        "type": "GeneDescriptor",
        "label": "KIT",
        "description": "c-KIT activation has been shown to have oncogenic activity in gastrointestinal stromal tumors (GISTs), melanomas, lung cancer, and other tumor types. The targeted therapeutics nilotinib and sunitinib have shown efficacy in treating KIT overactive patients, and are in late-stage trials in melanoma and GIST. KIT overactivity can be the result of many genomic events from genomic amplification to overexpression to missense mutations. Missense mutations have been shown to be key players in mediating clinical response and acquired resistance in patients being treated with these targeted therapeutics.",  # noqa: E501
        "gene_id": "hgnc:6342",
        "alternate_labels": [
            "MASTC",
            "KIT",
            "SCFR",
            "PBT",
            "CD117",
            "C-Kit"
        ],
        "xrefs": [
            "ncbigene:3815"
        ]
    }


@pytest.fixture(scope="module")
def civic_eid1756_statement():
    """Create test fixture for CIViC EID1756 statement."""
    return {
        "id": "civic.eid:1756",
        "description": "Study of 1817 PCa cases and 2026 cancer free controls to clarify the association of (MTHFR)c.677C>T (and c.1298A>C ) of pancreatic cancer risk in a population of Han Chinese in Shanghai. Results indicated a lower risk for the heterozygous CT genotype and homozygous TT genotype carriers of (MTHFR)c.677C>T which had a significantly lower risk of developing pancreatic cancer compared with the wild-type CC genotype.",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:B",
        "proposition": "proposition:cDLAt3AJPrHQPQ--JpKU4MkU528_kE-a",
        "variation_origin": "germline",
        "variation_descriptor": "civic.vid:258",
        "disease_descriptor": "civic.did:556",
        "method": "method:1",
        "supported_by": ["pmid:27819322"],
        "type": "Statement"
    }


@pytest.fixture(scope="module")
def civic_eid1756_proposition():
    """Create a test fixture for CIViC EID1756 proposition."""
    return {
        "id": "proposition:cDLAt3AJPrHQPQ--JpKU4MkU528_kE-a",
        "predicate": "is_prognostic_of_better_outcome_for",
        "subject": "ga4gh:VA.Nq7ozfH2X6m1PGr_n38E-F0NZ7I9UASP",
        "object_qualifier": "ncit:C9005",
        "type": "prognostic_proposition"
    }


@pytest.fixture(scope="module")
def civic_vid258():
    """Create a test fixture for CIViC VID258."""
    return {
        "id": "civic.vid:258",
        "type": "VariationDescriptor",
        "label": "A222V",
        "variation_id": "ga4gh:VA.Nq7ozfH2X6m1PGr_n38E-F0NZ7I9UASP",
        "variation": {
            "_id": "ga4gh:VA.Nq7ozfH2X6m1PGr_n38E-F0NZ7I9UASP",
            "location": {
                "_id": "ga4gh:VSL._zGTVJ2unM-BjeDKxGl0IKZtKWQdfOxw",
                "interval": {
                    "end": {"value": 222, "type": "Number"},
                    "start": {"value": 221, "type": "Number"},
                    "type": "SequenceInterval"
                },
                "sequence_id": "ga4gh:SQ.4RSETawLfMkNpQBPepa7Uf9ItHAEJUde",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "V",
                "type": "LiteralSequenceExpression"
            },
            "type": "Allele"
        },
        "xrefs": [
            "clinvar:3520",
            "caid:CA170990",
            "dbsnp:1801133"
        ],
        "alternate_labels": [
            "C677T",
            "ALA222VAL"
        ],
        "extensions": [
            {
                "name": "civic_representative_coordinate",
                "value": {
                    "chromosome": "1",
                    "start": 11856378,
                    "stop": 11856378,
                    "reference_bases": "G",
                    "variant_bases": "A",
                    "representative_transcript": "ENST00000376592.1",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates"
                },
                "type": "Extension"
            }
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs.c",
                "value": "NM_005957.4:c.665C>T",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.p",
                "value": "NP_005948.3:p.Ala222Val",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.c",
                "value": "ENST00000376592.1:c.665G>A",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000001.10:g.11856378G>A",
                "type": "Expression"
            }
        ],
        "gene_context": "civic.gid:3672"
    }


@pytest.fixture(scope="module")
def civic_did556():
    """Create a test fixture for CIViC DID556."""
    return {
        "id": "civic.did:556",
        "type": "DiseaseDescriptor",
        "label": "Pancreatic Cancer",
        "disease_id": "ncit:C9005",
        "xrefs": [
            "DOID:1793"
        ]
    }


@pytest.fixture(scope="module")
def civic_gid3672():
    """Create test fixture for CIViC GID3672."""
    return {
        "id": "civic.gid:3672",
        "type": "GeneDescriptor",
        "label": "MTHFR",
        "gene_id": "hgnc:7436",
        "alternate_labels": [
            "MTHFR"
        ],
        "xrefs": [
            "ncbigene:4524"
        ]
    }


@pytest.fixture(scope="module")
def pmid_15146165():
    """Create a test fixture for PMID 15146165."""
    return {
        "id": "pmid:15146165",
        "label": "Lasota et al., 2004, Lab. Invest.",
        "type": "Document",
        "description": "A great majority of GISTs with PDGFRA mutations represent gastric tumors of low or no malignant potential."  # noqa: E501
    }


@pytest.fixture(scope="module")
def pmid_18073307():
    """Create a test fixture for PMID 18073307."""
    return {
        "type": "Document",
        "id": "pmid:18073307",
        "label": "Elisei et al., 2008, J. Clin. Endocrinol. Metab.",
        "description": "Prognostic significance of somatic RET oncogene mutations in sporadic medullary thyroid cancer: a 10-year follow-up study."  # noqa: E501
    }


@pytest.fixture(scope="module")
def pmid_16384925():
    """Create a test fixture for PMID 16384925."""
    return {
        "id": "pmid:16384925",
        "label": "Cairoli et al., 2006, Blood",
        "description": "Prognostic impact of c-KIT mutations in core binding factor leukemias: an Italian retrospective study.",  # noqa: E501
        "type": "Document"
    }


@pytest.fixture(scope="module")
def pmid_27819322():
    """Create a test fixture for PMID 27819322."""
    return {
        "type": "Document",
        "id": "pmid:27819322",
        "label": "Wu et al., 2016, Sci Rep",
        "description": "MTHFR c.677C>T Inhibits Cell Proliferation and Decreases Prostate Cancer Susceptibility in the Han Chinese Population in Shanghai.",  # noqa: E501
        "xrefs": ["pmc:PMC5098242"]
    }


@pytest.fixture(scope="module")
def moa_aid71_statement():
    """Create a MOA Statement 71 test fixture."""
    return {
        "id": "moa.assertion:71",
        "description": "T315I mutant ABL1 in p210 BCR-ABL cells resulted in retained high levels of phosphotyrosine at increasing concentrations of inhibitor STI-571, whereas wildtype appropriately received inhibition.",  # noqa: E501
        "evidence_level": "moa.evidence_level:Preclinical",
        "proposition": "proposition:4BRAy5ckYBfbzLHr95Xz3M9D9mJpTRxr",
        "variation_origin": "somatic",
        "variation_descriptor": "moa.variant:71",
        "therapy_descriptor": "moa.normalize.therapy:Imatinib",
        "disease_descriptor": "moa.normalize.disease:oncotree%3ACML",
        "method": "method:4",
        "supported_by": [
            "pmid:11423618"
        ],
        "type": "Statement"
    }


@pytest.fixture(scope="module")
def moa_aid71_proposition():
    """Create a test fixture for MOA AID71 proposition."""
    return {
        "id": "proposition:4BRAy5ckYBfbzLHr95Xz3M9D9mJpTRxr",
        "predicate": "predicts_resistance_to",
        "subject": "ga4gh:VA.M3CbaYfwomLqvJbdK4w-W7V-zw7LdjGj",
        "object_qualifier": "ncit:C3174",
        "object": "rxcui:282388",
        "type": "therapeutic_response_proposition"
    }


@pytest.fixture(scope="module")
def moa_vid71():
    """Create a test fixture for MOA VID71."""
    return {
        "id": "moa.variant:71",
        "type": "VariationDescriptor",
        "label": "ABL1 p.T315I (Missense)",
        "variation_id": "ga4gh:VA.M3CbaYfwomLqvJbdK4w-W7V-zw7LdjGj",
        "variation": {
            "_id": "ga4gh:VA.M3CbaYfwomLqvJbdK4w-W7V-zw7LdjGj",
            "location": {
                "_id": "ga4gh:VSL.JkBiKTd3Kq-l0ZSOzCOJ1i60mh03hXb5",
                "interval": {
                    "end": {"value": 315, "type": "Number"},
                    "start": {"value": 314, "type": "Number"},
                    "type": "SequenceInterval"
                },
                "sequence_id": "ga4gh:SQ.dmFigTG-0fY6I54swb7PoDuxCeT6O3Wg",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "I",
                "type": "LiteralSequenceExpression"
            },
            "type": "Allele"
        },
        "extensions": [
            {
                "name": "moa_representative_coordinate",
                "value": {
                    "chromosome": "9",
                    "start_position": "133747580",
                    "end_position": "133747580",
                    "reference_allele": "C",
                    "alternate_allele": "T",
                    "cdna_change": "c.944C>T",
                    "protein_change": "p.T315I",
                    "exon": "5"
                },
                "type": "Extension"
            }
        ],
        "vrs_ref_allele_seq": "T",
        "gene_context": "moa.normalize.gene:ABL1"
    }


@pytest.fixture(scope="module")
def moa_abl1():
    """Create a test fixture for MOA ABL1 Gene Descriptor."""
    return {
        "id": "moa.normalize.gene:ABL1",
        "type": "GeneDescriptor",
        "label": "ABL1",
        "gene_id": "hgnc:76"
    }


@pytest.fixture(scope="module")
def moa_imatinib():
    """Create a test fixture for MOA Imatinib Therapy Descriptor."""
    return {
        "id": "moa.normalize.therapy:Imatinib",
        "type": "TherapyDescriptor",
        "label": "Imatinib",
        "therapy_id": "rxcui:282388",
        "extensions": [{
            "type": "Extension",
            "name": "regulatory_approval",
            "value": {
                "approval_rating": "FDA",
                "has_indications": [
                    {
                        "id": "hemonc:634",
                        "type": "DiseaseDescriptor",
                        "label": "Myelodysplastic syndrome",
                        "disease_id": "ncit:C3247"
                    },
                    {
                        "id": "hemonc:616",
                        "type": "DiseaseDescriptor",
                        "label": "Hypereosinophilic syndrome",
                        "disease_id": "ncit:C27038"
                    },
                    {
                        "id": "hemonc:582",
                        "type": "DiseaseDescriptor",
                        "label": "Chronic myelogenous leukemia",
                        "disease_id": "ncit:C3174"
                    },
                    {
                        "id": "hemonc:669",
                        "type": "DiseaseDescriptor",
                        "label": "Systemic mastocytosis",
                        "disease_id": "ncit:C9235"
                    },
                    {
                        "id": "hemonc:24309",
                        "type": "DiseaseDescriptor",
                        "label": "Acute lymphoblastic leukemia",
                        "disease_id": "ncit:C3167"
                    },
                    {
                        "id": "hemonc:667",
                        "type": "DiseaseDescriptor",
                        "label": "Soft tissue sarcoma",
                        "disease_id": "ncit:C9306"
                    },
                    {
                        "id": "hemonc:602",
                        "type": "DiseaseDescriptor",
                        "label": "Gastrointestinal stromal tumor",
                        "disease_id": "ncit:C3868"
                    },
                    {
                        "id": "hemonc:33893",
                        "type": "DiseaseDescriptor",
                        "label": "Chronic myelogenous leukemia pediatric",
                        "disease_id": None
                    }
                ]
            }
        }]
    }


@pytest.fixture(scope="module")
def moa_chronic_myelogenous_leukemia():
    """Create test fixture for MOA Chronic Myelogenous Leukemia Descriptor."""
    return {
        "id": "moa.normalize.disease:oncotree%3ACML",
        "type": "DiseaseDescriptor",
        "label": "Chronic Myelogenous Leukemia",
        "disease_id": "ncit:C3174"
    }


@pytest.fixture(scope="module")
def method1():
    """Create test fixture for method:1."""
    return {
        "id": "method:1",
        "label": "Standard operating procedure for curation and clinical interpretation of variants in cancer",  # noqa: E501
        "url": "https://genomemedicine.biomedcentral.com/articles/10.1186/s13073-019-0687-x",  # noqa: E501
        "version": {
            "year": 2019,
            "month": 11,
            "day": 29
        },
        "authors": "Danos, A.M., Krysiak, K., Barnell, E.K. et al.",
        "type": "Method"
    }


@pytest.fixture(scope="module")
def method2():
    """Create test fixture for method:2."""
    return {
        "id": "method:2",
        "type": "Method",
        "label": "Standards and Guidelines for the Interpretation and Reporting of Sequence Variants in Cancer: A Joint Consensus Recommendation of the Association for Molecular Pathology, American Society of Clinical Oncology, and College of American Pathologists",  # noqa: E501
        "url": "https://pubmed.ncbi.nlm.nih.gov/27993330/",
        "version": {
            "year": 2017,
            "month": 1
        },
        "authors": "Li MM, Datto M, Duncavage EJ, et al."
    }


@pytest.fixture(scope="module")
def method3():
    """Create test fixture for method:3."""
    return {
        "id": "method:3",
        "label": "Standards and guidelines for the interpretation of sequence variants: a joint consensus recommendation of the American College of Medical Genetics and Genomics and the Association for Molecular Pathology",  # noqa: E501
        "url": "https://pubmed.ncbi.nlm.nih.gov/25741868/",
        "version": {
            "year": 2015,
            "month": 5
        },
        "type": "Method",
        "authors": "Richards S, Aziz N, Bale S, et al."
    }


@pytest.fixture(scope="module")
def method4():
    """Create a test fixture for MOA method:4."""
    return {
        "id": "method:4",
        "label": "Clinical interpretation of integrative molecular profiles to guide precision cancer medicine",  # noqa: E501
        "url": "https://www.biorxiv.org/content/10.1101/2020.09.22.308833v1",
        "type": "Method",
        "version": {
            "year": 2020,
            "month": 9,
            "day": 22
        },
        "authors": "Reardon, B., Moore, N.D., Moore, N. et al."
    }


@pytest.fixture(scope="module")
def civic_methods(method1, method2, method3):
    """Create test fixture for methods."""
    return [method1, method2, method3]


@pytest.fixture(scope="module")
def pmid_11423618():
    """Create a test fixture for PMID 11423618."""
    return {
        "id": "pmid:11423618",
        "label": "Gorre, Mercedes E., et al. \"Clinical resistance to STI-571 cancer therapy caused by BCR-ABL gene mutation or amplification.\" Science 293.5531 (2001): 876-880.",  # noqa: E501
        "xrefs": [
            "doi:10.1126/science.1062538"
        ],
        "type": "Document"
    }


@pytest.fixture(scope="session")
def oncokb_diagnostic_statement1():
    """Create test fixture for OncoKB BRAF V600E diagnostic evidence"""
    return {
        "id": "oncokb.evidence:1Aj9eQzlxTuA5SU4pawmBSLhB1Z-XN88",
        "type": "Statement",
        "evidence_level": "oncokb.evidence_level:LEVEL_Dx3",
        "proposition": "proposition:aLUHxB-FSxQp8hvWKw0JWTdmVZUgkF2f",
        "variation_descriptor": "oncokb.variant:BRAF%20V600E",
        "disease_descriptor": "oncokb.disease:611",
        "method": "method:5",
        "supported_by": ["pmid:25422482", "pmid:26637772"]
    }


@pytest.fixture(scope="session")
def oncokb_diagnostic_proposition1():
    """Create test fixture for OncoKB BRAF V600E diagnostic proposition"""
    return {
        "id": "proposition:aLUHxB-FSxQp8hvWKw0JWTdmVZUgkF2f",
        "type": "diagnostic_proposition",
        "predicate": "is_diagnostic_inclusion_criterion_for",
        "subject": "ga4gh:VA.ZDdoQdURgO2Daj2NxLj4pcDnjiiAsfbO",
        "object_qualifier": "ncit:C53972"
    }


@pytest.fixture(scope="session")
def oncokb_therapeutic_statement1():
    """Create test fixture for OncoKB BRAF V600E therapeutic evidence"""
    return {
        "id": "oncokb.evidence:xKWfpPS0aNLElHg9v3mwmb9WMaT8P1pf",
        "description": "Trametinib is an oral small molecule inhibitor of MEK1/2 that is FDA-approved alone or with dabrafenib for the treatment of patients with metastatic melanoma harboring a V600E or V600K BRAF mutation. In an open-label, randomized Phase III trial, patients with BRAF V600E/K-mutated unresectable, metastatic melanoma received oral trametinib (2 mg once daily) or an intravenous regimen of either dacarbazine (1000 mg/m2) or paclitaxel (175 mg/m2) every three weeks. Trametinib demonstrated improved progression-free survival (HR for disease progression or death = 0.45) and six-month overall survival (81% vs. 67%; death HR = 0.54; p=0.01) (PMID: 22663011). However, like other MEK inhibitors, the benefit of trametinib is limited by adverse reactions, most notably grade three or four rash and diarrhea (PMID: 22663011). Trametinib is not typically used as monotherapy for patients with BRAF V600K melanoma given its lower response rate compared to BRAF inhibitors and combined BRAF and MEK inhibitors. Patients previously treated with a RAF inhibitor appear to be less likely than untreated patients to respond to trametinib treatment (PMID: 22663011), and FDA guidelines state that trametinib as a monotherapy is not indicated for these patients. Dabrafenib and trametinib are FDA-approved as a combination therapy, which has superior clinical outcomes compared to dabrafenib or trametinib monotherapy (PMID: 25399551, 25265492). Additionally, patients with melanoma treated with dabrafenib and trametinib in both the neoadjuvant and adjuvant settings had improved survival over patients given standard of care (PMID: 29361468).",  # noqa: E501
        "type": "Statement",
        "evidence_level": "oncokb.evidence_level:LEVEL_1",
        "proposition": "proposition:EOEfYXjsyQmgV2sNA-gfK5i0Cj8WGGuw",
        "variation_descriptor": "oncokb.variant:BRAF%20V600E",
        "disease_descriptor": "oncokb.disease:453",
        "therapy_descriptor": "oncokb.normalize.therapy:Trametinib",
        "method": "method:5",
        "supported_by": ["pmid:29361468", "pmid:25399551", "pmid:22663011",
                         "pmid:25265492"],
        "extensions": [
            {
                "type": "Extension",
                "name": "onckb_fda_level",
                "value": {
                    "level": "LEVEL_Fda2",
                    "description": "Cancer Mutations with Evidence of Clinical Significance"  # noqa: E501
                }
            }
        ]
    }


@pytest.fixture(scope="session")
def oncokb_therapeutic_proposition1():
    """Create test fixture for OncoKB BRAF V600E therapeutic proposition"""
    return {
        "id": "proposition:EOEfYXjsyQmgV2sNA-gfK5i0Cj8WGGuw",
        "type": "therapeutic_response_proposition",
        "predicate": "predicts_sensitivity_to",
        "subject": "ga4gh:VA.ZDdoQdURgO2Daj2NxLj4pcDnjiiAsfbO",
        "object_qualifier": "ncit:C3224",
        "object": "rxcui:1425098"
    }


@pytest.fixture(scope="session")
def oncokb_braf_v600e_vd():
    """Create test fixture for BRAF V600E Variation Descriptor"""
    return {
        "type": "VariationDescriptor",
        "id": "oncokb.variant:BRAF%20V600E",
        "label": "BRAF V600E",
        "description": "The BRAF V600E mutation is known to be oncogenic.",
        "variation_id": "ga4gh:VA.ZDdoQdURgO2Daj2NxLj4pcDnjiiAsfbO",
        "variation": {
            "_id": "ga4gh:VA.ZDdoQdURgO2Daj2NxLj4pcDnjiiAsfbO",
            "location": {
                "_id": "ga4gh:VSL.2cHIgn7iLKk4x9z3zLkSTTFMV0e48DR4",
                "interval": {
                    "end": {"value": 600, "type": "Number"},
                    "start": {"value": 599, "type": "Number"},
                    "type": "SequenceInterval"
                },
                "sequence_id": "ga4gh:SQ.cQvw4UsHHRRlogxbWCB8W-mKD4AraM9y",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "E",
                "type": "LiteralSequenceExpression"
            },
            "type": "Allele"
        },
        "gene_context": "oncokb.normalize.gene:BRAF",
        "extensions": [
            {
                "type": "Extension",
                "name": "oncogenic",
                "value": "Oncogenic"
            },
            {
                "type": "Extension",
                "name": "mutation_effect",
                "value": {
                    "knownEffect": "Gain-of-function",
                    "description": "The class I activating exon 15 BRAF V600E mutation is located in the kinase domain of the BRAF protein and is highly recurrent in melanoma, lung and thyroid cancer, among others (PMID: 28783719, 26091043, 25079552, 23833300, 25417114, 28783719, 12068308). This mutation has been comprehensively biologically characterized and has been shown to activate the downstream MAPK pathway independent of RAS (PMID: 15035987, 12068308, 19251651, 26343582), to render BRAF constitutively activated in monomeric form (PMID: 20179705), and to retain sensitivity to RAF monomer inhibitors such as vemurafenib and dabrafenib (PMID:26343582, 28783719, 20179705, 30351999).",  # noqa: E501
                    "citations": {
                        "pmids": [
                            "25417114",
                            "20179705",
                            "23833300",
                            "26091043",
                            "26343582",
                            "12068308",
                            "30351999",
                            "25079552",
                            "28783719",
                            "19251651",
                            "15035987"
                        ],
                        "abstracts": []
                    }
                }
            },
            {
                "type": "Extension",
                "name": "hotspot",
                "value": True
            },
            {
                "type": "Extension",
                "name": "vus",
                "value": False
            },
            {
                "type": "Extension",
                "name": "oncokb_highest_sensitive_level",
                "value": "LEVEL_1"
            },
            {
                "type": "Extension",
                "name": "oncokb_highest_diagnostic_implication_level",
                "value": "LEVEL_Dx2"
            },
            {
                "type": "Extension",
                "name": "oncokb_highest_fda_level",
                "value": "LEVEL_Fda2"
            },
            {
                "type": "Extension",
                "name": "allele_exist",
                "value": True
            }
        ]
    }


@pytest.fixture(scope="session")
def oncokb_braf_gene_descriptor():
    """Create test fixture for BRAF gene descriptor"""
    return {
        "id": "oncokb.normalize.gene:BRAF",
        "type": "GeneDescriptor",
        "label": "BRAF",
        "gene_id": "hgnc:1097",
        "description": "BRAF, an intracellular kinase, is frequently mutated in melanoma, thyroid and lung cancers among others.",  # noqa: E501
        "xrefs": ["ncbigene:673"],
        "extensions": [
            {
                "type": "Extension",
                "name": "ensembl_transcript_GRCh37",
                "value": "ENST00000288602"
            },
            {
                "type": "Extension",
                "name": "refseq_transcript_GRCh37",
                "value": "NM_004333.4"
            },
            {
                "type": "Extension",
                "name": "ensembl_transcript_GRCh38",
                "value": "ENST00000646891"
            },
            {
                "type": "Extension",
                "name": "refseq_transcript_GRCh38",
                "value": "NM_004333.4"
            },
            {
                "type": "Extension",
                "name": "oncogene",
                "value": True
            },
            {
                "type": "Extension",
                "name": "oncokb_highest_sensitive_level",
                "value": "1"
            },
            {
                "type": "Extension",
                "name": "oncokb_background",
                "value": "BRAF is a serine/threonine kinase that plays a key role in the regulation of the mitogen-activated protein kinase (MAPK) cascade (PMID: 15520807), which under physiologic conditions regulates the expression of genes involved in cellular functions, including proliferation (PMID: 24202393). Genetic alterations in BRAF are found in a large percentage of melanomas, thyroid cancers and histiocytic neoplasms as well as a small fraction of lung and colorectal cancers. The most common BRAF point mutation is V600E, which deregulates the protein's kinase activity leading to constitutive BRAF activation, as BRAF V600E can signal as a monomer independently of RAS or upstream activation (PMID: 20179705). Other BRAF mutations have been found that affect the protein's propensity to dimerize (PMID: 16858395, 26343582, 12068308). The product of these alterations is a BRAF kinase that can activate MAPK signaling in an unregulated manner and, in some instances, is directly responsible for cancer growth (PMID: 15520807). Inhibitors of mutant BRAF, including vemurafenib and dabrafenib, are FDA-approved for the treatment of late-stage or unresectable melanoma.",  # noqa: E501
            },
            {
                "type": "Extension",
                "name": "tumor_suppressor_gene",
                "value": False
            }
        ]
    }


@pytest.fixture(scope="session")
def oncokb_trametinib_therapy_descriptor():
    """Create OncoKB therapy descriptor for Trametinib"""
    return {
        "id": "oncokb.normalize.therapy:Trametinib",
        "type": "TherapyDescriptor",
        "label": "Trametinib",
        "therapy_id": "rxcui:1425098",
        "alternate_labels": [
            "JTP-74057",
            "MEK Inhibitor GSK1120212",
            "N-(3-{3-cyclopropyl-5-[(2-fluoro-4-iodophenyl)amino]-6,8-dimethyl-2,4,7-trioxo-3,4,6,7-tetrahydropyrido[4,3-d]pyrimidin-1(2H)-yl}phenyl)acetamide",  # noqa: E501
            "GSK1120212",
            "TRAMETINIB",
            "Trametinib"
        ],
        "xrefs": ["ncit:C77908"],
        "extensions": [
            {
                "type": "Extension",
                "name": "regulatory_approval",
                "value": {
                    "approval_rating": "ChEMBL",
                    "has_indications": [
                        {
                            "id": "mesh:D009369",
                            "type": "DiseaseDescriptor",
                            "label": "Neoplasms",
                            "disease_id": "ncit:C3262"
                        }
                    ]
                }
            }
        ]
    }


@pytest.fixture(scope="session")
def oncokb_ecd_disease_descriptor():
    """Create OncoKB disease descriptor for ECD"""
    return {
        "type": "DiseaseDescriptor",
        "id": "oncokb.disease:611",
        "label": "Erdheim-Chester Disease",
        "disease_id": "ncit:C53972",
        "xrefs": ["oncotree:ECD"],
        "extensions": [
            {
                "type": "Extension",
                "name": "oncotree_main_type",
                "value": {
                    "id": None,
                    "name": "Histiocytosis",
                    "tumor_form": "LIQUID"
                }
            },
            {
                "type": "Extension",
                "name": "tissue",
                "value": "Myeloid"
            },
            {
                "type": "Extension",
                "name": "parent",
                "value": "HDCN"
            },
            {
                "type": "Extension",
                "name": "level",
                "value": 4
            },
            {
                "type": "Extension",
                "name": "tumor_form",
                "value": "LIQUID"
            }
        ]
    }


@pytest.fixture(scope="session")
def oncokb_mel_disease_descriptor():
    """Create OncoKB disease descriptor for MEL"""
    return {
        "type": "DiseaseDescriptor",
        "id": "oncokb.disease:453",
        "label": "Melanoma",
        "disease_id": "ncit:C3224",
        "xrefs": ["oncotree:MEL"],
        "extensions": [
            {
                "type": "Extension",
                "name": "oncotree_main_type",
                "value": {
                    "id": None,
                    "name": "Melanoma",
                    "tumor_form": "SOLID"
                }
            },
            {
                "type": "Extension",
                "name": "tissue",
                "value": "Skin"
            },
            {
                "type": "Extension",
                "name": "parent",
                "value": "SKIN"
            },
            {
                "type": "Extension",
                "name": "level",
                "value": 2
            },
            {
                "type": "Extension",
                "name": "tumor_form",
                "value": "SOLID"
            }
        ]
    }


@pytest.fixture(scope="session")
def oncokb_diagnostic1_documents():
    """Create test fixture for OncoKB diagnostic evidence 1 documents"""
    return [
        {
            "id": "pmid:25422482",
            "label": "PubMed 25422482",
            "type": "Document"
        },
        {
            "id": "pmid:26637772",
            "label": "PubMed 26637772",
            "type": "Document"
        }
    ]


@pytest.fixture(scope="session")
def oncokb_therapeutic1_documents_query():
    """Create test fixture for OncoKB therapeutic evidence 1 documents during queries.
    Since CIViC provided more information, we now have a description
    and a more detailed label for pmid:22663011
    """
    return [
        {
            "id": "pmid:29361468",
            "label": "PubMed 29361468",
            "type": "Document"
        },
        {
            "id": "pmid:25399551",
            "label": "PubMed 25399551",
            "type": "Document"
        },
        {
            "id": "pmid:22663011",
            "label": "Flaherty et al., 2012, N. Engl. J. Med.",
            "description": "Improved survival with MEK inhibition in BRAF-mutated melanoma.",  # noqa: E501
            "type": "Document"
        },
        {
            "id": "pmid:25265492",
            "label": "PubMed 25265492",
            "type": "Document"
        }
    ]


@pytest.fixture(scope="session")
def oncokb_method():
    """Create test fixture for OncoKB method"""
    return {
        "id": "method:5",
        "label": "OncoKB Curation Standard Operating Procedure",
        "url": "https://sop.oncokb.org/",
        "version": {
            "year": 2021,
            "month": 11
        },
        "authors": "OncoKB",
        "type": "Method"
    }


@pytest.fixture(scope="session")
def sources_count() -> int:
    """Provide number of currently-implemented sources."""
    return len(SourceName.__members__)


@pytest.fixture(scope="session")
def check_statement():
    """Create a test fixture to compare statements."""
    def check_statement(actual, test):
        """Check that statements are match."""
        assert actual.keys() == test.keys()
        assert actual["id"] == test["id"]
        if "description" in test:
            assert actual["description"] == test["description"]
        else:
            assert "description" not in actual
        if "direction" in test.keys():
            # MOA doesn"t have direction?
            assert actual["direction"] == test["direction"]
        assert actual["evidence_level"] == test["evidence_level"]
        assert actual["proposition"].startswith("proposition:")
        if "variation_origin" in test:
            assert actual["variation_origin"] == test["variation_origin"]
        else:
            assert "variation_origin" not in actual
        assert actual["variation_descriptor"] == test["variation_descriptor"]
        if "therapy_descriptor" not in test.keys():
            assert "therapy_descriptor" not in actual.keys()
        else:
            assert actual["therapy_descriptor"] == test["therapy_descriptor"]
        assert actual["disease_descriptor"] == test["disease_descriptor"]
        assert actual["method"] == test["method"]
        assert set(actual["supported_by"]) == set(test["supported_by"])
        assert actual["type"] == test["type"]
    return check_statement


@pytest.fixture(scope="session")
def check_proposition():
    """Create a test fixture to compare propositions."""
    def check_proposition(actual, test):
        """Check that propositions match."""
        assert actual.keys() == test.keys()
        assert actual["id"].startswith("proposition:")
        assert actual["type"] == test["type"]
        if test["type"] == "therapeutic_response_proposition":
            assert actual["object"] == test["object"]
        else:
            assert "object" not in actual.keys()
        assert actual["predicate"] == test["predicate"]
        assert actual["subject"] == test["subject"]
        assert actual["object_qualifier"] == test["object_qualifier"]
    return check_proposition


@pytest.fixture(scope="session")
def check_variation_descriptor():
    """Create a test fixture to compare variation descriptors."""
    def check_variation_descriptor(actual, test, check_descriptor=None, nested=False):
        """Check that variation descriptors match."""
        actual_keys = actual.keys()
        test_keys = test.keys()
        assert actual_keys == test_keys
        for key in test_keys:
            if key in ["id", "type", "label", "description", "variation_id",
                       "structural_type", "vrs_ref_allele_seq"]:
                assert actual[key] == test[key]
            elif key == "gene_context":
                if nested:
                    check_descriptor(actual["gene_context"], test["gene_context"])
                else:
                    assert actual[key] == test[key]
            elif key in ["xrefs", "alternate_labels"]:
                assert set(actual[key]) == set(test[key])
            elif key == "variation":
                assert actual["variation"] == test["variation"]
            elif key == "extensions":
                assert len(actual["extensions"]) == len(test["extensions"])
                for test_extension in test["extensions"]:
                    for actual_extension in actual["extensions"]:
                        if test_extension["name"] == actual_extension["name"]:
                            if test_extension["name"] != \
                                    "civic_actionability_score":
                                assert actual_extension == test_extension
                            else:
                                try:
                                    float(actual_extension["value"])
                                except ValueError:
                                    assert False
                                else:
                                    assert True
            elif key == "expressions":
                assert len(actual["expressions"]) == len(test["expressions"])
                for expression in test["expressions"]:
                    assert expression in actual["expressions"]
    return check_variation_descriptor


@pytest.fixture(scope="session")
def check_descriptor():
    """Test fixture to compare gene, therapy, and disease descriptors."""
    def check_descriptor(actual, test):
        """Check that gene, therapy, and disease descriptors match."""
        actual_keys = actual.keys()
        test_keys = test.keys()
        assert actual_keys == test_keys
        for key in test_keys:
            if key in ["alternate_labels", "xrefs"]:
                assert set(actual[key]) == set(test[key])
            elif key == "extensions":
                assert len(actual["extensions"]) == len(test["extensions"])
                if test["type"] == "TherapyDescriptor":
                    # Therapy only has regulatory approval extension
                    assert len(actual["extensions"]) == 1
                    actual_ext = actual["extensions"][0]
                    test_ext = test["extensions"][0]
                    assert actual_ext["value"]["approval_rating"] == test_ext["value"]["approval_rating"]  # noqa: E501
                    assert len(actual_ext["value"]["has_indications"]) == len(test_ext["value"]["has_indications"])  # noqa: E501
                    for x in test_ext["value"]["has_indications"]:
                        assert x in actual_ext["value"]["has_indications"], x
                else:
                    for x in test[key]:
                        assert x in actual[key], x
            else:
                assert actual[key] == test[key]
    return check_descriptor


@pytest.fixture(scope="session")
def check_method():
    """Create a test fixture to compare methods."""
    def check_method(actual, test):
        """Check that methods match."""
        assert actual == test
    return check_method


@pytest.fixture(scope="session")
def check_document():
    """Create a test fixture to compare documents."""
    def check_document(actual, test):
        """Check that documents match."""
        actual_keys = actual.keys()
        test_keys = test.keys()
        assert actual_keys == test_keys
        for key in test_keys:
            assert key in actual_keys
            if key == "xrefs":
                assert set(actual[key]) == set(test[key])
            else:
                assert actual == test
    return check_document


@pytest.fixture(scope="session")
def check_transformed_cdm():
    """Test fixture to compare CDM transformations."""
    def check_transformed_cdm(data, statements, propositions,
                              variation_descriptors, gene_descriptors,
                              disease_descriptors, therapy_descriptors,
                              civic_methods, documents, check_statement,
                              check_proposition, check_variation_descriptor,
                              check_descriptor, check_document, check_method,
                              transformed_file):
        """Test that transform to CDM works correctly."""
        tests = (
            (data["statements"], statements, check_statement),
            (data["propositions"], propositions, check_proposition),
            (data["variation_descriptors"], variation_descriptors,
             check_variation_descriptor),
            (data["gene_descriptors"], gene_descriptors, check_descriptor),
            (data["disease_descriptors"], disease_descriptors,
             check_descriptor),
            (data["methods"], civic_methods, check_method),
            (data["documents"], documents, check_document)
        )

        if therapy_descriptors:
            tests += (data["therapy_descriptors"], therapy_descriptors,
                      check_descriptor),

        for actual_data, test_data, test_fixture in tests:
            assert len(actual_data) == len(test_data)
            for test in test_data:
                test_id = test["id"]
                checked_id = None
                for actual in actual_data:
                    actual_id = actual["id"]
                    if test_id == actual_id:
                        checked_id = actual_id
                        test_fixture(actual, test)
                assert checked_id == test_id, f"{actual_id} does not match expected"

        os.remove(transformed_file)
    return check_transformed_cdm


@pytest.fixture(scope="session")
def normalizers():
    """Provide normalizers to querying/transformation tests."""
    return VICCNormalizers()


@pytest.fixture(scope="session")
def query_handler(normalizers):
    """Create query handler test fixture"""
    return QueryHandler(normalizers=normalizers)
