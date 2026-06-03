from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from ..core.auth import verify_api_key
from ..core.domain_logic import generate_aenderungsbefehle, generate_gesetzesentwurf_content
from ..core.models import AenderungsbefehlRequest, AenderungsbefehlResponse, GesetzesentwurfRequest, GesetzesentwurfResponse

router = APIRouter()

@router.post("/generate_aenderungsbefehle", response_model=AenderungsbefehlResponse)
async def generate_aenderungsbefehle_endpoint(
    request: AenderungsbefehlRequest, 
    api_key: str = Depends(verify_api_key),
    model: str = Query(..., description="LLM model to use for Änderungsbefehle generation")
):
    """
    Generate Änderungsbefehle from final amendments using LLM.
    First step in the legal drafting process.
    """
    try:
        # Call the domain logic function
        response = await generate_aenderungsbefehle(
            task_description=request.task_description,
            final_amendments=request.final_amendments,
            api_key=api_key,
            model=model,
            guideline_ids=request.guideline_ids,
            excluded_rule_ids=request.excluded_rule_ids
        )

        return AenderungsbefehlResponse(response=response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating Änderungsbefehle: {str(e)}")

@router.post("/generate_entwurf", response_model=GesetzesentwurfResponse)
async def generate_gesetzesentwurf_content_endpoint(
    request: GesetzesentwurfRequest, 
    api_key: str = Depends(verify_api_key),
    model: str = Query(..., description="LLM model to use for Gesetzesentwurf generation")
):
    """
    Generate Gesetzesentwurf content from Änderungsbefehle using LLM.
    Second step in the legal drafting process.
    """
    try:
        # Call the domain logic function
        response = await generate_gesetzesentwurf_content(
            task_description=request.task_description,
            aenderungsbefehle=request.aenderungsbefehle,
            api_key=api_key,
            model=model,
            final_amendments=request.final_amendments,
            guideline_ids=request.guideline_ids,
            excluded_rule_ids=request.excluded_rule_ids
        )

        return GesetzesentwurfResponse(response=response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating Gesetzesentwurf content: {str(e)}")