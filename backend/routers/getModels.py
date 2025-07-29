from fastapi import APIRouter, Depends, Header
from backend.core.config import ModelEnum, is_deepinfra_model
from backend.core.auth import verify_api_key
from typing import Annotated, Optional
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def format_model_name(model_id: str, provider: str) -> str:
    """Format model ID into a display name."""
    if provider == "OpenAI":
        return model_id.replace("-", " ").replace("gpt", "GPT").replace("o1", "O1").replace("o3", "O3").replace("o4", "O4")
    else:  # DeepInfra
        # Extract model name from full path (e.g., "meta-llama/Llama-4-Scout" -> "Llama 4 Scout")
        name_parts = model_id.split("/")[-1]  # Get last part after "/"
        return name_parts.replace("-", " ").replace("_", " ")

async def fetch_openai_models(api_key: str) -> list[str]:
    """Fetch available OpenAI models using provided API key."""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and isinstance(data["data"], list):
                    models = [model["id"] for model in data["data"] if "id" in model]
                    # Filter for text generation models
                    text_models = [
                        model for model in models 
                        if any(keyword in model.lower() for keyword in [
                            "gpt", "o1", "o3", "o4", "davinci", "curie", "babbage", "ada"
                        ]) and not any(exclude in model.lower() for exclude in [
                            "embed", "tts", "whisper", "dall-e", "audio", "stt"
                        ])
                    ]
                    return text_models
                    
    except Exception as e:
        logger.error(f"Failed to fetch OpenAI models: {e}")
    
    return []

async def fetch_deepinfra_models(api_key: str) -> list[str]:
    """Fetch available DeepInfra models using provided API key."""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.deepinfra.com/v1/openai/models",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and isinstance(data["data"], list):
                    models = [model["id"] for model in data["data"] if "id" in model]
                    # Filter for text generation models
                    text_models = [
                        model for model in models 
                        if any(keyword in model.lower() for keyword in [
                            "llama", "deepseek", "qwen", "mixtral", "phi", "gemma", 
                            "mistral", "codellama", "vicuna", "alpaca", "openchat"
                        ])
                    ]
                    return text_models
                    
    except Exception as e:
        logger.error(f"Failed to fetch DeepInfra models: {e}")
    
    return []

@router.get("/models")
async def get_available_models(api_key: str = Depends(verify_api_key)):
    """Return all available models and their metadata."""
    models_list = []
    
    # Try to fetch OpenAI models with the provided API key
    openai_models = await fetch_openai_models(api_key)
    for model in openai_models:
        models_list.append({
            "id": model,
            "name": format_model_name(model, "OpenAI"),
            "provider": "OpenAI",
        })
    
    # Try to fetch DeepInfra models with the provided API key
    deepinfra_models = await fetch_deepinfra_models(api_key)
    for model in deepinfra_models:
        models_list.append({
            "id": model,
            "name": format_model_name(model, "DeepInfra"),
            "provider": "DeepInfra",
        })
    
    return {
        "models": models_list,
        "default": ModelEnum.GPT_4O.value,
    }

@router.get("/models/organized")
async def get_organized_available_models(api_key: str = Depends(verify_api_key)):
    """Return models organized into recommended and additional categories."""
    # Define recommended models
    openai_recommended = [
        "o1",
        "o3", 
        "o1-mini",
        "o3-mini",
        "o4-mini",
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4o",
        "gpt-4-turbo",
    ]
    
    deepinfra_recommended = [
        "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "deepseek-ai/DeepSeek-R1-Turbo",
        "deepseek-ai/DeepSeek-R1",
        "deepseek-ai/DeepSeek-V3-0324",
    ]
    
    # Fetch all available models
    all_openai = await fetch_openai_models(api_key)
    all_deepinfra = await fetch_deepinfra_models(api_key)
    
    # Organize models
    result = {
        "openai": {
            "recommended": [
                {
                    "id": model,
                    "name": format_model_name(model, "OpenAI"),
                    "provider": "OpenAI",
                }
                for model in openai_recommended if model in all_openai
            ],
            "additional": [
                {
                    "id": model,
                    "name": format_model_name(model, "OpenAI"),
                    "provider": "OpenAI",
                }
                for model in sorted(all_openai) if model not in openai_recommended
            ]
        },
        "deepinfra": {
            "recommended": [
                {
                    "id": model,
                    "name": format_model_name(model, "DeepInfra"),
                    "provider": "DeepInfra",
                }
                for model in deepinfra_recommended if model in all_deepinfra
            ],
            "additional": [
                {
                    "id": model,
                    "name": format_model_name(model, "DeepInfra"),
                    "provider": "DeepInfra",
                }
                for model in sorted(all_deepinfra) if model not in deepinfra_recommended
            ]
        }
    }
    
    return {
        "organized": result,
        "default": ModelEnum.GPT_4O.value,
    }