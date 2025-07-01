from fastapi import APIRouter, Query, Depends
from typing import Optional
from ..core.domain_logic import evaluate_proposals, deep_evaluate_proposals
from ..core.models import EvaluateRequest, EvaluateEntry, EvaluateResponse, DeepEvaluateRequest, DeepEvaluateEntry, DeepEvaluateResponse
from ..core.config import ModelEnum
from ..core.auth import verify_api_key

router = APIRouter()



@router.post("/evaluate_proposals", response_model=EvaluateResponse)
async def evaluate_proposals_endpoint(
    request: EvaluateRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(..., description="LLM model to use for evaluation")
):
    selected_model = model
    raw_entries = await evaluate_proposals(
        task_description=request.task_description, 
        relevant_norms=request.relevant_norms,
        amendment_proposals=request.amendment_proposals,
        api_key=api_key,
        model=selected_model
    )
    
    entries = [
        EvaluateEntry(
            proposalTitle=entry.get("proposalTitle", ""),
            affectedNorms=entry.get("affectedNorms", []),
            pro=entry.get("pro", []),
            contra=entry.get("contra", [])
        )
        for entry in raw_entries
    ]
    
    return EvaluateResponse(entries=entries)


@router.post("/deep_evaluate_proposals", response_model=DeepEvaluateResponse)
async def deep_evaluate_proposals_endpoint(
    request: DeepEvaluateRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(..., description="LLM model to use for evaluation")
):
    selected_model = model
    raw_entries = await deep_evaluate_proposals(
        task_description=request.task_description, 
        relevant_norms=request.relevant_norms,
        amendment_proposal=request.amendment_proposal,
        api_key=api_key,
        model=selected_model
    )
    
    entries = [
        DeepEvaluateEntry(
            proposalTitle=entry.get("proposalTitle", ""),
            affectedNorms=entry.get("affectedNorms", []),
            juristischeBeurteilung=DeepEvaluateEntry.JuristischeBeurteilung(
                Bewertung=entry.get("juristischeBeurteilung", {}).get("Bewertung", ""),
                PotentielleProbleme=entry.get("juristischeBeurteilung", {}).get("PotentielleProbleme", ""),
                Querverweise=entry.get("juristischeBeurteilung", {}).get("Querverweise", [])
            ),
            rechtstechnischeBeurteilung=DeepEvaluateEntry.RechtstechnischeBeurteilung(
                Klarheit=entry.get("rechtstechnischeBeurteilung", {}).get("Klarheit", ""),
                Formulierungsvorschlag=entry.get("rechtstechnischeBeurteilung", {}).get("Formulierungsvorschlag", ""),
                Risikopunkte=entry.get("rechtstechnischeBeurteilung", {}).get("Risikopunkte", [])
            ),
            dogmatischeBeurteilung=DeepEvaluateEntry.DogmatischeBeurteilung(
                Systematik=entry.get("dogmatischeBeurteilung", {}).get("Systematik", ""),
                Prinzipien=entry.get("dogmatischeBeurteilung", {}).get("Prinzipien", "")
            ),
            folgenabschätzung=DeepEvaluateEntry.Folgenabschätzung(
                Verwaltungsaufwand=entry.get("folgenabschätzung", {}).get("Verwaltungsaufwand", ""),
                FiskalischeAuswirkungen=entry.get("folgenabschätzung", {}).get("FiskalischeAuswirkungen", ""),
                Praktikabilität=entry.get("folgenabschätzung", {}).get("Praktikabilität", ""),
                Übergangsregelungen=entry.get("folgenabschätzung", {}).get("Übergangsregelungen", "")
            ),
            fazitProContra=DeepEvaluateEntry.FazitProContra(
                Pro=entry.get("fazitProContra", {}).get("Pro", []),
                Contra=entry.get("fazitProContra", {}).get("Contra", []),
                OffeneFragen=entry.get("fazitProContra", {}).get("OffeneFragen", [])
            )
        )
        for entry in raw_entries
    ]
    
    return DeepEvaluateResponse(entries=entries)