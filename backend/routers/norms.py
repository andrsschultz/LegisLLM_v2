from fastapi import APIRouter, Query, Depends
from typing import Optional
import os
import subprocess
from pathlib import Path
from ..core.domain_logic import identify_relevant_norms, identify_relevant_norms_multistep
from ..core.xml_parser import extract_section_from_law
from ..core.models import NormRequest, NormEntry, NormResponse
from ..core.config import ModelEnum
from ..core.auth import verify_api_key
from ..core.utils import resolve_law_xml_path, get_available_laws

router = APIRouter()

def _get_laws_updated_at() -> Optional[str]:
    """Return the ISO-8601 date of the last commit in the laws submodule."""
    laws_dir = Path(__file__).parent.parent / "laws"
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI"],
            cwd=str(laws_dir),
            capture_output=True,
            text=True,
            timeout=5,
        )
        date = result.stdout.strip()
        return date if date else None
    except Exception:
        return None

@router.get("/laws")
async def list_available_laws():
    """Return sorted list of all jurabk abbreviations available in the laws index."""
    laws = get_available_laws()
    return {
        "laws": laws,
        "count": len(laws),
        "updated_at": _get_laws_updated_at(),
    }

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
        model=selected_model,
        selected_laws=request.selected_laws
    )

    # Convert raw entries to NormEntry objects with wording
    # Deduplicate by jurabk + enbez to avoid extracting the same section multiple times.
    # Step 1 intentionally works on section level only, so any model-provided paragraph
    # detail is ignored here.
    norm_entries = []
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    # Track already extracted sections to avoid duplicates
    extracted_sections = {}

    for entry in raw_entries:
        jurabk = entry["jurabk"]
        enbez = entry["enbez"]
        P = None

        # Create unique key for section
        section_key = f"{jurabk}|{enbez}"

        # Check if we already extracted this section
        if section_key in extracted_sections:
            # Reuse the already extracted wording
            wording = extracted_sections[section_key]
        else:
            # Construct XML file path
            xml_file = resolve_law_xml_path(data_dir, jurabk)

            # Extract section number from enbez (e.g., "§ 21" -> "21")
            section_num = enbez.replace("§", "").strip()

            # Get the wording from XML
            wording = ""
            try:
                # Extract the entire section
                wording = extract_section_from_law(xml_file, section_num)
                # Cache the extracted wording
                extracted_sections[section_key] = wording
            except Exception as e:
                print(f"Error extracting wording for {jurabk} {enbez} P{P}: {e}")
                wording = f"Fehler beim Laden des Wortlauts für {jurabk} {enbez}"
                extracted_sections[section_key] = wording

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
        model=selected_model,
        selected_laws=request.selected_laws
    )

    return {"entries": norm_entries}
