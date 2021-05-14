"""Module for pytest fixtures."""
import pytest
import os


@pytest.fixture(scope='module')
def civic_eid2997_statement():
    """Create CIVIC EID2997 Statement test fixture."""
    return {
        "id": "civic:eid2997",
        "type": "Statement",
        "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:A",
        "proposition": "proposition:001",
        "variation_origin": "somatic",
        "variation_descriptor": "civic:vid33",
        "therapy_descriptor": "civic:tid146",
        "disease_descriptor": "civic:did8",
        "method": "method:001",
        "supported_by": ["pmid:23982599"]
    }


@pytest.fixture(scope='module')
def civic_eid2997_proposition():
    """Create a test fixture for EID2997 proposition."""
    return {
        "id": "proposition:001",
        "predicate": "predicts_sensitivity_to",
        "subject": "ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR",
        "object_qualifier": "ncit:C2926",
        "object": "rxcui:1430438",
        "type": "therapeutic_response_proposition"
    }


@pytest.fixture(scope='module')
def civic_vid33():
    """Create a test fixture for CIViC VID33."""
    return {
        "id": "civic:vid33",
        "type": "VariationDescriptor",
        "label": "L858R",
        "description": "EGFR L858R has long been recognized as a functionally significant mutation in cancer, and is one of the most prevalent single mutations in lung cancer. Best described in non-small cell lung cancer (NSCLC), the mutation seems to confer sensitivity to first and second generation TKI's like gefitinib and neratinib. NSCLC patients with this mutation treated with TKI's show increased overall and progression-free survival, as compared to chemotherapy alone. Third generation TKI's are currently in clinical trials that specifically focus on mutant forms of EGFR, a few of which have shown efficacy in treating patients that failed to respond to earlier generation TKI therapies.",  # noqa: E501
        "value_id": "ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR",
        "value": {
            "location": {
                "interval": {
                    "end": 858,
                    "start": 857,
                    "type": "SimpleInterval"
                },
                "sequence_id": "ga4gh:SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "R",
                "type": "SequenceState"
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
                    "reference_build": "GRCh37"
                },
                "type": "Extension"
            },
            {
                "name": "civic_actionability_score",
                "value": "352.5",
                "type": "Extension"
            }
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs:protein",
                "value": "NP_005219.2:p.Leu858Arg",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:transcript",
                "value": "ENST00000275493.2:c.2573T>G",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:transcript",
                "value": "NM_005228.4:c.2573T>G",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:genomic",
                "value": "NC_000007.13:g.55259515T>G",
                "type": "Expression"
            }
        ],
        "gene_context": "civic:gid19"
    }


@pytest.fixture(scope='module')
def civic_gid19():
    """Create test fixture for CIViC GID19."""
    return {
        "id": "civic:gid19",
        "type": "GeneDescriptor",
        "label": "EGFR",
        "description": "EGFR is widely recognized for its importance in cancer. Amplification and mutations have been shown to be driving events in many cancer types. Its role in non-small cell lung cancer, glioblastoma and basal-like breast cancers has spurred many research and drug development efforts. Tyrosine kinase inhibitors have shown efficacy in EGFR amplfied tumors, most notably gefitinib and erlotinib. Mutations in EGFR have been shown to confer resistance to these drugs, particularly the variant T790M, which has been functionally characterized as a resistance marker for both of these drugs. The later generation TKI's have seen some success in treating these resistant cases, and targeted sequencing of the EGFR locus has become a common practice in treatment of non-small cell lung cancer. \nOverproduction of ligands is another possible mechanism of activation of EGFR. ERBB ligands include EGF, TGF-a, AREG, EPG, BTC, HB-EGF, EPR and NRG1-4 (for detailed information please refer to the respective ligand section).",  # noqa: E501
        "value": {
            "id": "hgnc:3236",
            "type": "Gene"
        },
        "alternate_labels": [
            "ERRP",
            "EGFR",
            "mENA",
            "PIG61",
            "NISBD2",
            "HER1",
            "ERBB1",
            "ERBB"
        ],
        "xrefs": [
            "ncbigene:1956"
        ]
    }


@pytest.fixture(scope='module')
def civic_tid146():
    """Create test fixture for CIViC TID146."""
    return {
        "id": "civic:tid146",
        "type": "TherapyDescriptor",
        "label": "Afatinib",
        "value": {
            "id": "rxcui:1430438",
            "type": "Drug"
        },
        "alternate_labels": [
            "BIBW2992",
            "BIBW 2992",
            "(2e)-N-(4-(3-Chloro-4-Fluoroanilino)-7-(((3s)-Oxolan-3-yl)Oxy)Quinoxazolin-6-yl)-4-(Dimethylamino)But-2-Enamide"  # noqa: E501
        ],
        "xrefs": [
            "ncit:C66940"
        ]
    }


@pytest.fixture(scope='module')
def civic_did8():
    """Create test fixture for CIViC DID8."""
    return {
        "id": "civic:did8",
        "type": "DiseaseDescriptor",
        "label": "Lung Non-small Cell Carcinoma",
        "value": {
            "id": "ncit:C2926",
            "type": "Disease"
        },
        "xrefs": [
            "DOID:3908"
        ]
    }


@pytest.fixture(scope='module')
def pmid_23982599():
    """Create test fixture for CIViC EID2997 document."""
    return {
        "id": "pmid:23982599",
        "type": "Document",
        "label": "Dungo et al., 2013, Drugs",
        "description": "Afatinib: first global approval."
    }


@pytest.fixture(scope='module')
def civic_eid1409_statement():
    """Create test fixture for CIViC Evidence 1406."""
    return {
        "id": "civic:eid1409",
        "description": "Phase 3 randomized clinical trial comparing vemurafenib with dacarbazine in 675 patients with previously untreated, metastatic melanoma with the BRAF V600E mutation. At 6 months, overall survival was 84% (95% confidence interval [CI], 78 to 89) in the vemurafenib group and 64% (95% CI, 56 to 73) in the dacarbazine group. A relative reduction of 63% in the risk of death and of 74% in the risk of either death or disease progression was observed with vemurafenib as compared with dacarbazine (P<0.001 for both comparisons).",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:A",
        "proposition": "proposition:701",
        "variation_origin": "somatic",
        "variation_descriptor": "civic:vid12",
        "therapy_descriptor": "civic:tid4",
        "disease_descriptor": "civic:did206",
        "method": "method:001",
        "supported_by": ["pmid:21639808"],
        "type": "Statement"
    }


