from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = ""
    upstash_redis_url: str = ""
    confidence_threshold: float = 0.6

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()

app_config = get_settings()
