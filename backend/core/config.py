from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = ""
    deepinfra_api_key: str = ""
    
    #TBD
    model: str = "gpt-3.5-turbo"

    class Config:
        env_file = ".env"

settings = Settings()