from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    chunk_size: int = 800
    chunk_overlap: int = 150
    default_k: int = 5

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()