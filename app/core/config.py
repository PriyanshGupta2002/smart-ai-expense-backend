from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    CHECKPOINTER_DATABASE_URL: str
    OPENROUTER_API_KEY: str | None = None
    LANGSMITH_PROJECT: str
    LANGSMITH_API_KEY: str
    LANGSMITH_ENDPOINT: str
    LANGSMITH_TRACING: bool

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    COOKIE_SECURE: bool = False
    IMAGEKIT_PRIVATE_KEY: str
    IMAGEKIT_URL_ENDPOINT: str
    REDIS_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
