from pydantic_settings import BaseSettings
from enum import Enum
from typing import Optional

class ModelEnum(str, Enum):
    GPT_3_5 = "gpt-3.5"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"

class Settings(BaseSettings):
    openai_api_key: str = ""
    deepinfra_api_key: str = ""
    
    # Default model
    default_model: ModelEnum = ModelEnum.GPT_3_5

    class Config:
        env_file = ".env"

settings = Settings()

def get_model(model_override: Optional[ModelEnum] = None) -> str:
    """Get the model to use for a specific operation."""
    if model_override:
        return model_override.value
    return settings.default_model.value