@pytest.fixture(scope='module')
def civic_aid6_statement():
    """Create CIViC AID 6 test fixture."""
    return {
        "id": "civic:aid6",
        "description": "L858R is among the most common sensitizing EGFR mutations in NSCLC, and is assessed via DNA mutational analysis, including Sanger sequencing and next generation sequencing methods. Tyrosine kinase inhibitor afatinib is FDA approved, and is recommended (category 1) by NCCN guidelines along with erlotinib, gefitinib and osimertinib as first line systemic therapy in NSCLC with sensitizing EGFR mutation.",  # noqa: E501
        "direction": "supports",
        "evidence_level": "amp_asco_cap_2017_level:1A",
        "proposition": "proposition:001",
        "variation_origin": "somatic",
        "variation_descriptor": "civic:vid33",
        "therapy_descriptor": "civic:tid146",
        "disease_descriptor": "civic:did8",
        "method": "method:002",
        "supported_by": ["document:001", "civic:eid2997",
                         "civic:eid2629", "civic:eid982", "civic:eid968",
                         "civic:eid883", "civic:eid879"],
        "type": "Statement"
    }


@pytest.fixture(scope='module')
def civic_aid6_document():
    """Create test fixture for civic aid6 document."""
    return {
        "id": "document:001",
        "document_id": "https://www.nccn.org/professionals/"
                       "physician_gls/default.aspx",
        "label": "NCCN Guidelines: Non-Small Cell "
                 "Lung Cancer version 3.2018",
        "type": "Document"
    }


@pytest.fixture(scope='module')
def civic_eid2_statement():
    """Create a test fixture for CIViC EID2 statement."""
    return {
        "id": "civic:eid2",
        "type": "Statement",
        "description": "GIST tumors harboring PDGFRA D842V mutation are more likely to be benign than malignant.",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:B",
        "proposition": "proposition:001",
        "variation_origin": "somatic",
        "variation_descriptor": "civic:vid99",
        "disease_descriptor": "civic:did2",
        "method": "method:001",
        "supported_by": ["pmid:15146165"]
    }


@pytest.fixture(scope='module')
def civic_eid2_proposition():
    """Create a test fixture for CIViC EID2 proposition."""
    return {
        "id": "proposition:001",
        "predicate": "is_diagnostic_exclusion_criterion_for",
        "subject": "ga4gh:VA.3Yv7t0YzME9W4xErQf7-eFWtqvdfmjgt",
        "object_qualifier": "ncit:C3868",
        "type": "diagnostic_proposition"
    }


@pytest.fixture(scope='module')
def civic_vid99():
    """Create a test fixture for CIViC VID99."""
    return {
        "id": "civic:vid99",
        "type": "VariationDescriptor",
        "label": "D842V",
        "description": "PDGFRA D842 mutations are characterized broadly as imatinib resistance mutations. This is most well characterized in gastrointestinal stromal tumors, but other cell lines containing these mutations have been shown to be resistant as well. Exogenous expression of the A842V mutation resulted in constitutive tyrosine phosphorylation of PDGFRA in the absence of ligand in 293T cells and cytokine-independent proliferation of the IL-3-dependent Ba/F3 cell line, both evidence that this is an activating mutation. In imatinib resistant cell lines, a number of other therapeutics have demonstrated efficacy. These include; crenolanib, sirolimus, and midostaurin (PKC412).",  # noqa: E501
        "value_id": "ga4gh:VA.3Yv7t0YzME9W4xErQf7-eFWtqvdfmjgt",
        "value": {
            "location": {
                "interval": {
                    "start": 841,
                    "end": 842,
                    "type": "SimpleInterval"
                },
                "sequence_id": "ga4gh:SQ.XpQn9sZLGv_GU3uiWO7YHq9-_alGjrVX",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "V",
                "type": "SequenceState"
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
                    "reference_build": "GRCh37"
                },
                "type": "Extension"
            },
            {
                "name": "civic_actionability_score",
                "value": "100.5",
                "type": "Extension"
            },
            {
                "name": "variant_group",
                "value": [
                    {
                        "id": "civic:vgid1",
                        "label": "Imatinib Resistance",
                        "description": "While imatinib has shown to be incredibly successful in treating philadelphia chromosome positive CML, patients that have shown primary or secondary resistance to the drug have been observed to harbor T315I and E255K ABL kinase domain mutations. These mutations, among others, have been observed both in primary refractory disease and acquired resistance. In gastrointestinal stromal tumors (GIST), PDGFRA 842 mutations have also been shown to confer resistance to imatinib. ",  # noqa: E501
                        'type': 'variant_group'
                    }
                ],
                "type": "Extension"
            }
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs:transcript",
                "value": "NM_006206.4:c.2525A>T",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:protein",
                "value": "NP_006197.1:p.Asp842Val",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:transcript",
                "value": "ENST00000257290.5:c.2525A>T",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:genomic",
                "value": "NC_000004.11:g.55152093A>T",
                "type": "Expression"
            }
        ],
        "gene_context": "civic:gid38"
    }


@pytest.fixture(scope='module')
def civic_did2():
    """Create a test fixture for CIViC DID2."""
    return {
        "id": "civic:did2",
        "type": "DiseaseDescriptor",
        "label": "Gastrointestinal Stromal Tumor",
        "value": {
            "id": "ncit:C3868",
            "type": "Disease"
        },
        "xrefs": [
            "DOID:9253"
        ]
    }


