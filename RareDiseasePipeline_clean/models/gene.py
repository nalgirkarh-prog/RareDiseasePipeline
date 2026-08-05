from pydantic import BaseModel, Field
from typing import List, Optional


class Gene(BaseModel):
    symbol: str
    gene_name: Optional[str] = None

    ensembl_id: Optional[str] = None
    ncbi_gene_id: Optional[str] = None

    chromosome: Optional[str] = None

    start: Optional[int] = None
    end: Optional[int] = None
    strand: Optional[int] = None

    transcripts: List[str] = Field(default_factory=list)

    proteins: List[str] = Field(default_factory=list)

    description: Optional[str] = None
