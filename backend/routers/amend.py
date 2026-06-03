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
        model=selected_model,
        guideline_ids=request.guideline_ids,
        excluded_rule_ids=request.excluded_rule_ids,
        custom_rules=request.custom_rules
    )
    
    entries = []
    for entry in raw_entries:
        # Extract from amendedNorm section which now contains both original and amended wording
        amended_norm = entry.get("amendedNorm", {})
        
        # Create AmendEntry using the LLM-provided original and amended text
        entries.append(
            AmendEntry(
                originalNorm=NormEntry(
                    jurabk=amended_norm.get("jurabk", ""),
                    enbez=amended_norm.get("enbez"),
                    P=amended_norm.get("P"),
                    wording=amended_norm.get("originalWording", "")
                ),
                amendedNorm=NormEntry(
                    jurabk=amended_norm.get("jurabk", ""),
                    enbez=amended_norm.get("enbez"),
                    P=amended_norm.get("P"),
                    wording=amended_norm.get("amendedWording", "")
                )
            )
        )
    
    return AmendResponse(entries=entries)

