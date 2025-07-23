from pydantic import BaseModel
from typing import List


class NormEntry(BaseModel):
    jurabk: str 
    enbez: str | None = None
    P: str | None = None
    wording: str | None = None
    amendmentDescription: str | None = None

class NormRequest(BaseModel):
    task_description: str 
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_description": "Einführung einer Freigrenze für Einnahmen aus Vermietung und Verpachtung"
                }
            ]
        }
    }

class NormResponse(BaseModel):
    entries: List[NormEntry]


class ProposalRequest(BaseModel):
    task_description: str
    relevant_norms: List[NormEntry]
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_description": "Einführung einer Freigrenze für Einnahmen aus Vermietung und Verpachtung",
                    "relevant_norms": [
                        {
                        "jurabk": "EStG",
                        "enbez": "§ 21",
                        "P": "1",
                        "wording": "Natürliche Personen, die im Inland [...]"
                        }
                    ]
                }
            ]
        }
    }



class ProposalEntry(BaseModel):
    proposalTitle: str
    description: str
    affectedNorms: List[NormEntry]

class ProposalResponse(BaseModel):
    entries: List[ProposalEntry]


class EvaluateRequest(BaseModel):
    task_description: str
    relevant_norms: List[NormEntry]
    amendment_proposals: List[ProposalEntry]

class EvaluateEntry(BaseModel):
    proposalTitle: str
    affectedNorms: List[NormEntry]
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
        Querverweise: List[NormEntry]

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
    affectedNorms: List[NormEntry]
    juristischeBeurteilung: JuristischeBeurteilung
    rechtstechnischeBeurteilung: RechtstechnischeBeurteilung
    dogmatischeBeurteilung: DogmatischeBeurteilung
    folgenabschätzung: Folgenabschätzung
    fazitProContra: FazitProContra

class DeepEvaluateResponse(BaseModel):
    entries: List[DeepEvaluateEntry]


class AmendRequest(BaseModel):
    task_description: str
    custom_instructions: str | None = None
    relevant_norms: List[NormEntry]
    amendment_proposal: ProposalEntry

class AmendEntry(BaseModel):
    originalNorm: NormEntry
    amendedNorm: NormEntry

class AmendResponse(BaseModel):
    entries: List[AmendEntry]





