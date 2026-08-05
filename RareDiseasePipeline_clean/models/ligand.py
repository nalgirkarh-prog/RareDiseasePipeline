from pydantic import BaseModel
from typing import Optional


class Ligand(BaseModel):

    ligand_id: str

    name: str

    smiles: Optional[str] = None

    molecular_weight: Optional[float] = None

    logp: Optional[float] = None

    hbd: Optional[int] = None

    hba: Optional[int] = None

    rotatable_bonds: Optional[int] = None

    source: Optional[str] = None
