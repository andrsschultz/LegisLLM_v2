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


class ProposalRequest(BaseModel):
    task_description: str
    relevant_norms: List[NormEntry]

class ProposalEntry(BaseModel):
    proposalTitle: str
    description: str
    affectedNorms: List[NormReference]

class ProposalResponse(BaseModel):
    entries: List[ProposalEntry]