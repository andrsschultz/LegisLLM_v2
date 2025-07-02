from fastapi import APIRouter, Query, Depends
from typing import Optional
from ..core.models import ErfAufRequest, ErfAufEntry, ErfAufResponse
from ..core.domain_logic import identify_erfüllungsaufwand
from ..core.config import ModelEnum
from ..core.auth import verify_api_key

router = APIRouter()

@router.post("/expenditure", response_model=ErfAufResponse)
async def identify_expenditure(
    request: ErfAufRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(..., description="LLM model to use for calculation of expenditure and compliance costs")
):
    selected_model = model
    raw_entries = await identify_erfüllungsaufwand(
        task_description=request.task_description, 
        relevant_norms=request.relevant_norms, 
        amendment_proposal=request.amendment_proposal,
        amended_norms=request.amended_norms,
        api_key=api_key,
        model=selected_model
    )
    
    entries = [
        ErfAufEntry(
            title=entry.get("title", ""),
            description=entry.get("description", ""),
            cost_category=entry.get("cost_category", "low"),
            citizens_cost_eur=float(entry.get("citizens_cost_eur", 0.0)),
            business_cost_eur=float(entry.get("business_cost_eur", 0.0)),
            administration_cost_eur=float(entry.get("administration_cost_eur", 0.0)),
            total_cost_eur=float(entry.get("total_cost_eur", 0.0)),
            full_text=entry.get("full_text", "")
        )
        for entry in raw_entries
    ]
    
    return ErfAufResponse(entries=entries)

