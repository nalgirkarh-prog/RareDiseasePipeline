from pydantic import BaseModel
from typing import Optional


class Protein(BaseModel):

    protein_id: str

    uniprot: Optional[str] = None

    sequence: Optional[str] = None

    length: Optional[int] = None

    alphafold: Optional[str] = None

    pdb_ids: list[str] = []
