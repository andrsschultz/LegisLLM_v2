from pydantic_settings import BaseSettings
from enum import Enum
from typing import Optional

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
    default_model: ModelEnum = ModelEnum.GPT_3_5_TURBO

    class Config:
        env_file = ".env"

settings = Settings()

def get_model(model_override: Optional[ModelEnum] = None) -> str:
    """Get the model to use for a specific operation."""
    if model_override:
        return model_override.value
    return settings.default_model.value

def is_deepinfra_model(model: str) -> bool:
    """Check if the given model is a DeepInfra model."""
    deepinfra_models = {
        ModelEnum.LLAMA_4_MAVERICK_17B_128E_INSTRUCT_FP8.value,
        ModelEnum.LLAMA_4_SCOUT_17B_16E_INSTRUCT.value,
        ModelEnum.DEEPSEEK_R1_TURBO.value,
        ModelEnum.DEEPSEEK_R1.value,
        ModelEnum.DEEPSEEK_V3_0324.value,
    }
    return model in deepinfra_models