@pytest.fixture(scope='module')
def civic_gid38():
    """Create a test fixture for CIViC GID38."""
    return {
        "id": "civic:gid38",
        "type": "GeneDescriptor",
        "label": "PDGFRA",
        "description": "Commonly mutated in GI tract tumors, PDGFR family genes (mutually exclusive to KIT mutations) are a hallmark of gastrointestinal stromal tumors. Gene fusions involving the PDGFRA kinase domain are highly correlated with eosinophilia, and the WHO classifies myeloid and lymphoid neoplasms with these characteristics as a distinct disorder. Mutations in the 842 region of PDGFRA have been often found to confer resistance to the tyrosine kinase inhibitor, imatinib.",  # noqa: E501
        "value": {
            "id": "hgnc:8803",
            "type": "Gene"
        },
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


@pytest.fixture(scope='module')
def civic_eid74_statement():
    """Create a test fixture for CIViC EID74 statement."""
    return {
        "id": "civic:eid74",
        "description": "In patients with medullary carcinoma, the presence of RET M918T mutation is associated with increased probability of lymph node metastases.",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:B",
        "proposition": "proposition:002",
        "variation_origin": "somatic",
        "variation_descriptor": "civic:vid113",
        "disease_descriptor": "civic:did15",
        "method": "method:001",
        "supported_by": ["pmid:18073307"],
        "type": "Statement"
    }


@pytest.fixture(scope='module')
def civic_eid74_proposition():
    """Create a test fixture for CIViC EID74 proposition."""
    return {
        "id": "proposition:002",
        "predicate": "is_diagnostic_inclusion_criterion_for",
        "subject": "ga4gh:VA.ifPUeUiHj0TkYmimFK7T7jvbucAsGKqa",
        "object_qualifier": "ncit:C3879",
        "type": "diagnostic_proposition"
    }


@pytest.fixture(scope='module')
def civic_vid113():
    """Create a test fixture for CIViC VID113."""
    return {
        "id": "civic:vid113",
        "type": "VariationDescriptor",
        "label": "M918T",
        "description": "RET M819T is the most common somatically acquired mutation in medullary thyroid cancer (MTC). While there currently are no RET-specific inhibiting agents, promiscuous kinase inhibitors have seen some success in treating RET overactivity. Data suggests however, that the M918T mutation may lead to drug resistance, especially against the VEGFR-inhibitor motesanib. It has also been suggested that RET M819T leads to more aggressive MTC with a poorer prognosis.",  # noqa: E501
        "value_id": "ga4gh:VA.ifPUeUiHj0TkYmimFK7T7jvbucAsGKqa",
        "value": {
            "location": {
                "interval": {
                    "end": 918,
                    "start": 917,
                    "type": "SimpleInterval"
                },
                "sequence_id": "ga4gh:SQ.jMu9-ItXSycQsm4hyABeW_UfSNRXRVnl",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "T",
                "type": "SequenceState"
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
                    "reference_build": "GRCh37"
                },
                "type": "Extension"
            },
            {
                "name": "civic_actionability_score",
                "value": "86",
                "type": "Extension"
            },
            {
                "name": "variant_group",
                "value": [
                    {
                        "id": "civic:vgid6",
                        "label": "Motesanib Resistance",
                        "description": "RET activation is a common oncogenic marker of medullary thyroid carcinoma. Treatment of these patients with the targeted therapeutic motesanib has shown to be effective. However, the missense mutations C634W and M918T have shown to confer motesanib resistance in cell lines. ",  # noqa: E501
                        'type': 'variant_group'
                    }
                ],
                "type": "Extension"
            }
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs:transcript",
                "value": "NM_020975.4:c.2753T>C",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:protein",
                "value": "NP_065681.1:p.Met918Thr",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:transcript",
                "value": "ENST00000355710.3:c.2753T>C",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:genomic",
                "value": "NC_000010.10:g.43617416T>C",
                "type": "Expression"
            }
        ],
        "gene_context": "civic:gid42"
    }


@pytest.fixture(scope='module')
def civic_did15():
    """Create test fixture for CIViC DID15."""
    return {
        "id": "civic:did15",
        "type": "DiseaseDescriptor",
        "label": "Thyroid Gland Medullary Carcinoma",
        "value": {
            "id": "ncit:C3879",
            "type": "Disease"
        },
        "xrefs": [
            "DOID:3973"
        ]
    }


@pytest.fixture(scope='module')
def civic_gid42():
    """Create test fixture for CIViC GID42."""
    return {
        "id": "civic:gid42",
        "type": "GeneDescriptor",
        "label": "RET",
        "description": "RET mutations and the RET fusion RET-PTC lead to activation of this tyrosine kinase receptor and are associated with thyroid cancers. RET point mutations are the most common mutations identified in medullary thyroid cancer (MTC) with germline and somatic mutations in RET associated with hereditary and sporadic forms, respectively. The most common somatic form mutation is M918T (exon 16) and a variety of other mutations effecting exons 10, 11 and 15 have been described. The prognostic significance of these mutations have been hotly debated in the field, however, data suggests that some RET mutation may confer drug resistence. No RET-specific agents are currently clinically available but several promiscuous kinase inhibitors that target RET, among others, have been approved for MTC treatment.",  # noqa: E501
        "value": {
            "id": "hgnc:9967",
            "type": "Gene"
        },
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


@pytest.fixture(scope='module')
def civic_aid9_statement():
    """Create a test fixture for CIViC AID9 statement."""
    return {
        "id": "civic:aid9",
        "description": "ACVR1 G328V mutations occur within the kinase domain, leading to activation of downstream signaling. Exclusively seen in high-grade pediatric gliomas, supporting diagnosis of diffuse intrinsic pontine glioma.",  # noqa: E501
        "direction": "supports",
        "evidence_level": "amp_asco_cap_2017_level:2C",
        "proposition": "proposition:003",
        "variation_origin": "somatic",
        "variation_descriptor": "civic:vid1686",
        "disease_descriptor": "civic:did2950",
        "method": "method:002",
        "supported_by": ["civic:eid4846", "civic:eid6955"],
        "type": "Statement"
    }


@pytest.fixture(scope='module')
def civic_aid9_proposition():
    """Create a test fixture for CIViC AID9 proposition."""
    return {
        "id": "proposition:003",
        "predicate": "is_diagnostic_inclusion_criterion_for",
        "subject": "ga4gh:VA.twWuxZk0p0Vn3NSkp0kwD1VgfNN2fvDm",
        "object_qualifier": "DOID:0080684",
        "type": "diagnostic_proposition"
    }


@pytest.fixture(scope='module')
def civic_vid1686():
    """Create a test fixture for CIViC VID1686."""
    return {
        "id": "civic:vid1686",
        "type": "VariationDescriptor",
        "label": "G328V",
        "value_id": "ga4gh:VA.twWuxZk0p0Vn3NSkp0kwD1VgfNN2fvDm",
        "value": {
            "location": {
                "interval": {
                    "end": 328,
                    "start": 327,
                    "type": "SimpleInterval"
                },
                "sequence_id": "ga4gh:SQ.6CnHhDq_bDCsuIBf0AzxtKq_lXYM7f0m",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "V",
                "type": "SequenceState"
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
                    "reference_build": "GRCh37"
                },
                "type": "Extension"
            },
            {
                "name": "civic_actionability_score",
                "value": "30",
                "type": "Extension"
            },
            {
                "name": "variant_group",
                "value": [
                    {
                        "id": "civic:vgid23",
                        "label": "ACVR1 kinase domain mutation",
                        'type': 'variant_group'
                    }
                ],
                "type": "Extension"
            }
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs:transcript",
                "value": "NM_001105.4:c.983G>T",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:protein",
                "value": "NP_001096.1:p.Gly328Val",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:genomic",
                "value": "NC_000002.11:g.158622516C>A",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:transcript",
                "value": "ENST00000434821.1:c.983G>T",
                "type": "Expression"
            }
        ],
        "gene_context": "civic:gid154"
    }


