from pydantic import BaseModel
from typing import Optional


class Transcript(BaseModel):

    transcript_id: str

    transcript_name: Optional[str] = None

    canonical: bool = False

    biotype: Optional[str] = None

    protein_id: Optional[str] = None

    cds_length: Optional[int] = None
