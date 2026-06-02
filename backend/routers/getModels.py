from fastapi import APIRouter, Depends
from backend.core.config import ModelEnum, get_deepinfra_models, get_organized_models
from backend.core.auth import verify_api_key

router = APIRouter()


def format_model_name(model_id: str) -> str:
    """Format model ID into a display name."""
    name_parts = model_id.split("/")[-1]
    return name_parts.replace("-", " ").replace("_", " ")


@router.get("/models")
async def get_available_models(api_key: str = Depends(verify_api_key)):
    """Return all available models and their metadata."""
    models_list = [
        {
            "id": model,
            "name": format_model_name(model),
            "provider": "DeepInfra",
        }
        for model in get_deepinfra_models()
    ]

    return {
        "models": models_list,
        "default": ModelEnum.QWEN3_5_397B.value,
    }


@router.get("/models/organized")
async def get_organized_available_models(api_key: str = Depends(verify_api_key)):
    """Return models organized into recommended and additional categories."""
    organized = get_organized_models()

    result = {
        "deepinfra": {
            "recommended": [
                {"id": m, "name": format_model_name(m), "provider": "DeepInfra"}
                for m in organized["deepinfra"]["recommended"]
            ],
            "additional": [],
        }
    }

    return {
        "organized": result,
        "default": ModelEnum.QWEN3_5_397B.value,
    }
