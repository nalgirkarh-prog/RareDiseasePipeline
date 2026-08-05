from pydantic import BaseModel
from typing import Optional


class Structure(BaseModel):

    pdb_id: Optional[str] = None

    title: Optional[str] = None

    method: Optional[str] = None

    resolution: Optional[float] = None

    file_path: Optional[str] = None
