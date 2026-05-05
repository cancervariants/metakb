"""Unit tests for Transformer base helpers."""

import pytest
from cool_seq_tool.handlers import SeqRepoAccess
from cool_seq_tool.sources import TranscriptMappings
from ga4gh.cat_vrs.models import (
    CategoricalVariant,
    Constraint,
    DefiningAlleleConstraint,
)
from ga4gh.vrs import models

from metakb.repository.neo4j_models import CategoricalVariantNode
from metakb.transformers.catvars import get_normalized_protein_consequence_name


@pytest.fixture
def alleles() -> dict[str, models.Allele]:
    return {
        "ga4gh:VA.WAfO7lGIxcVaOaLL91Itjle5zd0p7Ic6": models.Allele(
            id="ga4gh:VA.WAfO7lGIxcVaOaLL91Itjle5zd0p7Ic6",
            location=models.SequenceLocation(
                id="ga4gh:SL.t-3DrWALhgLdXHsupI-e-M00aL3HgK3y",
                sequenceReference=models.SequenceReference(
                    refgetAccession="SQ.cQvw4UsHHRRlogxbWCB8W-mKD4AraM9y",
                ),
                start=599,
                end=600,
                sequence=models.sequenceString("V"),
            ),
            state=models.LiteralSequenceExpression(sequence=models.sequenceString("V")),
        ),
        "ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L": models.Allele(
            id="ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L",
            location=models.SequenceLocation(
                id="ga4gh:SL.t-3DrWALhgLdXHsupI-e-M00aL3HgK3y",
                sequenceReference=models.SequenceReference(
                    refgetAccession="SQ.cQvw4UsHHRRlogxbWCB8W-mKD4AraM9y",
                ),
                start=599,
                end=600,
                sequence=models.sequenceString("V"),
            ),
            state=models.LiteralSequenceExpression(sequence=models.sequenceString("E")),
        ),
        "ga4gh:VA.PpuS5Xbqkoat8rOHToYXl46bUX4WHTzo": models.Allele(
            id="ga4gh:VA.PpuS5Xbqkoat8rOHToYXl46bUX4WHTzo",
            location=models.SequenceLocation(
                id="ga4gh:SL.BLLY98ZhGp_60b_Qf5GW_0wQ2QJUTPic",
                sequenceReference=models.SequenceReference(
                    refgetAccession="SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE"
                ),
                start=772,
                end=773,
                sequence=models.sequenceString("H"),
            ),
            state=models.ReferenceLengthExpression(
                length=2, sequence=models.sequenceString("HH"), repeatSubunitLength=1
            ),
        ),
        "ga4gh:VA.i2mlUlU6zjxaCbKmBs2lOqxb06mHg5Xa": models.Allele(
            id="ga4gh:VA.i2mlUlU6zjxaCbKmBs2lOqxb06mHg5Xa",
            location=models.SequenceLocation(
                id="ga4gh:SL.hSdEN_wYYHQKXR7knKc7UPr_zg36wZuk",
                sequenceReference=models.SequenceReference(
                    refgetAccession="SQ.AF1UFydIo02-bMplonKSfxlWY2q6ze3m"
                ),
                start=770,
                end=775,
                sequence=models.sequenceString("AYVMA"),
            ),
            state=models.ReferenceLengthExpression(
                length=9,
                sequence=models.sequenceString("AYVMAYVMA"),
                repeatSubunitLength=4,
            ),
        ),
        "ga4gh:VA.JkqD1otgdDeZdOxpYw0T9fXEnly_2EtW": models.Allele(
            id="ga4gh:VA.JkqD1otgdDeZdOxpYw0T9fXEnly_2EtW",
            location=models.SequenceLocation(
                id="ga4gh:SL.v7153g7a-dYonPHmZ_fG9AIvYq95n1r_",
                sequenceReference=models.SequenceReference(
                    refgetAccession="SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE"
                ),
                start=746,
                end=750,
                sequence=models.sequenceString("LREA"),
            ),
            state=models.LiteralSequenceExpression(sequence=models.sequenceString("P")),
        ),
        "ga4gh:VA.DYjudLZvIA-rU6f2CK783CaO7r-jFWCu": models.Allele(
            id="ga4gh:VA.DYjudLZvIA-rU6f2CK783CaO7r-jFWCu",
            location=models.SequenceLocation(
                id="ga4gh:SL.4SCNcOJ-Jo-zr1ZmtEVErfYmbhQLLbTb",
                sequenceReference=models.SequenceReference(
                    refgetAccession="SQ.AF1UFydIo02-bMplonKSfxlWY2q6ze3m"
                ),
                start=775,
                end=776,
                sequence=models.sequenceString("G"),
            ),
            state=models.LiteralSequenceExpression(
                sequence=models.sequenceString("VC")
            ),
        ),
        "ga4gh:VA.VukKKBRCtZoy8fyUe_1PRTmx2EKzI-YC": models.Allele(
            id="ga4gh:VA.VukKKBRCtZoy8fyUe_1PRTmx2EKzI-YC",
            location=models.SequenceLocation(
                id="ga4gh:SL.DjD4VfOipktubb2HSyOlQkQnAf9PvDhw",
                sequenceReference=models.SequenceReference(
                    refgetAccession="SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE"
                ),
                start=769,
                end=770,
                sequence=models.sequenceString("D"),
            ),
            state=models.LiteralSequenceExpression(
                sequence=models.sequenceString("GY")
            ),
        ),
        "ga4gh:VA.9nu3YQ_Pi3fTdyJJEI4RBgRvMd17B_DL": models.Allele(
            id="ga4gh:VA.9nu3YQ_Pi3fTdyJJEI4RBgRvMd17B_DL",
            location=models.SequenceLocation(
                id="ga4gh:SL.eVPHw-FdCcVzbt7A3GIzFPFJRBLj66HW",
                sequenceReference=models.SequenceReference(
                    refgetAccession="SQ.TcMVFj5kDODDWpiy1d_1-3_gOf4BYaAB"
                ),
                start=578,
                end=579,
                sequence=models.sequenceString("D"),
            ),
            state=models.ReferenceLengthExpression(
                length=0, sequence=models.sequenceString(""), repeatSubunitLength=1
            ),
        ),
        "ga4gh:VA.OEk1XHnNu8vLwLfaJqg5Jwaj_MiyGUO1": models.Allele(
            id="ga4gh:VA.OEk1XHnNu8vLwLfaJqg5Jwaj_MiyGUO1",
            location=models.SequenceLocation(
                id="ga4gh:SL.tAhZYYVDMY7abXyLn20VUfhf9e4bhCM9",
                sequenceReference=models.SequenceReference(
                    refgetAccession="SQ.TcMVFj5kDODDWpiy1d_1-3_gOf4BYaAB"
                ),
                start=556,
                end=558,
                sequence=models.sequenceString("WK"),
            ),
            state=models.ReferenceLengthExpression(
                length=0, sequence=models.sequenceString(""), repeatSubunitLength=2
            ),
        ),
    }


