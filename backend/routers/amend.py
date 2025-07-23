from fastapi import APIRouter, Query, Depends
from typing import Optional
from ..core.models import AmendRequest, AmendEntry, AmendResponse, NormEntry
from ..core.domain_logic import generate_final_amendment
from ..core.config import ModelEnum
from ..core.auth import verify_api_key

router = APIRouter()



@router.post("/amend", response_model=AmendResponse)
async def amend_law(
    request: AmendRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(..., description="LLM model to use for amendment generation")
):
    selected_model = model
    raw_entries = await generate_final_amendment(
        task_description=request.task_description, 
        relevant_norms=request.relevant_norms,
        amendment_proposal=request.amendment_proposal,
        api_key=api_key,
        custom_instructions=request.custom_instructions or None,
        model=selected_model
    )
    
    # Create mapping from affected norms in the proposal to preserve original wording if needed
    affected_norms_map = {
        f"{norm.jurabk}_{norm.enbez}_{norm.P}": norm 
        for norm in request.amendment_proposal.affectedNorms
    }
    
    entries = [
        AmendEntry(
            originalNorm=NormEntry(
                jurabk=entry.get("originalNorm", {}).get("jurabk", ""),
                enbez=entry.get("originalNorm", {}).get("enbez"),
                P=entry.get("originalNorm", {}).get("P"),
                wording=entry.get("originalNorm", {}).get("wording")
            ),
            amendedNorm=NormEntry(
                jurabk=entry.get("amendedNorm", {}).get("jurabk", ""),
                enbez=entry.get("amendedNorm", {}).get("enbez"),
                P=entry.get("amendedNorm", {}).get("P"),
                wording=entry.get("amendedNorm", {}).get("wording")
            )
        )
        for entry in raw_entries
    ]
    
    return AmendResponse(entries=entries)

