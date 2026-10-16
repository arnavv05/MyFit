from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    ENVIRONMENT: str = "development"
    APP_NAME: str = "myfitness-backend"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "myfitness"
    # Separate test DB so tests never pollute Atlas data
    MONGODB_TEST_DB_NAME: str = "myfitness_test"

    # JWT
    SECRET_KEY: str = "supersecretkey_change_in_production_jwt_secret_min_32_chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # CORS – allow Vite dev-server on both hostnames
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Rate-limiting (requests per window)
    AUTH_RATE_LIMIT_REQUESTS: int = 60
    AUTH_RATE_LIMIT_SECONDS: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
