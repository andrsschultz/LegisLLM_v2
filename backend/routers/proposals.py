from fastapi import APIRouter, Query, Depends
from typing import Optional
from ..core.domain_logic import develop_amendment_proposals
from ..core.models import ProposalRequest, ProposalEntry, ProposalResponse
from ..core.config import ModelEnum
from ..core.auth import verify_api_key

router = APIRouter()

@router.post("/generate_proposals", response_model=ProposalResponse)
async def generate_proposals(
    request: ProposalRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(..., description="LLM model to use for proposal generation")
):
    selected_model = model
    raw_entries = await develop_amendment_proposals(
        task_description=request.task_description,
        relevant_norms=request.relevant_norms,
        api_key=api_key,
        model=selected_model,
        guideline_ids=request.guideline_ids,
        excluded_rule_ids=request.excluded_rule_ids,
        custom_rules=request.custom_rules
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


