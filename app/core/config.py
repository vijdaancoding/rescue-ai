from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Rescue AI Backend"
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    LIVEKIT_SIP_URI: str = ""  # e.g. sip:xxxxx.sip.livekit.cloud
    LIVEKIT_SIP_USERNAME: str = ""
    LIVEKIT_SIP_PASSWORD: str = ""

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    OPENCAGE_API_KEY: str = ""  # reverse geocoding
    GOOGLE_API_KEY: str = ""

    # Comma-separated list of allowed CORS origins; "*" for any.
    CORS_ORIGINS: str = "*"

    # SQLAlchemy connection pool sizing.
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        raw = (self.CORS_ORIGINS or "").strip()
        if raw in ("", "*"):
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


settings = Settings()
