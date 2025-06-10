from fastapi import APIRouter
from ..core.domain_logic import evaluate_proposals
from ..core.models import EvaluateRequest, EvaluateEntry, EvaluateResponse

router = APIRouter()

@router.post("/evaluate_proposals", response_model=EvaluateResponse)
async def generate_proposals(request: EvaluateRequest):
    raw_entries = await evaluate_proposals(
        task_description=request.task_description, 
        relevant_norms=request.relevant_norms,
        amendment_proposals=request.amendment_proposals
    )
    
    entries = [
        EvaluateEntry(
            proposalTitle=entry.get("proposalTitle", ""),
            affectedNorms=entry.get("affectedNorms", []),
            juristischeBeurteilung=EvaluateEntry.JuristischeBeurteilung(
                Bewertung=entry.get("juristischeBeurteilung", {}).get("Bewertung", ""),
                PotentielleProbleme=entry.get("juristischeBeurteilung", {}).get("PotentielleProbleme", ""),
                Querverweise=entry.get("juristischeBeurteilung", {}).get("Querverweise", [])
            ),
            rechtstechnischeBeurteilung=EvaluateEntry.RechtstechnischeBeurteilung(
                Klarheit=entry.get("rechtstechnischeBeurteilung", {}).get("Klarheit", ""),
                Formulierungsvorschlag=entry.get("rechtstechnischeBeurteilung", {}).get("Formulierungsvorschlag", ""),
                Risikopunkte=entry.get("rechtstechnischeBeurteilung", {}).get("Risikopunkte", [])
            ),
            dogmatischeBeurteilung=EvaluateEntry.DogmatischeBeurteilung(
                Systematik=entry.get("dogmatischeBeurteilung", {}).get("Systematik", ""),
                Prinzipien=entry.get("dogmatischeBeurteilung", {}).get("Prinzipien", "")
            ),
            folgenabschätzung=EvaluateEntry.Folgenabschätzung(
                Verwaltungsaufwand=entry.get("folgenabschätzung", {}).get("Verwaltungsaufwand", ""),
                FiskalischeAuswirkungen=entry.get("folgenabschätzung", {}).get("FiskalischeAuswirkungen", ""),
                Praktikabilität=entry.get("folgenabschätzung", {}).get("Praktikabilität", ""),
                Übergangsregelungen=entry.get("folgenabschätzung", {}).get("Übergangsregelungen", "")
            ),
            fazitProContra=EvaluateEntry.FazitProContra(
                Pro=entry.get("fazitProContra", {}).get("Pro", []),
                Contra=entry.get("fazitProContra", {}).get("Contra", []),
                OffeneFragen=entry.get("fazitProContra", {}).get("OffeneFragen", [])
            )
        )
        for entry in raw_entries
    ]
    
    return EvaluateResponse(entries=entries)