from pydantic import BaseModel
from typing import List


class NormEntry(BaseModel):
    jurabk: str 
    enbez: str | None = None
    P: str | None = None
    wording: str | None = None

class NormReference(BaseModel):
    jurabk: str
    enbez: str
    P: str

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


class AmendRequest(BaseModel):
    task_description: str
    custom_instructions: str | None = None
    relevant_norms: List[NormEntry]
    amendment_proposal: ProposalEntry

class AmendEntry(BaseModel):
    amendedNorm: str

class AmendResponse(BaseModel):
    entries: List[AmendEntry]


class ErfAufRequest(BaseModel):
    task_description: str
    relevant_norms: List[NormEntry]
    amendment_proposal: ProposalEntry
    amended_norms: List[AmendEntry]
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_description": "Abschaffung der Staffelung der Pendlerpauschale",
                    "relevant_norms": [
                        {
                            "jurabk": "EStG",
                            "enbez": "§ 9",
                            "P": "1",
                            "wording": "Aufwendungen des Arbeitnehmers für die Wege zwischen Wohnung und erster Tätigkeitsstätte..."
                        }
                    ],
                    "amendment_proposal": {
                        "proposalTitle": "Vereinheitlichung der Pendlerpauschale",
                        "description": "Einheitlicher Satz von 0,38 Euro ab erstem Kilometer",
                        "affectedNorms": [
                            {
                                "jurabk": "EStG",
                                "enbez": "§ 9",
                                "P": "1"
                            }
                        ]
                    },
                    "amended_norms": [
                        {
                            "amendedNorm": "§ 9 Absatz 1 Satz 8a: Ab dem Veranlagungszeitraum 2026 wird eine Entfernungspauschale von 0,38 Euro je vollem Kilometer angesetzt..."
                        }
                    ]
                }
            ]
        }
    }


class ErfAufEntry(BaseModel):
    title: str
    description: str
    cost_category: str  # "high" or "low"
    citizens_cost_eur: float
    business_cost_eur: float
    administration_cost_eur: float
    total_cost_eur: float
    full_text: str


class ErfAufResponse(BaseModel):
    entries: List[ErfAufEntry]

