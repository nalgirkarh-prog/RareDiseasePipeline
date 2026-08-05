from pydantic import BaseModel
from typing import Optional


class Disease(BaseModel):

    name: str

    gene_symbol: Optional[str] = None

    omim_id: Optional[str] = None

    medgen_id: Optional[str] = None

    inheritance: Optional[str] = None
