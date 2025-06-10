from fastapi import APIRouter
from ..core.models import AmendRequest, AmendEntry, AmendResponse
from ..core.domain_logic import generate_final_amendment

router = APIRouter()



@router.post("/amend", response_model=AmendResponse)
async def amend_law(request: AmendRequest):
    raw_entries = await generate_final_amendment(
        task_description=request.task_description, 
        relevant_norms=request.relevant_norms,
        amendment_proposal=request.amendment_proposal,
        custom_instructions = request.custom_instructions or None
    )
    
    entries = [
        AmendEntry(
            amendedNorm=entry.get("amendedNorm", ""),
        )
        for entry in raw_entries
    ]
    
    return AmendResponse(entries=entries)

