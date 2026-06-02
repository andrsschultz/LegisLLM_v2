from pydantic_settings import BaseSettings
from enum import Enum
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


# Single source of truth for all available models (sorted by provider, then model name)
DEEPINFRA_MODELS = [
    "anthropic/claude-haiku-4-5",
    "anthropic/claude-opus-4-7",
    "anthropic/claude-opus-4-8",
    "anthropic/claude-sonnet-4-6",
    "deepseek-ai/DeepSeek-R1-0528",
    "deepseek-ai/DeepSeek-V3.2",
    "deepseek-ai/DeepSeek-V4-Flash",
    "deepseek-ai/DeepSeek-V4-Pro",
    "google/gemini-3.1-pro",
    "google/gemini-3.5-flash",
    "MiniMaxAI/MiniMax-M2.5",
    "moonshotai/Kimi-K2.6",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-120b-Turbo",
    "Qwen/Qwen3-32B",
    "Qwen/Qwen3.5-122B-A10B",
    "Qwen/Qwen3.5-397B-A17B",
    "Qwen/Qwen3.6-35B-A3B",
    "zai-org/GLM-4.7-Flash",
    "zai-org/GLM-5.1",
]


class ModelEnum(str, Enum):
    QWEN3_5_397B = "Qwen/Qwen3.5-397B-A17B"


class Settings(BaseSettings):
    deepinfra_api_key: str = ""

    # Default model
    default_model: ModelEnum = ModelEnum.QWEN3_5_397B

    class Config:
        env_file = ".env"

settings = Settings()


def get_deepinfra_models() -> List[str]:
    """Return the hardcoded list of available DeepInfra models."""
    return list(DEEPINFRA_MODELS)


def get_model(model_override: Optional[ModelEnum] = None) -> str:
    """Get the model to use for a specific operation."""
    if model_override:
        return model_override.value
    return settings.default_model.value


def is_deepinfra_model(model: str) -> bool:
    """Check if the given model is a DeepInfra model."""
    normalized_model = (model or "").strip()
    if not normalized_model:
        return False
    # All models are DeepInfra models now
    return True


def get_all_available_models() -> Dict[str, List[str]]:
    """Get all available models grouped by provider."""
    return {
        "deepinfra": get_deepinfra_models()
    }


def get_organized_models() -> Dict[str, Dict[str, List[str]]]:
    """Get models organized into recommended and additional categories."""
    return {
        "deepinfra": {
            "recommended": list(DEEPINFRA_MODELS),
            "additional": []
        }
    }