@pytest.fixture(scope='module')
def civic_did2950():
    """Create a test fixture for CIViC DID2950."""
    return {
        "id": "civic:did2950",
        "type": "DiseaseDescriptor",
        "label": "Diffuse Midline Glioma, H3 K27M-mutant",
        "value": {
            "id": "DOID:0080684",
            "type": "Disease"
        },
        "xrefs": [
            "DOID:0080684"
        ]
    }


@pytest.fixture(scope='module')
def civic_gid154():
    """Create a test fixture for CIViC GID154."""
    return {
        "id": "civic:gid154",
        "type": "GeneDescriptor",
        "label": "ACVR1",
        "value": {
            "id": "hgnc:171",
            "type": "Gene"
        },
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


@pytest.fixture(scope='module')
def civic_eid26_statement():
    """Create a test fixture for CIViC EID26 statement."""
    return {
        "id": "civic:eid26",
        "description": "In acute myloid leukemia patients, D816 mutation is associated with earlier relapse and poorer prognosis than wildtype KIT.",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:B",
        "proposition": "proposition:001",
        "variation_origin": "somatic",
        "variation_descriptor": "civic:vid65",
        "disease_descriptor": "civic:did3",
        "method": "method:001",
        "supported_by": ["pmid:16384925"],
        "type": "Statement"
    }


@pytest.fixture(scope='module')
def civic_eid26_proposition():
    """Create a test fixture for CIViC EID26 proposition."""
    return {
        "id": "proposition:001",
        "predicate": "is_prognostic_of_worse_outcome_for",
        "subject": "ga4gh:VA.EGLm8XWH3V17-VZw7vEygPmy4wHQ8mCf",
        "object_qualifier": "ncit:C3171",
        "type": "prognostic_proposition"
    }


@pytest.fixture(scope='module')
def civic_vid65():
    """Create a test fixture for CIViC VID65."""
    return {
        "id": "civic:vid65",
        "type": "VariationDescriptor",
        "label": "D816V",
        "description": "KIT D816V is a mutation observed in acute myeloid leukemia (AML). This variant has been linked to poorer prognosis and worse outcome in AML patients.",  # noqa: E501
        "value_id": "ga4gh:VA.EGLm8XWH3V17-VZw7vEygPmy4wHQ8mCf",
        "value": {
            "location": {
                "interval": {
                    "end": 816,
                    "start": 815,
                    "type": "SimpleInterval"
                },
                "sequence_id": "ga4gh:SQ.TcMVFj5kDODDWpiy1d_1-3_gOf4BYaAB",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "V",
                "type": "SequenceState"
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
                    "reference_build": "GRCh37"
                },
                "type": "Extension"
            },
            {
                "name": "civic_actionability_score",
                "value": "67",
                "type": "Extension"
            },
            {
                "name": "variant_group",
                "value": [
                    {
                        "id": "civic:vgid2",
                        "label": "KIT Exon 17",
                        'type': 'variant_group'
                    }
                ],
                "type": "Extension"
            }
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs:transcript",
                "value": "NM_000222.2:c.2447A>T",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:protein",
                "value": "NP_000213.1:p.Asp816Val",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:transcript",
                "value": "ENST00000288135.5:c.2447A>T",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:genomic",
                "value": "NC_000004.11:g.55599321A>T",
                "type": "Expression"
            }
        ],
        "gene_context": "civic:gid29"
    }


@pytest.fixture(scope='module')
def civic_did3():
    """Create test fixture for CIViC DID3."""
    return {
        "id": "civic:did3",
        "type": "DiseaseDescriptor",
        "label": "Acute Myeloid Leukemia",
        "value": {
            "id": "ncit:C3171",
            "type": "Disease"
        },
        "xrefs": [
            "DOID:9119"
        ]
    }


