from pydantic_settings import BaseSettings
from typing import List 

class Settings(BaseSettings):
    APP_NAME : str
    GENERATION_BACKEND : str
    EMBEDDING_BACKEND : str
    OPENAI_API_KEY : str
    OPENAI_API_URL : str = None
    GENERATION_MODEL_ID_LITERAL : List[str] = None
    GENERATION_MODEL_ID : str
    EMBEDDING_MODEL_ID : str
    EMBEDDING_MODEL_SIZE : int
    INPUT_DAFAULT_MAX_CHARACTERS : int
    GENERATION_DAFAULT_MAX_TOKENS : int
    GENERATION_DAFAULT_TEMPERATURE : float
    TAVILY_API_KEY : str

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()