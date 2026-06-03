import re

from fastapi import APIRouter, Query, UploadFile, File, Form, Depends, HTTPException
from ..core.guidelines import get_available_guidelines
from ..core.guideline_extractor import extract_rules_from_pdf
from ..core.auth import verify_api_key

router = APIRouter()


@router.get("/guidelines")
async def list_guidelines(include_rules: bool = Query(False)):
    """Return available guideline catalogs, optionally with full rules."""
    return {"guidelines": get_available_guidelines(include_rules=include_rules)}


@router.post("/guidelines/extract")
async def extract_guideline(
    file: UploadFile = File(...),
    model: str = Form(...),
    custom_name: str = Form(""),
    api_key: str = Depends(verify_api_key),
):
    """Upload a PDF and extract rules via LLM. Returns the full catalog JSON
    without persisting it on the server — the client stores it locally."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Nur PDF-Dateien werden unterstützt.")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Die Datei ist zu groß (max. 20 MB).")

    # Derive a slug-style catalog ID from the filename
    stem = file.filename.rsplit(".", 1)[0]
    catalog_id = "custom_" + re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")
    if catalog_id == "custom_":
        catalog_id = "custom"

    try:
        catalog = await extract_rules_from_pdf(
            pdf_bytes=pdf_bytes,
            api_key=api_key,
            model=model,
            catalog_id=catalog_id,
            custom_name=custom_name or None,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Regelextraktion: {str(e)}")

    return catalog
