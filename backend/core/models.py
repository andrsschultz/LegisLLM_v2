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


class EvaluateRequest(BaseModel):
    task_description: str
    relevant_norms: List[NormEntry]
    amendment_proposals: List[ProposalEntry]

class EvaluateEntry(BaseModel):
    proposalTitle: str
    affectedNorms: List[NormReference]
    pro: List[str]
    contra: List[str]

class EvaluateResponse(BaseModel):
    entries: List[EvaluateEntry]




class DeepEvaluateRequest(BaseModel):
    task_description: str
    relevant_norms: List[NormEntry]
    amendment_proposal: ProposalEntry

class DeepEvaluateEntry(BaseModel):
    class JuristischeBeurteilung(BaseModel):
        Bewertung: str
        PotentielleProbleme: str
        Querverweise: List[NormReference]

    class RechtstechnischeBeurteilung(BaseModel):
        Klarheit: str
        Formulierungsvorschlag: str
        Risikopunkte: List[str]

    class DogmatischeBeurteilung(BaseModel):
        Systematik: str
        Prinzipien: str

    class Folgenabschätzung(BaseModel):
        Verwaltungsaufwand: str
        FiskalischeAuswirkungen: str
        Praktikabilität: str
        Übergangsregelungen: str

    class FazitProContra(BaseModel):
        Pro: List[str]
        Contra: List[str]
        OffeneFragen: List[str]

    proposalTitle: str
    affectedNorms: List[NormReference]
    juristischeBeurteilung: JuristischeBeurteilung
    rechtstechnischeBeurteilung: RechtstechnischeBeurteilung
    dogmatischeBeurteilung: DogmatischeBeurteilung
    folgenabschätzung: Folgenabschätzung
    fazitProContra: FazitProContra

class DeepEvaluateResponse(BaseModel):
    entries: List[DeepEvaluateEntry]