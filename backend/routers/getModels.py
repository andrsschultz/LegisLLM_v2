from fastapi import APIRouter
from backend.core.config import ModelEnum, is_deepinfra_model, get_all_available_models, get_organized_models

router = APIRouter()

def format_model_name(model_id: str, provider: str) -> str:
    """Format model ID into a display name."""
    if provider == "OpenAI":
        return model_id.replace("-", " ").replace("gpt", "GPT").replace("o1", "O1").replace("o3", "O3").replace("o4", "O4")
    else:  # DeepInfra
        # Extract model name from full path (e.g., "meta-llama/Llama-4-Scout" -> "Llama 4 Scout")
        name_parts = model_id.split("/")[-1]  # Get last part after "/"
        return name_parts.replace("-", " ").replace("_", " ")

@router.get("/models")
def get_available_models():
    """Return all available models and their metadata."""
    all_models = get_all_available_models()
    
    models_list = []
    
    # Add OpenAI models
    for model in all_models["openai"]:
        models_list.append({
            "id": model,
            "name": format_model_name(model, "OpenAI"),
            "provider": "OpenAI",
        })
    
    # Add DeepInfra models
    for model in all_models["deepinfra"]:
        models_list.append({
            "id": model,
            "name": format_model_name(model, "DeepInfra"),
            "provider": "DeepInfra",
        })
    
    return {
        "models": models_list,
        "default": ModelEnum.GPT_4.value,
    }

@router.get("/models/organized")
def get_organized_available_models():
    """Return models organized into recommended and additional categories."""
    organized = get_organized_models()
    
    result = {}
    
    for provider, categories in organized.items():
        result[provider] = {}
        for category, models in categories.items():
            result[provider][category] = [
                {
                    "id": model,
                    "name": format_model_name(model, provider.title()),
                    "provider": provider.title(),
                }
                for model in models
            ]
    
    return {
        "organized": result,
        "default": ModelEnum.GPT_4.value,
    }