from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from ..core.domain_logic import develop_amendment_proposals
from ..core.models import ProposalRequest, ProposalEntry, ProposalResponse

router = APIRouter()

@router.post("/generate_proposals", response_model=ProposalResponse)
async def generate_proposals(request: ProposalRequest):
    raw_entries = await develop_amendment_proposals(
        task_description=request.task_description, 
        relevant_norms=request.relevant_norms
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


