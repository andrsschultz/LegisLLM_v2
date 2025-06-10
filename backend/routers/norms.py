from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
import os
from ..core.domain_logic import identify_relevant_norms
from ..core import domain_logic
from ..core.xml_parser import extract_section_from_law

router = APIRouter()

class NormRequest(BaseModel):
    task_description: str 

class NormEntry(BaseModel):
    jurabk: str
    enbez: str
    P: str
    wording: str

class NormResponse(BaseModel):
    entries: List[NormEntry]

@router.post("/identify", response_model=NormResponse)
async def identify_norms(request: NormRequest):

    raw_entries = await identify_relevant_norms(request.task_description)

    # Convert raw entries to NormEntry objects with wording
    norm_entries = []
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    
    for entry in raw_entries:
        jurabk = entry.get("jurabk", "")
        enbez = entry.get("enbez", "")
        P = entry.get("P", "")
        
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