@pytest.fixture(scope='module')
def civic_gid29():
    """Create test fixture for CIViC GID29."""
    return {
        "id": "civic:gid29",
        "type": "GeneDescriptor",
        "label": "KIT",
        "description": "c-KIT activation has been shown to have oncogenic activity in gastrointestinal stromal tumors (GISTs), melanomas, lung cancer, and other tumor types. The targeted therapeutics nilotinib and sunitinib have shown efficacy in treating KIT overactive patients, and are in late-stage trials in melanoma and GIST. KIT overactivity can be the result of many genomic events from genomic amplification to overexpression to missense mutations. Missense mutations have been shown to be key players in mediating clinical response and acquired resistance in patients being treated with these targeted therapeutics.",  # noqa: E501
        "value": {
            "id": "hgnc:6342",
            "type": "Gene"
        },
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


@pytest.fixture(scope='module')
def civic_eid1756_statement():
    """Create test fixture for CIViC EID1756 statement."""
    return {
        "id": "civic:eid1756",
        "description": "Study of 1817 PCa cases and 2026 cancer free controls to clarify the association of (MTHFR)c.677C>T  (and c.1298A>C ) of pancreatic cancer risk in a population of Han Chinese in Shanghai.  Results indicated a lower risk for the heterozygous CT genotype and homozygous TT genotype carriers of (MTHFR)c.677C>T  which had a significantly lower risk of developing pancreatic cancer compared with the wild-type CC genotype.",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:B",
        "proposition": "proposition:002",
        "variation_origin": "germline",
        "variation_descriptor": "civic:vid258",
        "disease_descriptor": "civic:did556",
        "method": "method:001",
        "supported_by": ["pmid:27819322"],
        "type": "Statement"
    }


@pytest.fixture(scope='module')
def civic_eid1756_proposition():
    """Create a test fixture for CIViC EID1756 proposition."""
    return {
        "id": "proposition:002",
        "predicate": "is_prognostic_of_better_outcome_for",
        "subject": "ga4gh:VA.V5IUMLhaM8Oo-oAClUZqb-gDPaIzIi-A",
        "object_qualifier": "ncit:C9005",
        "type": "prognostic_proposition"
    }


@pytest.fixture(scope='module')
def civic_vid258():
    """Create a test fixture for CIViC VID258."""
    return {
        "id": "civic:vid258",
        "type": "VariationDescriptor",
        "label": "A222V",
        "value_id": "ga4gh:VA.V5IUMLhaM8Oo-oAClUZqb-gDPaIzIi-A",
        "value": {
            "location": {
                "interval": {
                    "end": 222,
                    "start": 221,
                    "type": "SimpleInterval"
                },
                "sequence_id": "ga4gh:SQ.4RSETawLfMkNpQBPepa7Uf9ItHAEJUde",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "V",
                "type": "SequenceState"
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
                    "reference_build": "GRCh37"
                },
                "type": "Extension"
            },
            {
                "name": "civic_actionability_score",
                "value": "55",
                "type": "Extension"
            }
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs:transcript",
                "value": "NM_005957.4:c.665C>T",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:protein",
                "value": "NP_005948.3:p.Ala222Val",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:transcript",
                "value": "ENST00000376592.1:c.665G>A",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:genomic",
                "value": "NC_000001.10:g.11856378G>A",
                "type": "Expression"
            }
        ],
        "gene_context": "civic:gid3672"
    }


@pytest.fixture(scope='module')
def civic_did556():
    """Create a test fixture for CIViC DID556."""
    return {
        "id": "civic:did556",
        "type": "DiseaseDescriptor",
        "label": "Pancreatic Cancer",
        "value": {
            "id": "ncit:C9005",
            "type": "Disease"
        },
        "xrefs": [
            "DOID:1793"
        ]
    }


@pytest.fixture(scope='module')
def civic_gid3672():
    """Create test fixture for CIViC GID3672."""
    return {
        "id": "civic:gid3672",
        "type": "GeneDescriptor",
        "label": "MTHFR",
        "value": {
            "id": "hgnc:7436",
            "type": "Gene"
        },
        "alternate_labels": [
            "MTHFR"
        ],
        "xrefs": [
            "ncbigene:4524"
        ]
    }


@pytest.fixture(scope='module')
def pmid_15146165():
    """Create a test fixture for PMID 15146165."""
    return {
        "id": "pmid:15146165",
        "label": "Lasota et al., 2004, Lab. Invest.",
        "type": "Document",
        "description": "A great majority of GISTs with PDGFRA mutations represent gastric tumors of low or no malignant potential."  # noqa: E501
    }


@pytest.fixture(scope='module')
def pmid_18073307():
    """Create a test fixture for PMID 18073307."""
    return {
        "type": "Document",
        "id": "pmid:18073307",
        "label": "Elisei et al., 2008, J. Clin. Endocrinol. Metab.",
        "description": "Prognostic significance of somatic RET oncogene mutations in sporadic medullary thyroid cancer: a 10-year follow-up study."  # noqa: E501
    }


@pytest.fixture(scope='module')
def pmid_16384925():
    """Create a test fixture for PMID 16384925."""
    return {
        "id": "pmid:16384925",
        "label": "Cairoli et al., 2006, Blood",
        "description": "Prognostic impact of c-KIT mutations in core binding factor leukemias: an Italian retrospective study.",  # noqa: E501
        "type": "Document"
    }


@pytest.fixture(scope='module')
def pmid_27819322():
    """Create a test fixture for PMID 27819322."""
    return {
        "type": "Document",
        "id": "pmid:27819322",
        "label": "Wu et al., 2016, Sci Rep",
        "description": "MTHFR c.677C>T Inhibits Cell Proliferation and Decreases Prostate Cancer Susceptibility in the Han Chinese Population in Shanghai.",  # noqa: E501
        "xrefs": ["pmc:PMC5098242"]
    }


@pytest.fixture(scope='module')
def moa_aid69_statement():
    """Create a MOA Statement 69 test fixture."""
    return {
        "id": "moa:aid69",
        "description": "T315I mutant ABL1 in p210 BCR-ABL cells resulted in retained high levels of phosphotyrosine at increasing concentrations of inhibitor STI-571, whereas wildtype appropriately received inhibition.",  # noqa: E501
        "evidence_level": "moa.evidence_level:Preclinical",
        "proposition": "proposition:001",
        "variation_origin": "somatic",
        "variation_descriptor": "moa:vid69",
        "therapy_descriptor": "moa.normalize.therapy:Imatinib",
        "disease_descriptor": "moa.normalize.disease:oncotree%3ACML",
        "method": "method:004",
        "supported_by": [
            "pmid:11423618"
        ],
        "type": "Statement"
    }


