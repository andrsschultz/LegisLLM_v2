from fastapi import APIRouter, Query, Depends
from typing import Optional
import os
from ..core.domain_logic import identify_relevant_norms, identify_relevant_norms_multistep
from ..core.xml_parser import extract_section_from_law
from ..core.models import NormRequest, NormEntry, NormResponse
from ..core.config import ModelEnum
from ..core.auth import verify_api_key

router = APIRouter()

@router.post("/identify", response_model=NormResponse)
async def identify_norms(
    request: NormRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(..., description="LLM model to use for norm identification")
):
    selected_model = model
    raw_entries = await identify_relevant_norms(
        task_description=request.task_description,
        api_key=api_key,
        model=selected_model
    )

    # Convert raw entries to NormEntry objects with wording
    norm_entries = []
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    
    for entry in raw_entries:
        jurabk = entry["jurabk"]
        enbez = entry["enbez"]
        P = entry.get("P")
        
        # Construct XML file path
        xml_file = os.path.join(data_dir, f"{jurabk}.xml")
        
        # Extract section number from enbez (e.g., "§ 21" -> "21")
        section_num = enbez.replace("§", "").strip()
        
        # Get the wording from XML
        wording = ""
        try:
            # Extract the entire section
            wording = extract_section_from_law(xml_file, section_num)
        except Exception as e:
            print(f"Error extracting wording for {jurabk} {enbez} P{P}: {e}")
            wording = f"Fehler beim Laden des Wortlauts für {jurabk} {enbez}"
        
        # Create NormEntry object
        norm_entry = NormEntry(
            jurabk=jurabk,
            enbez=enbez,
            P=P,
            wording=wording
        )
        norm_entries.append(norm_entry)

    return {"entries": norm_entries}

@router.post("/identify_multistep", response_model=NormResponse)
async def identify_norms_multistep(
    request: NormRequest,
    api_key: str = Depends(verify_api_key),
    model: str = Query(..., description="LLM model to use for norm identification. Breaks down identifcation taks into multiple sub-tasks to improve accuracy.")
):
    selected_model = model
    norm_entries = await identify_relevant_norms_multistep(
        task_description=request.task_description,
        api_key=api_key,
        model=selected_model
    )

    return {"entries": norm_entries}


