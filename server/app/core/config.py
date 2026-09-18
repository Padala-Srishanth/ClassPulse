"""
app.core.config — Application Configuration

Uses pydantic-settings to load, validate, and type every environment variable.
All configuration comes exclusively from environment variables or a .env file.
No secrets are hardcoded anywhere in this module.

Usage:
    from app.core.config import get_settings
    settings = get_settings()
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    pydantic-settings will:
      1. Read a .env file (if present)
      2. Override with actual OS environment variables
      3. Validate types and raise clear errors for missing required fields
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Silently ignore unknown env vars
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    APP_ENV: str = "development"
    APP_NAME: str = "ClassPulse API"
    APP_VERSION: str = "1.0.0"

    # -------------------------------------------------------------------------
    # Server
    # -------------------------------------------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # -------------------------------------------------------------------------
    # Firebase — Service Account Credentials
    # SECURITY: These values must come from environment variables only.
    # Never hardcode or commit these values.
    # -------------------------------------------------------------------------
    FIREBASE_PROJECT_ID: str = "classpulse-demo"
    FIREBASE_CLIENT_EMAIL: str = "demo@classpulse-demo.iam.gserviceaccount.com"
    FIREBASE_PRIVATE_KEY: str = "mock-private-key"

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    CORS_ORIGINS: str = "*"

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    LOG_LEVEL: str = "INFO"

    # -------------------------------------------------------------------------
    # Security
    # -------------------------------------------------------------------------
    HIDE_ERROR_DETAILS: bool = False

    ENABLE_DEMO_AUTH: bool = True

    # -------------------------------------------------------------------------
    # ClassPulse AI Assistant (Chatbot)
    #
    # The chatbot's intent understanding, authorization, and data retrieval are
    # ALWAYS deterministic backend logic (see app/services/chatbot/). These
    # settings only control an OPTIONAL final "phrasing" pass that makes the
    # already-computed, already-authorized response read more naturally.
    #
    # If ANTHROPIC_API_KEY is not set, the chatbot falls back to its built-in
    # template-based response generator and remains fully functional — no
    # external API key is required to use the assistant.
    #
    # SECURITY: The LLM (when enabled) never receives raw credentials, tokens,
    # or unrestricted database access — only the already-authorized, already-
    # aggregated JSON produced by the controlled chatbot tools.
    # -------------------------------------------------------------------------
    ANTHROPIC_API_KEY: str = ""
    CHATBOT_LLM_MODEL: str = "claude-haiku-4-5-20251001"

    # -------------------------------------------------------------------------
    # Computed properties
    # -------------------------------------------------------------------------

    @property
    def is_development(self) -> bool:
        """True when running in a local development environment."""
        return self.APP_ENV.lower() == "development"

    @property
    def is_production(self) -> bool:
        """True when running in production. Used to gate sensitive behaviour."""
        return self.APP_ENV.lower() == "production"

    @property
    def allow_demo_auth(self) -> bool:
        """
        True if mock/demo authentication tokens are permitted.
        Defaults to True so deployed demo/portfolio environments (e.g. Render + Vercel)
        can use demo personas and mock tokens seamlessly.
        Can be explicitly disabled by setting ENABLE_DEMO_AUTH=false in environment variables.
        """
        return self.ENABLE_DEMO_AUTH

    @property
    def chatbot_llm_enabled(self) -> bool:
        """True if the optional LLM phrasing pass should be used for chatbot replies."""
        return bool(self.ANTHROPIC_API_KEY)

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse the CORS_ORIGINS comma-separated string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def firebase_credentials_dict(self) -> dict:
        """
        Build the Firebase credentials dictionary from environment variables.

        The private key is stored as a string with literal \\n characters in
        the environment. This property normalises them to real newlines, which
        is what the Firebase Admin SDK expects.

        SECURITY: This dictionary should never be logged or returned in an API
        response. It is consumed only by firebase_admin.credentials.Certificate.
        """
        return {
            "type": "service_account",
            "project_id": self.FIREBASE_PROJECT_ID,
            "private_key": self.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
            "client_email": self.FIREBASE_CLIENT_EMAIL,
            # Additional fields required by the Certificate class:
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": (
                f"https://www.googleapis.com/robot/v1/metadata/x509/"
                f"{self.FIREBASE_CLIENT_EMAIL.replace('@', '%40')}"
            ),
        }

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got '{v}'")
        return v.upper()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the application settings singleton.

    Cached with lru_cache so that environment variables are only read and
    validated once per process lifetime — consistent with the FastAPI
    recommended pattern for dependency injection.

    Tests can clear this cache with get_settings.cache_clear() to inject
    different settings per test.
    """
    return Settings()
