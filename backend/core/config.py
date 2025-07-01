from pydantic_settings import BaseSettings
from enum import Enum
from typing import Optional, List, Dict
import httpx
import logging
from functools import lru_cache

class ModelEnum(str, Enum):

    GPT_O1 = "o1"
    GPT_03 = "o3"
    GPT_O1_MINI = "o1-mini"
    GPT_O3_MINI = "o3-mini"
    GPT_O4_MINI = "o4-mini"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    
    # DeepInfra models
    LLAMA_4_MAVERICK_17B_128E_INSTRUCT_FP8 = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
    LLAMA_4_SCOUT_17B_16E_INSTRUCT = "meta-llama/Llama-4-Scout-17B-16E-Instruct"
    DEEPSEEK_R1_TURBO = "deepseek-ai/DeepSeek-R1-Turbo"
    DEEPSEEK_R1 = "deepseek-ai/DeepSeek-R1"
    DEEPSEEK_V3_0324 = "deepseek-ai/DeepSeek-V3-0324"

class Settings(BaseSettings):
    openai_api_key: str = ""
    deepinfra_api_key: str = ""
    
    # Default model
    default_model: ModelEnum = ModelEnum.GPT_4

    class Config:
        env_file = ".env"

settings = Settings()

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_openai_models() -> List[str]:
    """Fetch available OpenAI text generation models dynamically.
    
    Returns:
        List of model names available on OpenAI for text generation.
        Falls back to hardcoded models if API call fails.
    """
    hardcoded_models = [
        "o1",
        "o3", 
        "o1-mini",
        "o3-mini",
        "o4-mini",
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo",
    ]
    
    if not settings.openai_api_key:
        logger.warning("No OpenAI API key provided, using hardcoded models")
        return hardcoded_models
    
    try:
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://api.openai.com/v1/models",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and isinstance(data["data"], list):
                    models = [model["id"] for model in data["data"] if "id" in model]
                    # Filter for text generation models (exclude embeddings, tts, etc.)
                    text_models = [
                        model for model in models 
                        if any(keyword in model.lower() for keyword in [
                            "gpt", "o1", "o3", "o4", "davinci", "curie", "babbage", "ada"
                        ]) and not any(exclude in model.lower() for exclude in [
                            "embed", "tts", "whisper", "dall-e", "audio", "stt"
                        ])
                    ]
                    if text_models:
                        logger.info(f"Successfully fetched {len(text_models)} OpenAI models")
                        return text_models
                    
            logger.warning(f"OpenAI API returned status {response.status_code}, using hardcoded models")
                    
    except Exception as e:
        logger.error(f"Failed to fetch OpenAI models: {e}")
    
    return hardcoded_models

@lru_cache(maxsize=1)
def get_deepinfra_models() -> List[str]:
    """Fetch available DeepInfra text generation models dynamically.
    
    Returns:
        List of model names available on DeepInfra for text generation.
        Falls back to hardcoded models if API call fails.
    """
    hardcoded_models = [
        "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "deepseek-ai/DeepSeek-R1-Turbo",
        "deepseek-ai/DeepSeek-R1",
        "deepseek-ai/DeepSeek-V3-0324",
    ]
    
    if not settings.deepinfra_api_key:
        logger.warning("No DeepInfra API key provided, using hardcoded models")
        return hardcoded_models
    
    try:
        headers = {
            "Authorization": f"Bearer {settings.deepinfra_api_key}",
            "Content-Type": "application/json"
        }
        
        # Try OpenAI-compatible models endpoint
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://api.deepinfra.com/v1/openai/models",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and isinstance(data["data"], list):
                    models = [model["id"] for model in data["data"] if "id" in model]
                    # Filter for text generation models (exclude image, audio, etc.)
                    text_models = [
                        model for model in models 
                        if any(keyword in model.lower() for keyword in [
                            "llama", "deepseek", "qwen", "mixtral", "phi", "gemma", 
                            "mistral", "codellama", "vicuna", "alpaca", "openchat"
                        ])
                    ]
                    if text_models:
                        logger.info(f"Successfully fetched {len(text_models)} DeepInfra models")
                        return text_models
                    
            logger.warning(f"DeepInfra API returned status {response.status_code}, using hardcoded models")
                    
    except Exception as e:
        logger.error(f"Failed to fetch DeepInfra models: {e}")
    
    return hardcoded_models

def get_model(model_override: Optional[ModelEnum] = None) -> str:
    """Get the model to use for a specific operation."""
    if model_override:
        return model_override.value
    return settings.default_model.value

def is_deepinfra_model(model: str) -> bool:
    """Check if the given model is a DeepInfra model."""
    # Get current list of DeepInfra models (cached)
    deepinfra_models = set(get_deepinfra_models())
    
    # Also check against hardcoded enum values for backward compatibility
    enum_models = {
        ModelEnum.LLAMA_4_MAVERICK_17B_128E_INSTRUCT_FP8.value,
        ModelEnum.LLAMA_4_SCOUT_17B_16E_INSTRUCT.value,
        ModelEnum.DEEPSEEK_R1_TURBO.value,
        ModelEnum.DEEPSEEK_R1.value,
        ModelEnum.DEEPSEEK_V3_0324.value,
    }
    
    return model in deepinfra_models or model in enum_models

def get_all_available_models() -> Dict[str, List[str]]:
    """Get all available models grouped by provider.
    
    Returns:
        Dictionary with 'openai' and 'deepinfra' keys containing model lists.
    """
    return {
        "openai": get_openai_models(),
        "deepinfra": get_deepinfra_models()
    }

def get_organized_models() -> Dict[str, Dict[str, List[str]]]:
    """Get models organized into recommended and additional categories.
    
    Returns:
        Dictionary with 'recommended' and 'additional' models for each provider.
    """
    openai_recommended = [
        "o1",
        "o3", 
        "o1-mini",
        "o3-mini",
        "o4-mini",
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo",
    ]
    
    deepinfra_recommended = [
        "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "deepseek-ai/DeepSeek-R1-Turbo",
        "deepseek-ai/DeepSeek-R1",
        "deepseek-ai/DeepSeek-V3-0324",
    ]
    
    all_openai = get_openai_models()
    all_deepinfra = get_deepinfra_models()
    
    # Filter out recommended models from the full list
    openai_additional = [model for model in all_openai if model not in openai_recommended]
    deepinfra_additional = [model for model in all_deepinfra if model not in deepinfra_recommended]
    
    return {
        "openai": {
            "recommended": [model for model in openai_recommended if model in all_openai],
            "additional": sorted(openai_additional)
        },
        "deepinfra": {
            "recommended": [model for model in deepinfra_recommended if model in all_deepinfra],
            "additional": sorted(deepinfra_additional)
        }
    }