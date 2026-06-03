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
        model=selected_model,
        guideline_ids=request.guideline_ids,
        excluded_rule_ids=request.excluded_rule_ids
    )

    # Create mapping from proposal title to original affected norms to preserve wording
    proposal_norms_map = {
        proposal.proposalTitle: proposal.affectedNorms 
        for proposal in request.amendment_proposals
    }
    
    entries = [
        EvaluateEntry(
            proposalTitle=entry.get("proposalTitle", ""),
            affectedNorms=proposal_norms_map.get(entry.get("proposalTitle", ""), []),
            pro=entry.get("pro", []),
            contra=entry.get("contra", [])
        )
        for entry in raw_entries
    ]
    
    print("Entries after evaluation:", entries)
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
        model=selected_model,
        guideline_ids=request.guideline_ids,
        excluded_rule_ids=request.excluded_rule_ids
    )

    # Preserve original affected norms with wording from request
    original_affected_norms = request.amendment_proposal.affectedNorms
    
    entries = [
        DeepEvaluateEntry(
            proposalTitle=entry.get("proposalTitle", ""),
            affectedNorms=original_affected_norms,
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