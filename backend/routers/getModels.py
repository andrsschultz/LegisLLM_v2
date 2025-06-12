from fastapi import APIRouter
from backend.core.config import ModelEnum, is_deepinfra_model

router = APIRouter()

@router.get("/models")
def get_available_models():
    """Return all available models and their metadata."""
    return {
        "models": [
            {
                "id": model.value, 
                "name": model.name.replace("_", " "),
                "provider": "DeepInfra" if is_deepinfra_model(model.value) else "OpenAI",
            }
            for model in ModelEnum
        ],
        "default": ModelEnum.GPT_3_5_TURBO.value,
    }