@pytest.fixture(scope='module')
def moa_aid69_proposition():
    """Create a test fixture for MOA AID69 proposition."""
    return {
        "id": "proposition:001",
        "predicate": "predicts_resistance_to",
        "subject": "ga4gh:VA.wVNOLHSUDotkavwqtSiPW1aWxJln3VMG",
        "object_qualifier": "ncit:C3174",
        "object": "rxcui:282388",
        "type": "therapeutic_response_proposition"
    }


@pytest.fixture(scope='module')
def moa_vid69():
    """Create a test fixture for MOA VID69."""
    return {
        "id": "moa:vid69",
        "type": "VariationDescriptor",
        "label": "ABL1 p.T315I (Missense)",
        "value_id": "ga4gh:VA.wVNOLHSUDotkavwqtSiPW1aWxJln3VMG",
        "value": {
            "location": {
                "interval": {
                    "end": 315,
                    "start": 314,
                    "type": "SimpleInterval"
                },
                "sequence_id": "ga4gh:SQ.dmFigTG-0fY6I54swb7PoDuxCeT6O3Wg",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "I",
                "type": "SequenceState"
            },
            "type": "Allele"
        },
        "extensions": [
            {
                "name": "moa_representative_coordinate",
                "value": {
                    "chromosome": "9",
                    "start_position": "133747580.0",
                    "end_position": "133747580.0",
                    "reference_allele": "C",
                    "alternate_allele": "T",
                    "cdna_change": "c.944C>T",
                    "protein_change": "p.T315I",
                    "exon": "5.0"
                },
                "type": "Extension"
            }
        ],
        "ref_allele_seq": "T",
        "gene_context": "moa.normalize.gene:ABL1"
    }


@pytest.fixture(scope='module')
def moa_abl1():
    """Create a test fixture for MOA ABL1 Gene Descriptor."""
    return {
        "id": "moa.normalize.gene:ABL1",
        "type": "GeneDescriptor",
        "label": "ABL1",
        "value": {
            "id": "hgnc:76",
            "type": "Gene"
        }
    }


@pytest.fixture(scope='module')
def moa_imatinib():
    """Create a test fixture for MOA Imatinib Therapy Descriptor."""
    return {
        "id": "moa.normalize.therapy:Imatinib",
        "type": "TherapyDescriptor",
        "label": "Imatinib",
        "value": {
            "id": "rxcui:282388",
            "type": "Drug"
        }
    }


@pytest.fixture(scope='module')
def moa_chronic_myelogenous_leukemia():
    """Create test fixture for MOA Chronic Myelogenous Leukemia Descriptor."""
    return {
        "id": "moa.normalize.disease:oncotree%3ACML",
        "type": "DiseaseDescriptor",
        "label": "Chronic Myelogenous Leukemia",
        "value": {
            "id": "ncit:C3174",
            "type": "Disease"
        }
    }


