from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Border Verification Platform"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Supabase (or any cloud-hosted) PostgreSQL connection string, e.g.:
    #   postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
    # See README.md section "Supabase Setup" for exactly where to find this.
    DATABASE_URL: str

    # Supabase's connection pooler (PgBouncer, port 6543, "Transaction" mode) does not
    # support server-side prepared statements. Set this to true when DATABASE_URL points
    # at the pooler port so SQLAlchemy uses NullPool and disables statement caching.
    # Set to false when connecting directly to the database (port 5432).
    DB_USE_PGBOUNCER: bool = True

    # Supabase requires TLS. Kept as a setting (rather than hard-coded) so a local/test
    # database that doesn't support SSL can still be used by setting this to "disable".
    DB_SSL_MODE: str = "require"

    # Connection pool sizing for the direct (non-PgBouncer) connection case.
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    # Recycle connections periodically — cloud providers (including Supabase) will
    # silently drop idle connections, so recycling avoids stale-connection errors.
    DB_POOL_RECYCLE_SECONDS: int = 300

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: str = "http://localhost:3000"

    API_V1_PREFIX: str = "/api/v1"

    # ── ML Pipeline: file upload handling ──────────────────────────────────
    UPLOAD_DIR: str = "/tmp/border-verification-uploads"
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_UPLOAD_EXTENSIONS: str = "jpg,jpeg,png,pdf"

    # ── ML Pipeline: adapter wiring ─────────────────────────────────────────
    # Each of the five ML components is implemented independently by a teammate as a
    # concrete class satisfying the corresponding interface in app/ml/interfaces.py.
    # Set these to the dotted import path of that class once it's ready, e.g.:
    #   YOLO_ADAPTER_CLASS=app.ml.adapters.yolo_adapter.YoloDetectorAdapter
    # Left unset (empty string), the pipeline uses the scaffold stub in
    # app/ml/adapters/, which raises a clear "not implemented" error rather than
    # fabricating a result — see README "ML Integration" section.
    YOLO_ADAPTER_CLASS: str = ""
    YOLO_MODEL_PATH: str = ""

    OCR_ADAPTER_CLASS: str = ""
    OCR_MODEL_PATH: str = ""

    MRZ_ADAPTER_CLASS: str = ""

    TAMPERING_ADAPTER_CLASS: str = ""
    TAMPERING_MODEL_PATH: str = ""

    RISK_ADAPTER_CLASS: str = ""
    RISK_MODEL_PATH: str = ""

    @property
    def allowed_upload_extensions_list(self) -> List[str]:
        return [ext.strip().lower().lstrip(".") for ext in self.ALLOWED_UPLOAD_EXTENSIONS.split(",") if ext.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        """Test suite overrides DATABASE_URL to sqlite — pooling/SSL settings don't apply there."""
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
