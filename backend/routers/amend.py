from fastapi import APIRouter, Query, Depends
from typing import Optional
from ..core.models import AmendRequest, AmendEntry, AmendResponse, NormEntry
from ..core.domain_logic import generate_final_amendment
from ..core.config import ModelEnum
from ..core.auth import verify_api_key
import os
from ..core.xml_parser import extract_section_from_law

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
    
    entries = []
    for entry in raw_entries:
        jurabk = entry.get("amendedNorm", {}).get("jurabk", "")
        enbez = entry.get("amendedNorm", {}).get("enbez")
        P = entry.get("amendedNorm", {}).get("P")
        amendedWording = entry.get("amendedNorm", {}).get("wording")

        # Get the original wording from XML
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        xml_file = os.path.join(data_dir, f"{jurabk}.xml")
        
        # Parse section number from enbez (handle formats like "§ 3", "§ 3 Abs. 1", etc.)
        section_num = enbez.replace("§", "").strip()
        if " Abs." in section_num:
            # Extract just the section number before "Abs."
            section_num = section_num.split(" Abs.")[0].strip()

        originalWording = ""
        try:
            originalWording = extract_section_from_law(xml_file, section_num, P)
        except Exception as e:
            print(f"Error extracting wording for {jurabk} {enbez} P{P}: {e}")
            originalWording = f"Fehler beim Laden des Wortlauts für {jurabk} {enbez}"

        entries.append(
            AmendEntry(
                originalNorm=NormEntry(
                    jurabk=jurabk,
                    enbez=enbez,
                    P=P,
                    wording=originalWording
                ),
                amendedNorm=NormEntry(
                    jurabk=jurabk,
                    enbez=enbez,
                    P=P,
                    wording=amendedWording
                )
            )
        )
    
    return AmendResponse(entries=entries)