class _DummySeqRepoAccess(SeqRepoAccess):
    def __init__(self, aliases: list[str]) -> None:
        self._aliases = aliases

    def translate_alias(self, _: str) -> tuple[list[str], None]:
        return self._aliases, None

    def translate_identifier(self, _: str) -> tuple[list[str], None]:
        return self._aliases, None

    @staticmethod
    def extract_sequence_type(alias: str) -> str | None:
        if "refseq:NP_" in alias or "refseq:XP_" in alias:
            return "p"
        return "g"


class _DummyTxMappings(TranscriptMappings):
    def __init__(self, gene_name: str | None = "BRAF") -> None:
        self.get_gene_symbol_from_refseq_protein = lambda _: gene_name
        self.get_gene_symbol_from_ensembl_protein = lambda _: gene_name


def test_get_normalized_protein_consequence_name(
    alleles: dict[str, models.Allele],
) -> None:
    allele = alleles["ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L"]
    normalized_name = get_normalized_protein_consequence_name(
        _DummySeqRepoAccess(["refseq:NP_004324.2"]), _DummyTxMappings(), allele
    )
    assert normalized_name == "BRAF V600E"


def test_psq_name_ins(alleles: dict[str, models.Allele]):
    allele = alleles["ga4gh:VA.PpuS5Xbqkoat8rOHToYXl46bUX4WHTzo"]
    normalized_name = get_normalized_protein_consequence_name(
        _DummySeqRepoAccess(["refseq:NP_005219.2"]), _DummyTxMappings("EGFR"), allele
    )
    assert normalized_name == "EGFR H773_V774insH"

    allele = alleles["ga4gh:VA.i2mlUlU6zjxaCbKmBs2lOqxb06mHg5Xa"]
    normalized_name = get_normalized_protein_consequence_name(
        _DummySeqRepoAccess(["refseq:NP_004439.2"]), _DummyTxMappings("ERBB2"), allele
    )
    assert normalized_name == "ERBB2 A775_G776insYVMA"


def test_get_psq_name_delins(alleles: dict[str, models.Allele]) -> None:
    allele = alleles["ga4gh:VA.JkqD1otgdDeZdOxpYw0T9fXEnly_2EtW"]
    normalized_name = get_normalized_protein_consequence_name(
        _DummySeqRepoAccess(["refseq:NP_005219.2"]), _DummyTxMappings("EGFR"), allele
    )
    assert normalized_name == "EGFR L747_A750delinsP"

    allele = alleles["ga4gh:VA.DYjudLZvIA-rU6f2CK783CaO7r-jFWCu"]
    normalized_name = get_normalized_protein_consequence_name(
        _DummySeqRepoAccess(["refseq:NP_004439.2"]), _DummyTxMappings("ERBB2"), allele
    )
    assert normalized_name == "ERBB2 G776delinsVC"

    allele = alleles["ga4gh:VA.VukKKBRCtZoy8fyUe_1PRTmx2EKzI-YC"]
    normalized_name = get_normalized_protein_consequence_name(
        _DummySeqRepoAccess(["refseq:NP_005219.2"]), _DummyTxMappings("EGFR"), allele
    )
    assert normalized_name == "EGFR D770delinsGY"


def test_psq_name_del(alleles: dict[str, models.Allele]):
    allele = alleles["ga4gh:VA.9nu3YQ_Pi3fTdyJJEI4RBgRvMd17B_DL"]
    normalized_name = get_normalized_protein_consequence_name(
        _DummySeqRepoAccess(["refseq:NP_000213.1"]), _DummyTxMappings("KIT"), allele
    )
    assert normalized_name == "KIT D579del"

    allele = alleles["ga4gh:VA.OEk1XHnNu8vLwLfaJqg5Jwaj_MiyGUO1"]
    normalized_name = get_normalized_protein_consequence_name(
        _DummySeqRepoAccess(["refseq:NP_000213.1"]), _DummyTxMappings("KIT"), allele
    )
    assert normalized_name == "KIT W557_K558del"


def test_categorical_variant_node_uses_normalized_name_for_name(
    alleles: dict[str, models.Allele],
) -> None:
    allele = alleles["ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L"]
    cv = CategoricalVariant(
        id="civic.mpid:1",
        name="BRAF V600E",
        constraints=[Constraint(root=DefiningAlleleConstraint(allele=allele))],
    )
    cv_node = CategoricalVariantNode.from_gks(cv)
    assert cv_node.name == "BRAF V600E"
