from pydantic import BaseModel
from typing import Optional


class Pocket(BaseModel):

    pocket_id: str

    score: float

    druggability: float

    volume: float

    center_x: Optional[float] = None
    center_y: Optional[float] = None
    center_z: Optional[float] = None

    size_x: Optional[float] = None
    size_y: Optional[float] = None
    size_z: Optional[float] = None

    source_file: Optional[str] = None
