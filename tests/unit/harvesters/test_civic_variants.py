"""Test CIViC source"""
import pytest
from metakb.harvesters.civic import CIViC
from civicpy import civic as civicpy


@pytest.fixture(scope='module')
def civic():
    """Create a list of genes."""
    civicpy.load_cache(on_stale='ignore')
    c = CIViC()
    return c


@pytest.fixture(scope='module')
def pdgfra():
    """Create a fixture for PDGFRA variant."""
    return {
        'id': 100,
        'entrez_name': "PDGFRA",
        'entrez_id': 5156,
        'name': "D842Y",
        'description': "PDGFRA D842 mutations are characterized broadly as "
                       "imatinib resistance mutations. This is most well "
                       "characterized in gastrointestinal stromal tumors, but "
                       "other cell lines containing these mutations have been "
                       "shown to be resistant as well. In imatinib resistant "
                       "cell lines, a number of other therapeutics have "
                       "demonstrated efficacy. These include; crenolanib, "
                       "sirolimus, and midostaurin (PKC412).",
        'gene_id': 38,
        'type': "variant",
        'variant_types': [
            {
                'id': 47,
                'name': "missense_variant",
                'display_name': "Missense Variant",
                'so_id': "SO:0001583",
                'description': "A sequence variant, that changes one or more"
                               " bases, resulting in a different amino acid "
                               "sequence but where the length is preserved.",
                'url':
                    "http://www.sequenceontology.org/browser/"
                    "current_svn/term/SO:0001583"
            }
        ],
        'civic_actionability_score': 4,
        'coordinates': {
            'chromosome': "4",
            'start': 55152092,
            'stop': 55152092,
            'reference_bases': "G",
            'variant_bases': "T",
            'representative_transcript': "ENST00000257290.5",
            'chromosome2': None,
            'start2': None,
            'stop2': None,
            'representative_transcript2': None,
            'ensembl_version': 75,
            'reference_build': "GRCh37"
        },
        'evidence_items': [
            {
                'id': 45,
                'name': "EID45",
                'description': "In CHO cells with PDGFRA D842Y mutation "
                               "that have shown imatinib resistance, "
                               "crenolanib was significantly more potent "
                               "at inhibiting kinase activity than imatinib.",
                'disease': {
                    'id': 2,
                    'name': "Gastrointestinal Stromal Tumor",
                    'display_name': "Gastrointestinal Stromal Tumor",
                    'doid': "9253",
                    'url': "http://www.disease-ontology.org/?id=DOID:9253"
                },
                'drugs': [
                    {
                        'id': 21,
                        'name': "Crenolanib",
                        'ncit_id': "C64639",
                        'aliases': [
                            "PDGFR Inhibitor CP-868596",
                            "CP-868596",
                            "CP-868,596",
                            "[1-[2-[5-(3-Methyloxetan-3-ylmethoxy)benzimidazol"
                            "-1-yl]quinolin-8-yl]piperidin-4-yl]amine",
                            "4-Piperidinamine, 1-[2-[5-[(3-methyl-3-oxetanyl)"
                            "methoxy]-1Hbenzimidazol-1-yl]-8-quinolinyl]-"
                        ]
                    }
                ],
                'rating': 4,
                'evidence_level': "D",
                'evidence_type': "Predictive",
                'clinical_significance': "Sensitivity/Response",
                'evidence_direction': "Supports",
                'variant_origin': "Somatic",
                'drug_interaction_type': None,
                'status': "accepted",
                # 'open_change_count': 0,
                'type': "evidence",
                'source': {
                    'id': 80,
                    'name': "Crenolanib inhibits the drug-resistant PDGFRA "
                            "D842V mutation associated with imatinib-resistant"
                            " gastrointestinal stromal tumors.",
                    'citation': "Heinrich et al., 2012, Clin. Cancer Res.",
                    'citation_id': "22745105",
                    'source_type': "PubMed",
                    'asco_abstract_id': None,
                    'source_url':
                        "http://www.ncbi.nlm.nih.gov/pubmed/22745105",
                    'open_access': None,
                    'pmc_id': None,
                    'publication_date': {
                        'year': 2012,
                        'month': 8,
                        'day': 15
                    },
                    'journal': "Clin. Cancer Res.",
                    'full_journal_title':
                        "Clinical cancer research : an official"
                        " journal of the American Association"
                        " for Cancer Research",
                    'status': "fully curated",
                    'is_review': False,
                    'clinical_trials': []
                },
                'variant_id': 100,
                'phenotypes': []
            }
        ],
        'variant_groups': [
            {
                'id': 1,
                'name': "Imatinib Resistance",
                'description': "While imatinib has shown to be incredibly "
                               "successful in treating philadelphia chromosome"
                               " positive CML, patients that have shown "
                               "primary or secondary resistance to the drug "
                               "have been observed to harbor T315I and E255K "
                               "ABL kinase domain mutations. These mutations,"
                               " among others, have been observed both in "
                               "primary refractory disease and acquired "
                               "resistance. In gastrointestinal stromal "
                               "tumors (GIST), PDGFRA 842 mutations have "
                               "also been shown to confer resistance to"
                               " imatinib. ",
                'variants': [
                    {
                        'id': 2,
                        'entrez_name': "ABL1",
                        'entrez_id': 25,
                        'name': "BCR-ABL T315I",
                        'description': "While the efficacy of imatinib has "
                                       "revolutionized chronic myelogenous "
                                       "leukemia (CML) treatment, it is still"
                                       " not a cure-all. Both initial "
                                       "resistance and acquired resistance "
                                       "as a result of selection have been "
                                       "seen in a small subset of CML "
                                       "patients. The ABL kinase domain "
                                       "mutation T315I (aka T334I) has been "
                                       "shown to be one such mutation that"
                                       " confers resistance to imatinib. "
                                       "Second generation TKI's (dasatinib"
                                       " and ponatinib) specific to BCR-ABL"
                                       " have shown efficacy in treating "
                                       "resistant cases.",
                        'gene_id': 4,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases, "
                                               "resulting in a different amino"
                                               " acid sequence but where "
                                               "the length is preserved.",
                                'url':
                                    "http://www.sequenceontology.org/browser/"
                                    "current_svn/term/SO:0001583"
                            },
                            {
                                'id': 120,
                                'name': "transcript_fusion",
                                'display_name': "Transcript Fusion",
                                'so_id': "SO:0001886",
                                'description': "A feature fusion where the"
                                               " deletion brings together "
                                               "transcript regions.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001886"
                            }
                        ],
                        'civic_actionability_score': 146,
                        'coordinates': {
                            'chromosome': "9",
                            'start': 133748283,
                            'stop': 133748283,
                            'reference_bases': "C",
                            'variant_bases': "T",
                            'representative_transcript': "ENST00000318560.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 3,
                        'entrez_name': "ABL1",
                        'entrez_id': 25,
                        'name': "BCR-ABL E255K",
                        'description': "While the efficacy of imatinib has "
                                       "revolutionized chronic myelogenous"
                                       " leukemia (CML) treatment, it is "
                                       "still not a cure-all. Both initial"
                                       " resistance and acquired resistance"
                                       " as a result of selection have been"
                                       " seen in a small subset of CML "
                                       "patients. The ABL kinase domain "
                                       "mutation E255K has been shown to be"
                                       " one such mutation that confers "
                                       "resistance to imatinib. Second "
                                       "generation TKI's (dasatinib and "
                                       "nilotinib) specific to BCR-ABL have"
                                       " shown efficacy in treating "
                                       "resistant cases.",
                        'gene_id': 4,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases, "
                                               "resulting in a different "
                                               "amino acid sequence but where"
                                               " the length is preserved.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001583"
                            },
                            {
                                'id': 120,
                                'name': "transcript_fusion",
                                'display_name': "Transcript Fusion",
                                'so_id': "SO:0001886",
                                'description': "A feature fusion where the "
                                               "deletion brings together "
                                               "transcript regions.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001886"
                            }
                        ],
                        'civic_actionability_score': 73,
                        'coordinates': {
                            'chromosome': "9",
                            'start': 133738363,
                            'stop': 133738363,
                            'reference_bases': "G",
                            'variant_bases': "A",
                            'representative_transcript': "ENST00000318560.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 98,
                        'entrez_name': "PDGFRA",
                        'entrez_id': 5156,
                        'name': "D842I",
                        'description': "PDGFRA D842 mutations are "
                                       "characterized broadly as imatinib "
                                       "resistance mutations. This is most"
                                       " well characterized in "
                                       "gastrointestinal stromal tumors, "
                                       "but other cell lines containing "
                                       "these mutations have been shown to be"
                                       " resistant as well. In imatinib "
                                       "resistant cell lines, a number of "
                                       "other therapeutics have demonstrated"
                                       " efficacy. These include; crenolanib,"
                                       " sirolimus, and midostaurin (PKC412).",
                        'gene_id': 38,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases, "
                                               "resulting in a different "
                                               "amino acid sequence but where"
                                               " the length is preserved.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001583"
                            }
                        ],
                        'civic_actionability_score': 4,
                        'coordinates': {
                            'chromosome': "4",
                            'start': 55152092,
                            'stop': 55152093,
                            'reference_bases': "GA",
                            'variant_bases': "AT",
                            'representative_transcript': "ENST00000257290.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 99,
                        'entrez_name': "PDGFRA",
                        'entrez_id': 5156,
                        'name': "D842V",
                        'description': "PDGFRA D842 mutations are "
                                       "characterized broadly as imatinib"
                                       " resistance mutations. This is most"
                                       " well characterized in "
                                       "gastrointestinal stromal tumors, but"
                                       " other cell lines containing these "
                                       "mutations have been shown to be "
                                       "resistant as well. Exogenous "
                                       "expression of the A842V mutation"
                                       " resulted in constitutive tyrosine"
                                       " phosphorylation of PDGFRA in the "
                                       "absence of ligand in 293T cells and "
                                       "cytokine-independent proliferation "
                                       "of the IL-3-dependent Ba/F3 cell "
                                       "line, both evidence that this is an "
                                       "activating mutation. In imatinib "
                                       "resistant cell lines, a number of "
                                       "other therapeutics have demonstrated"
                                       " efficacy. These include; crenolanib,"
                                       " sirolimus, and midostaurin (PKC412).",
                        'gene_id': 38,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases,"
                                               " resulting in a different "
                                               "amino acid sequence but "
                                               "where the length is "
                                               "preserved.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001583"
                            }
                        ],
                        'civic_actionability_score': 100.5,
                        'coordinates': {
                            'chromosome': "4",
                            'start': 55152093,
                            'stop': 55152093,
                            'reference_bases': "A",
                            'variant_bases': "T",
                            'representative_transcript': "ENST00000257290.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 100,
                        'entrez_name': "PDGFRA",
                        'entrez_id': 5156,
                        'name': "D842Y",
                        'description': "PDGFRA D842 mutations are "
                                       "characterized broadly as imatinib"
                                       " resistance mutations. This is "
                                       "most well characterized in "
                                       "gastrointestinal stromal tumors, "
                                       "but other cell lines containing these"
                                       " mutations have been shown to be "
                                       "resistant as well. In imatinib "
                                       "resistant cell lines, a number of "
                                       "other therapeutics have demonstrated"
                                       " efficacy. These include; crenolanib,"
                                       " sirolimus, and midostaurin (PKC412).",
                        'gene_id': 38,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases, "
                                               "resulting in a different "
                                               "amino acid sequence but"
                                               " where the length is "
                                               "preserved.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001583"
                            }
                        ],
                        'civic_actionability_score': 4,
                        'coordinates': {
                            'chromosome': "4",
                            'start': 55152092,
                            'stop': 55152092,
                            'reference_bases': "G",
                            'variant_bases': "T",
                            'representative_transcript': "ENST00000257290.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 101,
                        'entrez_name': "PDGFRA",
                        'entrez_id': 5156,
                        'name': "I843DEL",
                        'description': "PDGFRA D842 mutations are "
                                       "characterized broadly as imatinib"
                                       " resistance mutations. This is "
                                       "most well characterized in "
                                       "gastrointestinal stromal tumors, "
                                       "but other cell lines containing "
                                       "these mutations have been shown to "
                                       "be resistant as well. In imatinib "
                                       "resistant cell lines, a number of "
                                       "other therapeutics have demonstrated "
                                       "efficacy. These include; crenolanib,"
                                       " sirolimus, and midostaurin (PKC412).",
                        'gene_id': 38,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 107,
                                'name': "inframe_deletion",
                                'display_name': "Inframe Deletion",
                                'so_id': "SO:0001822",
                                'description': "An inframe non synonymous "
                                               "variant that deletes bases "
                                               "from the coding sequence.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001822"
                            }
                        ],
                        'civic_actionability_score': 5,
                        'coordinates': {
                            'chromosome': "4",
                            'start': 55152095,
                            'stop': 55152097,
                            'reference_bases': "ATC",
                            'variant_bases': None,
                            'representative_transcript': "ENST00000257290.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 102,
                        'entrez_name': "PDGFRA",
                        'entrez_id': 5156,
                        'name': "D842_I843delinsVM",
                        'description': "PDGFRA D842 mutations are "
                                       "characterized broadly as imatinib "
                                       "resistance mutations. The "
                                       "DI842-843VM variant is the result of"
                                       " a double point mutation. This is"
                                       " most well characterized in"
                                       " gastrointestinal stromal tumors, "
                                       "but other cell lines containing "
                                       "these mutations have been shown to"
                                       " be resistant as well. In imatinib "
                                       "resistant cell lines, a number of "
                                       "other therapeutics have demonstrated"
                                       " efficacy. These include; "
                                       "crenolanib, sirolimus, and "
                                       "midostaurin (PKC412).",
                        'gene_id': 38,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases, "
                                               "resulting in a different "
                                               "amino acid sequence but "
                                               "where the length is preserved"
                                               ".",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001583"
                            }
                        ],
                        'civic_actionability_score': 4,
                        'coordinates': {
                            'chromosome': "4",
                            'start': 55152093,
                            'stop': 55152097,
                            'reference_bases': "ACATC",
                            'variant_bases': "TCATG",
                            'representative_transcript': "ENST00000257290.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 241,
                        'entrez_name': "ABL1",
                        'entrez_id': 25,
                        'name': "BCR-ABL F317L",
                        'description': "BCR-ABL F317L, like the similar "
                                       "BCR-ABL T315I mutation, is becoming "
                                       "a common clinical marker for"
                                       " resistance to front-line therapies"
                                       " in CML. It has been shown to confer"
                                       " resistance to dasatinib, but "
                                       "responds well to ponatinib and other "
                                       "second generation inhibitors.",
                        'gene_id': 4,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases,"
                                               " resulting in a different "
                                               "amino acid sequence but where"
                                               " the length is preserved.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001583"
                            },
                            {
                                'id': 120,
                                'name': "transcript_fusion",
                                'display_name': "Transcript Fusion",
                                'so_id': "SO:0001886",
                                'description': "A feature fusion where the"
                                               " deletion brings together "
                                               "transcript regions.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001886"
                            }
                        ],
                        'civic_actionability_score': 109.5,
                        'coordinates': {
                            'chromosome': "9",
                            'start': 133748288,
                            'stop': 133748288,
                            'reference_bases': "T",
                            'variant_bases': "C",
                            'representative_transcript': "ENST00000318560.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    }
                ],
                'type': "variant_group"
            }
        ],
        'assertions': [],
        'variant_aliases': [
            "ASP842TYR",
            "RS121913265"
        ],
        'hgvs_expressions': [
            "ENST00000257290.5:c.2524G>T",
            "NC_000004.11:g.55152092G>T",
            "NM_006206.5:c.2524G>T",
            "NP_006197.1:p.Asp842Tyr"
        ],
        'clinvar_entries': [
            "376250"
        ],
        'allele_registry_id': 'CA16602703'
    }


def test_variants(pdgfra, civic):
    """Test civic harvester works correctly for variants."""
    actual_pdgfra = civic._harvest_variant_by_id(100)
    assert actual_pdgfra.keys() == pdgfra.keys()
    keys = pdgfra.keys()
    for key in keys:
        if key == 'variant_aliases' or key == 'hgvs_expressions':
            assert set(actual_pdgfra[key]) == set(pdgfra[key])
        else:
            assert actual_pdgfra[key] == pdgfra[key]
