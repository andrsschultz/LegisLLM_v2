from fastapi import APIRouter
from backend.core.config import ModelEnum

router = APIRouter()

@router.get("/models")
def get_available_models():
    """Return all available models and their metadata."""
    return {
        "models": [
            {"id": model.value, "name": model.name.replace("_", " ")} 
            for model in ModelEnum
        ],
        "default": ModelEnum.GPT_3_5_TURBO.value
    }