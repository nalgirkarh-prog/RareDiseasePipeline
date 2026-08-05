from pydantic import BaseModel


class Interaction(BaseModel):

    protein: str

    score: float
