"""Handle data exchange formats for ingest/loading"""

from ga4gh.va_spec.base import Statement
from pydantic import BaseModel


class MoaHarvestedData(BaseModel):
    """Define output for harvested data from MOA"""

    variants: list[dict]
    genes: list[str]
    assertions: list[dict]
    sources: list[dict]


class TransformedData(BaseModel):
    """Define model for transformed data"""

    evidence: list[Statement] = []
    assertions: list[Statement] = []
