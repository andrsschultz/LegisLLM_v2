from fastapi import APIRouter
from ..core.guidelines import get_available_guidelines

router = APIRouter()


@router.get("/guidelines")
async def list_guidelines():
    """Return available guideline catalogs."""
    return {"guidelines": get_available_guidelines()}
