from fastapi import APIRouter, Query
from typing import Optional
from ..core.models import AmendRequest, AmendEntry, AmendResponse
from ..core.domain_logic import generate_final_amendment
from ..core.config import ModelEnum, get_model

router = APIRouter()



@router.post("/amend", response_model=AmendResponse)
async def amend_law(
    request: AmendRequest,
    model: Optional[ModelEnum] = Query(None, description="LLM model to use for amendment generation")
):
    selected_model = get_model(model)
    raw_entries = await generate_final_amendment(
        task_description=request.task_description, 
        relevant_norms=request.relevant_norms,
        amendment_proposal=request.amendment_proposal,
        custom_instructions=request.custom_instructions or None,
        model=selected_model
    )
    
    entries = [
        AmendEntry(
            amendedNorm=entry.get("amendedNorm", ""),
        )
        for entry in raw_entries
    ]
    
    return AmendResponse(entries=entries)

