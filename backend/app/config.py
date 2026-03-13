from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    environment: str = "development"
    secret_key: str = "change-me"
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "sqlite+aiosqlite:///./melioptimizer.db"
    database_url_sync: str = "sqlite:///./melioptimizer.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MeLi OAuth
    meli_app_id: str = ""
    meli_secret_key: str = ""
    meli_redirect_uri: str = "http://localhost:8000/auth/meli/callback"

    # Claude API
    anthropic_api_key: str = ""

    # Security
    token_encryption_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
