"""Test MOAlmanac source"""
import pytest
from metakb.harvesters.moalmanac import MOAlmanac


@pytest.fixture(scope='module')
def genes():
    """Create a list of genes."""
    moa = MOAlmanac()
    variants = moa._harvest_variants()

    return moa._harvest_genes(variants)


@pytest.fixture(scope='module')
def pik3ca():
    """Create a fixture for gene PIK3CA."""
    return {
        "name": "PIK3CA",
        "variants": [
            {
                "feature_type": "somatic_variant",
                "feature_id": 444,
                "gene": "PIK3CA",
                "chromosome": None,
                "start_position": None,
                "end_position": None,
                "reference_allele": None,
                "alternate_allele": None,
                "cdna_change": None,
                "protein_change": None,
                "variant_annotation": None,
                "exon": None,
                "rsid": None,
                "feature": "PIK3CA"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 447,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178936091.0",
                "end_position": "178936091.0",
                "reference_allele": "G",
                "alternate_allele": "C",
                "cdna_change": "c.1633G>C",
                "protein_change": "p.E545Q",
                "variant_annotation": "Missense",
                "exon": "10.0",
                "rsid": "rs104886003",
                "feature": "PIK3CA p.E545Q (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 448,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178927980.0",
                "end_position": "178927980.0",
                "reference_allele": "T",
                "alternate_allele": "C",
                "cdna_change": "c.1258T>C",
                "protein_change": "p.C420R",
                "variant_annotation": "Missense",
                "exon": "8.0",
                "rsid": "rs121913272",
                "feature": "PIK3CA p.C420R (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 449,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178936082.0",
                "end_position": "178936082.0",
                "reference_allele": "G",
                "alternate_allele": "A",
                "cdna_change": "c.1624G>A",
                "protein_change": "p.E542K",
                "variant_annotation": "Missense",
                "exon": "10.0",
                "rsid": "rs121913273",
                "feature": "PIK3CA p.E542K (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 450,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178936082.0",
                "end_position": "178936082.0",
                "reference_allele": "G",
                "alternate_allele": "C",
                "cdna_change": "c.1624G>C",
                "protein_change": "p.E542Q",
                "variant_annotation": "Missense",
                "exon": "10.0",
                "rsid": "rs121913273",
                "feature": "PIK3CA p.E542Q (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 451,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178936092.0",
                "end_position": "178936092.0",
                "reference_allele": "A",
                "alternate_allele": "C",
                "cdna_change": "c.1634A>C",
                "protein_change": "p.E545A",
                "variant_annotation": "Missense",
                "exon": "10.0",
                "rsid": "rs121913274",
                "feature": "PIK3CA p.E545A (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 452,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178936093.0",
                "end_position": "178936093.0",
                "reference_allele": "G",
                "alternate_allele": "T",
                "cdna_change": "c.1635G>T",
                "protein_change": "p.E545D",
                "variant_annotation": "Missense",
                "exon": "10.0",
                "rsid": "rs121913275",
                "feature": "PIK3CA p.E545D (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 454,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178936092.0",
                "end_position": "178936092.0",
                "reference_allele": "A",
                "alternate_allele": "G",
                "cdna_change": "c.1634A>G",
                "protein_change": "p.E545G",
                "variant_annotation": "Missense",
                "exon": "10.0",
                "rsid": "rs121913274",
                "feature": "PIK3CA p.E545G (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 455,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178936091.0",
                "end_position": "178936091.0",
                "reference_allele": "G",
                "alternate_allele": "A",
                "cdna_change": "c.1633G>A",
                "protein_change": "p.E545K",
                "variant_annotation": "Missense",
                "exon": "10.0",
                "rsid": "rs104886003",
                "feature": "PIK3CA p.E545K (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 456,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178952090.0",
                "end_position": "178952090.0",
                "reference_allele": "G",
                "alternate_allele": "C",
                "cdna_change": "c.3145G>C",
                "protein_change": "p.G1049R",
                "variant_annotation": "Missense",
                "exon": "21.0",
                "rsid": "rs121913277",
                "feature": "PIK3CA p.G1049R (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 457,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178952090.0",
                "end_position": "178952090.0",
                "reference_allele": "G",
                "alternate_allele": "A",
                "cdna_change": "c.3145G>A",
                "protein_change": "p.G1049S",
                "variant_annotation": "Missense",
                "exon": "21.0",
                "rsid": "rs121913277",
                "feature": "PIK3CA p.G1049S (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 458,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178952085.0",
                "end_position": "178952085.0",
                "reference_allele": "A",
                "alternate_allele": "T",
                "cdna_change": "c.3140A>T",
                "protein_change": "p.H1047L",
                "variant_annotation": "Missense",
                "exon": "21.0",
                "rsid": "rs121913279",
                "feature": "PIK3CA p.H1047L (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 459,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178952085.0",
                "end_position": "178952085.0",
                "reference_allele": "A",
                "alternate_allele": "G",
                "cdna_change": "c.3140A>G",
                "protein_change": "p.H1047R",
                "variant_annotation": "Missense",
                "exon": "21.0",
                "rsid": "rs121913279",
                "feature": "PIK3CA p.H1047R (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 460,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178952084.0",
                "end_position": "178952084.0",
                "reference_allele": "C",
                "alternate_allele": "T",
                "cdna_change": "c.3139C>T",
                "protein_change": "p.H1047Y",
                "variant_annotation": "Missense",
                "exon": "21.0",
                "rsid": "rs121913281",
                "feature": "PIK3CA p.H1047Y (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 461,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178938860.0",
                "end_position": "178938860.0",
                "reference_allele": "A",
                "alternate_allele": "C",
                "cdna_change": "c.2102A>C",
                "protein_change": "p.H701P",
                "variant_annotation": "Missense",
                "exon": "14.0",
                "rsid": "rs121913282",
                "feature": "PIK3CA p.H701P (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 462,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178952074.0",
                "end_position": "178952074.0",
                "reference_allele": "G",
                "alternate_allele": "A",
                "cdna_change": "c.3129G>A",
                "protein_change": "p.M1043I",
                "variant_annotation": "Missense",
                "exon": "21.0",
                "rsid": "rs121913283",
                "feature": "PIK3CA p.M1043I (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 464,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178936074.0",
                "end_position": "178936074.0",
                "reference_allele": "C",
                "alternate_allele": "G",
                "cdna_change": "c.1616C>G",
                "protein_change": "p.P539R",
                "variant_annotation": "Missense",
                "exon": "10.0",
                "rsid": "rs121913285",
                "feature": "PIK3CA p.P539R (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 465,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178936094.0",
                "end_position": "178936094.0",
                "reference_allele": "C",
                "alternate_allele": "A",
                "cdna_change": "c.1636C>A",
                "protein_change": "p.Q546K",
                "variant_annotation": "Missense",
                "exon": "10.0",
                "rsid": "rs121913286",
                "feature": "PIK3CA p.Q546K (Missense)"
            },
            {
                "feature_type": "somatic_variant",
                "feature_id": 466,
                "gene": "PIK3CA",
                "chromosome": "3",
                "start_position": "178952007.0",
                "end_position": "178952007.0",
                "reference_allele": "A",
                "alternate_allele": "G",
                "cdna_change": "c.3062A>G",
                "protein_change": "p.Y1021C",
                "variant_annotation": "Missense",
                "exon": "21.0",
                "rsid": "rs121913288",
                "feature": "PIK3CA p.Y1021C (Missense)"
            },
            {
                "feature_type": "copy_number",
                "feature_id": 741,
                "direction": "Amplification",
                "gene": "PIK3CA",
                "cytoband": None,
                "feature": "PIK3CA Amplification"
            }
        ]
    }


def test_gene_pik3ca(genes, pik3ca):
    """Test moa harvester works correctly for genes."""
    for g in genes:
        if g['name'] == "PIK3CA":
            actual = g
            break
    assert actual.keys() == pik3ca.keys()
    keys = pik3ca.keys()
    for key in keys:
        assert actual[key] == pik3ca[key]
