from pydantic import BaseModel
from typing import Optional


class Variant(BaseModel):

    variant_id: str

    gene: Optional[str] = None

    accession: Optional[str] = None

    hgvs_c: Optional[str] = None

    hgvs_p: Optional[str] = None

    clinical_significance: Optional[str] = None

    consequence: Optional[str] = None

    residue: Optional[int] = None
