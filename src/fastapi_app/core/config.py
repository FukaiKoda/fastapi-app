from pydantic_settings import BaseSettings, SettingsConfigDict

from pydantic import SecretStr, HttpUrl

from functools import lru_cache

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "FastAPI App"
    LOGLEVEL: bool = False
    #Infra Config
    DATABASE_URL: str
    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    CORS_ALLOWED_ORIGINS: list[HttpUrl]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings():
    return Settings()