@pytest.fixture(scope='module')
def method001():
    """Create test fixture for method:001."""
    return {
        "id": "method:001",
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


@pytest.fixture(scope='module')
def method002():
    """Create test fixture for method:002."""
    return {
        "id": "method:002",
        "type": "Method",
        "label": "Standards and Guidelines for the Interpretation and Reporting of Sequence Variants in Cancer: A Joint Consensus Recommendation of the Association for Molecular Pathology, American Society of Clinical Oncology, and College of American Pathologists",  # noqa: E501
        "url": "https://pubmed.ncbi.nlm.nih.gov/27993330/",
        "version": {
            "year": 2017,
            "month": 1
        },
        "authors": "Li MM, Datto M, Duncavage EJ, et al."
    }


@pytest.fixture(scope='module')
def method003():
    """Create test fixture for method:003."""
    return {
        "id": "method:003",
        "label": "Standards and guidelines for the interpretation of sequence variants: a joint consensus recommendation of the American College of Medical Genetics and Genomics and the Association for Molecular Pathology",  # noqa: E501
        "url": "https://pubmed.ncbi.nlm.nih.gov/25741868/",
        "version": {
            "year": 2015,
            "month": 5
        },
        "type": "Method",
        "authors": "Richards S, Aziz N, Bale S, et al."
    }


@pytest.fixture(scope='module')
def method004():
    """Create a test fixture for MOA method:004."""
    return {
        "id": "method:004",
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


@pytest.fixture(scope='module')
def civic_methods(method001, method002, method003):
    """Create test fixture for methods."""
    return [method001, method002, method003]


@pytest.fixture(scope='module')
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


@pytest.fixture(scope='module')
def pmkb_statement_113():
    """Create fixture for PMKB statement 113"""
    return {
        "id": "pmkb.statement:113",
        "description": "CTNNB1 encodes the protein b-catenin, a transcriptional activator involved in the WNT signaling pathway. Somatic gain-of-function mutations in CTNNB1 result in aberrant accumulation of the b-catenin protein and are prevalent in a wide range of solid tumors, including endometrial carcinoma, ovarian carcinoma, hepatocellular carcinoma, and colorectal carcinoma, among others. Genetic alterations in CTNNB1 have been identified in 4% of non-small cell lung cancers. The CTNNB1 S45P mutation is likely oncogenic, but no real progress has been made in targeting oncogenic mutant forms of CTNNB1 in lung cancer. However, CTNNB1 mutation-positive cancers are presumed to be resistant to pharmacologic inhibition of upstream components of the WNT pathway, instead requiring direct inhibition of b-catenin function. In one study pharmacological inhibition of b-catenin suppressed EGFR-L858R/T790M mutated lung tumor and genetic deletion of the b-catenin gene dramatically reduced lung tumor formation in transgenic mice, suggesting that b-catenin plays an essential role in lung tumorigenesis and that targeting the b-catenin pathway may provide novel strategies to prevent lung cancer development or overcome resistance to EGFR TKIs. These results should be interpreted in the clinical context.",  # noqa: E501
        "evidence_level": "2",
        "proposition": "proposition:1",
        "variation_descriptor": "pmkb.variant:217",
        "therapy_descriptor": "pmkb.normalize.therapy:therapeutic%20procedure",
        "disease_descriptor": "pmkb.normalize.disease:Adenocarcinoma",
        "method": "method:5",
        "supported_by": [
            "document:1",
            "document:2",
            "document:3",
            "document:4",
            "document:5",
            "document:6",
            "document:7",
            "document:8",
            "document:9",
            "document:10"
        ],
        "variation_origin": "somatic",
        "type": "Statement"
    }


@pytest.fixture(scope='module')
def pmkb_vod_variant_217():
    """Create fixture for VOD of PMKB variant CTNNB1 S45P."""
    return {
        "id": "pmkb.variant:217",
        "type": "VariationDescriptor",
        "label": "CTNNB1 S45P",
        "value_id": "ga4gh:VA.6CgLeqGUIVF2XLiMwOpy142d2_iBTt7V",
        "value": {
            "location": {
                "interval": {
                    "end": 45,
                    "start": 44,
                    "type": "SimpleInterval"
                },
                "sequence_id": "ga4gh:SQ.FhMJAgGb9jn2O4_xxRn3C1JNlL0MKKsM",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "P",
                "type": "SequenceState"
            },
            "type": "Allele"
        },
        "molecule_context": "protein",
        "structural_type": "SO:0001606",
        "ref_allele_seq": "S",
        "gene_context": "pmkb.normalize.gene:CTNNB1",
        "extensions": [
            {
                "name": "associated_with",
                "value": [
                    "ensembl:ENST00000349496"
                ],
                "type": "Extension"
            }
        ]
    }


@pytest.fixture(scope='module')
def pmkb_vod_adenocarcinoma():
    """Create fixture for VOD of PMKB disease adenocarcinoma."""
    return {
        "id": "pmkb.normalize.disease:Adenocarcinoma",
        "type": "DiseaseDescriptor",
        "label": "Adenocarcinoma",
        "value": {
            "id": "ncit:C2852",
            "type": "Disease"
        },
        "extensions": [
            {
                "type": "Extension",
                "name": "tissue_types",
                "value": [
                    "Lung"
                ]
            }
        ]
    }


@pytest.fixture(scope='module')
def pmkb_vod_therapeutic_procedure():
    """Create fixture for VOD of PMKB therapy Therapeutic Procedure."""
    return {
        "id": "pmkb.normalize.therapy:therapeutic%20procedure",
        "type": "TherapyDescriptor",
        "label": "therapeutic procedure",
        "value": {
            "id": "ncit:C49236",
            "type": "Drug"
        }
    }


@pytest.fixture(scope='module')
def pmkb_vod_ctnnb1():
    """Create fixture for VOD of PMKB gene CTNNB1."""
    return {
        "id": "pmkb.normalize.gene:CTNNB1",
        "type": "GeneDescriptor",
        "label": "CTNNB1",
        "value": {
            "id": "hgnc:2514",
            "type": "Gene"
        }
    }


@pytest.fixture(scope='module')
def pmkb_method():
    """Create test fixture for PMKB method object."""
    return {
        "id": "method:5",
        "label": "The cancer precision medicine knowledge base for structured clinical-grade mutations and interpretations",  # noqa: E501
        "url": "https://academic.oup.com/jamia/article/24/3/513/2418181",
        "version": {
            "year": 2016,
            "month": 5,
            "day": None
        },
        "authors": "Huang et al.",
        "type": "Method"
    }


@pytest.fixture(scope='module')
def pmkb_docs():
    """Create fixture for PMKB documents associated w/ PMKB statement 217."""
    return [
        {
            "id": "document:1",
            "label": "Cancer Genome Atlas Research Network, Kandoth C, Schultz N, Cherniack AD,",  # noqa: E501
            "type": "Document"
        },
        {
            "id": "document:2",
            "label": "Akbani R, Liu Y, Shen H, Robertson AG, Pashtan I, Shen R, Benz CC, Yau C, Laird PW, Ding L, Zhang W, Mills GB, Kucherlapati R, Mardis ER, Levine DA. Integrated genomic characterization of endometrial carcinoma. Nature. 2013 May 2;497(7447):67-73.",  # noqa: E501
            "type": "Document"
        },
        {
            "id": "document:3",
            "label": "Cancer Genome Atlas Network. Comprehensive molecular characterization of human colon and rectal cancer. Nature. 2012 Jul 18;487(7407):330-7.",  # noqa: E501
            "type": "Document"
        },
        {
            "id": "document:4",
            "label": "Kan Z, Zheng H, Liu X, Li S, Barber TD, Gong Z, Gao H, Hao K, Willard MD, Xu",  # noqa: E501
            "type": "Document"
        },
        {
            "id": "document:5",
            "label": "J, Hauptschein R, Rejto PA, Fernandez J, Wang G, Zhang Q, Wang B, Chen R, Wang J,Lee NP, Zhou W, Lin Z, Peng Z, Yi K, Chen S, Li L, Fan X, Yang J, Ye R, Ju J,Wang K, Estrella H, Deng S, Wei P, Qiu M, Wulur IH, Liu J, Ehsani ME, Zhang C,Loboda A, Sung WK, Aggarwal A, Poon RT, Fan ST, Wang J, Hardwick J, Reinhard C,Dai H, Li Y, Luk JM, Mao M. Whole-genome sequencing identifies recurrent mutations in hepatocellular carcinoma. Genome Res. 2013 Sep;23(9):1422-33.",  # noqa: E501
            "type": "Document"
        },
        {
            "id": "document:6",
            "label": "Clevers H, Nusse R. Wnt/b-catenin signaling and disease. Cell. 2012 Jun 8;149(6):1192-205.",  # noqa: E501
            "type": "Document"
        },
        {
            "id": "document:7",
            "label": "Greulich. The Genomics of Lung Adenocarcinoma: Opportunities for Targeted Therapies. Genes & Cancer 1(12) 1200--1210.",  # noqa: E501
            "type": "Document"
        },
        {
            "id": "document:8",
            "label": "NGS sequencing of 240 NSCLC cases treated at MSKCC with anti-PD-(L)1 based therapy using the MSK-IMPACT assay.",  # noqa: E501
            "type": "Document"
        },
        {
            "id": "document:9",
            "label": "Austinat M, Dunsch R, Wittekind C, Tannapfel A, Gebhardt R, Gaunitz F. Correlation between beta-catenin mutations and expression of Wnt-signaling target genes in hepatocellular carcinoma. Mol Cancer. 2008 Feb 18;7:21.",  # noqa: E501
            "type": "Document"
        },
        {
            "id": "document:10",
            "label": "Nakayama S, Sng N, Carretero J, et al. b-catenin contributes to lung tumor development induced by EGFR mutations. Cancer Res. 2014;74 (20):5891-902.",  # noqa: E501
            "type": "Document"
        }
    ]


@pytest.fixture(scope='module')
def pmkb_proposition():
    """Create fixture for PMKB proposition."""
    return {
        "id": "proposition:1",
        "type": "therapeutic_response_proposition",
        "predicate": "predicts_resistance_to",
        "subject": "ga4gh:VA.6CgLeqGUIVF2XLiMwOpy142d2_iBTt7V",
        "object_qualifier": "ncit:C2852",
        "object": "ncit:C49236"
    }


@pytest.fixture(scope='module')
def check_statement():
    """Create a test fixture to compare statements."""
    def check_statement(actual, test):
        """Check that statements are match."""
        assert actual.keys() == test.keys()
        assert actual['id'] == test['id']
        assert actual['description'] == test['description']
        if 'direction' in test.keys():
            # MOA doesn't have direction?
            assert actual['direction'] == test['direction']
        assert actual['evidence_level'] == test['evidence_level']
        assert actual['proposition'].startswith('proposition:')
        assert actual['variation_origin'] == test['variation_origin']
        assert actual['variation_descriptor'] == test['variation_descriptor']
        if 'therapy_descriptor' not in test.keys():
            assert 'therapy_descriptor' not in actual.keys()
        else:
            assert actual['therapy_descriptor'] == test['therapy_descriptor']
        assert actual['disease_descriptor'] == test['disease_descriptor']
        assert actual['method'] == test['method']
        assert set(actual['supported_by']) == set(test['supported_by'])
        assert actual['type'] == test['type']
    return check_statement


@pytest.fixture(scope='module')
def check_proposition():
    """Create a test fixture to compare propositions."""
    def check_proposition(actual, test):
        """Check that propositions match."""
        assert actual.keys() == test.keys()
        assert actual['id'].startswith('proposition:')
        assert actual['type'] == test['type']
        if test['type'] == 'therapeutic_response_proposition':
            assert actual['object'] == test['object']
        else:
            assert 'object' not in actual.keys()
        assert actual['predicate'] == test['predicate']
        assert actual['subject'] == test['subject']
        assert actual['object_qualifier'] == test['object_qualifier']
    return check_proposition


@pytest.fixture(scope='module')
def check_variation_descriptor():
    """Create a test fixture to compare variation descriptors."""
    def check_variation_descriptor(actual, test):
        """Check that variation descriptors match."""
        actual_keys = actual.keys()
        test_keys = test.keys()
        assert actual_keys == test_keys
        for key in test_keys:
            if key in ['id', 'type', 'label', 'description', 'value_id',
                       'structural_type', 'ref_seq_allele', 'gene_context']:
                assert actual[key] == test[key]
            elif key in ['xrefs', 'alternate_labels']:
                assert set(actual[key]) == set(test[key])
            elif key == 'value':
                assert actual['value'] == test['value']
            elif key == 'extensions':
                assert len(actual) == len(test)
                for test_extension in test['extensions']:
                    for actual_extension in actual['extensions']:
                        if test_extension['name'] == actual_extension['name']:
                            if test_extension['name'] != \
                                    'civic_actionability_score':
                                assert actual_extension == test_extension
                            else:
                                try:
                                    float(actual_extension['value'])
                                except ValueError:
                                    assert False
                                else:
                                    assert True
            elif key == 'expressions':
                assert len(actual['expressions']) == len(test['expressions'])
                for expression in test['expressions']:
                    assert expression in actual['expressions']
    return check_variation_descriptor


@pytest.fixture(scope='module')
def check_descriptor():
    """Test fixture to compare gene, therapy, and disease descriptors."""
    def check_descriptor(actual, test):
        """Check that gene, therapy, and disease descriptors match."""
        actual_keys = actual.keys()
        test_keys = test.keys()
        assert actual_keys == test_keys
        for key in test_keys:
            if key in ['id', 'type', 'label', 'description', 'value']:
                assert actual[key] == test[key]
            elif key in ['alternate_labels', 'xrefs']:
                assert set(actual[key]) == set(test[key])
    return check_descriptor


@pytest.fixture(scope='module')
def check_method():
    """Create a test fixture to compare methods."""
    def check_method(actual, test):
        """Check that methods match."""
        assert actual == test
    return check_method


@pytest.fixture(scope='module')
def check_document():
    """Create a test fixture to compare documents."""
    def check_document(actual, test):
        """Check that documents match."""
        actual_keys = actual.keys()
        test_keys = test.keys()
        assert actual_keys == test_keys
        for key in test_keys:
            assert key in actual_keys
            if key == 'xrefs':
                assert set(actual[key]) == set(test[key])
            else:
                assert actual == test
    return check_document


@pytest.fixture(scope='module')
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
            (data['statements'], statements, check_statement),
            (data['propositions'], propositions, check_proposition),
            (data['variation_descriptors'], variation_descriptors,
             check_variation_descriptor),
            (data['gene_descriptors'], gene_descriptors, check_descriptor),
            (data['disease_descriptors'], disease_descriptors,
             check_descriptor),
            (data['methods'], civic_methods, check_method),
            (data['documents'], documents, check_document)
        )

        if therapy_descriptors:
            tests += (data['therapy_descriptors'], therapy_descriptors,
                      check_descriptor),

        for t in tests:
            actual_data = t[0]
            test_data = t[1]
            test_fixture = t[2]

            assert len(actual_data) == len(test_data)
            for test in test_data:
                test_id = test['id']
                checked_id = None
                for actual in actual_data:
                    actual_id = actual['id']
                    if test_id == actual_id:
                        checked_id = actual_id
                        test_fixture(actual, test)
                assert checked_id == test_id

        os.remove(transformed_file)
    return check_transformed_cdm
