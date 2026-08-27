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

    # --- Task 4: outbound notification channels -----------------------------
    # Every one of these is optional and defaults to "off". The application is
    # fully functional with none of them set — in-app notifications (the
    # notifications table) are always written regardless, and an unconfigured
    # or failing external channel never blocks or fails the action that
    # triggered it (see services/delivery_service.py).
    #
    # Email (SMTP). For Gmail specifically, smtp_password must be a Google
    # "App Password" (16 characters, generated at
    # https://myaccount.google.com/apppasswords with 2-Step Verification
    # enabled) — a normal account password will not authenticate.
    # Never commit real values: set these in backend/.env, which is gitignored.
    email_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
    smtp_timeout_seconds: int = 10

    # WhatsApp (Meta WhatsApp Cloud API). Requires a Meta Business account, a
    # registered phone number id, a permanent access token, and — because the
    # Cloud API only permits free-form text inside a 24-hour customer service
    # window — an approved message template for business-initiated messages.
    # See DOCUMENTATION in NOTIFICATIONS.md; nothing here is invented or
    # assumed to exist, and the feature stays disabled until configured.
    whatsapp_enabled: bool = False
    whatsapp_api_url: str = "https://graph.facebook.com/v21.0"
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_template_name: str = ""
    whatsapp_template_language: str = "en"
    whatsapp_timeout_seconds: int = 10

    # Used to build absolute links inside outbound email/WhatsApp messages, so
    # a technician can jump straight to the assignment from their inbox/phone.
    frontend_base_url: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
