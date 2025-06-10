from pydantic import BaseModel
from typing import List


class NormEntry(BaseModel):
    jurabk: str
    enbez: str
    P: str
    wording: str

class NormReference(BaseModel):
    jurabk: str
    enbez: str
    P: str

class NormRequest(BaseModel):
    task_description: str 


class NormResponse(BaseModel):
    entries: List[NormEntry]
