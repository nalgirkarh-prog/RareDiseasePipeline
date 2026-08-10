from pydantic import BaseModel
from typing import Optional


class DockingResult(BaseModel):

    ligand_id: str

    pocket_id: str

    affinity: Optional[float] = None

    output_file: Optional[str] = None
