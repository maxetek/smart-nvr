from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://smartnvr:changeme@postgres:5432/smartnvr"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # JWT
    jwt_secret_key: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Encryption
    encryption_key: str = "changeme_generate_fernet_key"

    # go2rtc
    go2rtc_api_url: str = "http://go2rtc:1984"

    # Initial admin
    initial_admin_username: str = "admin"
    initial_admin_password: str = "changeme"
    initial_admin_email: str = "admin@smartnvr.local"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # App
    app_name: str = "Smart NVR"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
