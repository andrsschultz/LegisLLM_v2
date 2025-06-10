from fastapi import APIRouter, Query
from typing import Optional
from ..core.domain_logic import develop_amendment_proposals
from ..core.models import ProposalRequest, ProposalEntry, ProposalResponse
from ..core.config import ModelEnum, get_model

router = APIRouter()

@router.post("/generate_proposals", response_model=ProposalResponse)
async def generate_proposals(
    request: ProposalRequest,
    model: Optional[ModelEnum] = Query(None, description="LLM model to use for proposal generation")
):
    selected_model = get_model(model)
    raw_entries = await develop_amendment_proposals(
        task_description=request.task_description, 
        relevant_norms=request.relevant_norms,
        model=selected_model
    )
    
    entries = [
        ProposalEntry(
            proposalTitle=entry.get("proposalTitle", ""),
            description=entry.get("description", ""),
            affectedNorms=entry.get("affectedNorms", [])
        )
        for entry in raw_entries
    ]
    
    return ProposalResponse(entries=entries)


