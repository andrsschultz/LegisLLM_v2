from fastapi import APIRouter, Query
from ..core.guidelines import get_available_guidelines

router = APIRouter()


@router.get("/guidelines")
async def list_guidelines(include_rules: bool = Query(False)):
    """Return available guideline catalogs, optionally with full rules."""
    return {"guidelines": get_available_guidelines(include_rules=include_rules)}
