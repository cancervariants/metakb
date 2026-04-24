"""Handle data exchange formats for ingest/loading"""

from enum import StrEnum

from ga4gh.va_spec.base import Statement
from pydantic import BaseModel


class MoaHarvestedData(BaseModel):
    """Define output for harvested data from MOA"""

    assertions: list[dict]
    sources: list[dict]


class CBioPortalStudyName(StrEnum):
    """Enumerate supported study names"""

    PPTC_2019 = "pptc_2019"
    ALL_PHASE2_TARGET_2018_PUB = "all_phase2_target_2018_pub"
    RT_TARGET_2018_PUB = "rt_target_2018_pub"
    WT_TARGET_2018_PUB = "wt_target_2018_pub"
    AML_TARGET_2018_PUB = "aml_target_2018_pub"
    NBL_TARGET_2018_PUB = "nbl_target_2018_pub"
    PEDIATRIC_DKFZ_2017 = "pediatric_dkfz_2017"
    MIXED_PIPSEQ_2017 = "mixed_pipseq_2017"
    ALL_STJUDE_2016 = "all_stjude_2016"
    ALL_STJUDE_2015 = "all_stjude_2015"
    ES_DFARBER_BROAD_2014 = "es_dfarber_broad_2014"
    ES_IOCURIE_2014 = "es_iocurie_2014"
    MBL_PCGP = "mbl_pcgp"
    PANCAN_MAPPYACTS_2022 = "pancan_mappyacts_2022"
    CHL_SCCC_2023 = "chl_sccc_2023"
    PANCAN_PDX_UTHSA_2023 = "pancan_pdx_uthsa_2023"
    LGG_CTF_SYNODOS_2025 = "lgg_ctf_synodos_2025"


class CBioPortalHarvestedStudyData(BaseModel):
    """Provide harvested data for a cBioPortal study"""

    study_name: CBioPortalStudyName
    variants: list[dict]
    patients: list[dict]
    samples: list[dict]
    metadata: list[dict]


class CBioPortalHarvestedData(BaseModel):
    """Provide harvested data for all cbioportal studies"""

    studies: list[CBioPortalHarvestedStudyData]


class TransformedData(BaseModel):
    """Define model for transformed data"""

    evidence: list[Statement] = []
    assertions: list[Statement] = []
