from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "BIMS"
    debug: bool = False

    database_url: str

    # Matches the fallback run_dev_sqlite.py already uses for zero-setup local dev —
    # kept as an explicit default (not left required) so the app never hard-crashes
    # on a platform (e.g. Railway) that hasn't set a real secret yet. Insecure by
    # name on purpose: override it before sharing any deployment publicly.
    secret_key: str = "dev-secret-key-not-for-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    upload_folder: str = "app/uploads"
    max_upload_size: int = 10 * 1024 * 1024

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
