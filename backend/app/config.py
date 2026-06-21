from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    upstash_redis_url: str
    confidence_threshold: float = 0.6

    class Config:
        env_file = ".env"

settings = Settings()
