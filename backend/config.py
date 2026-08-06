from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "BIMS"
    debug: bool = False

    database_url: str

    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    upload_folder: str = "app/uploads"
    max_upload_size: int = 10 * 1024 * 1024

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
