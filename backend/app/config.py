from typing import Annotated
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Supabase (Auth + API)
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Postgres (Alembic + direct DB access)
    database_url: str

    # OpenAI
    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    # Server
    allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        url = value.strip()
        if not url:
            raise ValueError("DATABASE_URL must not be empty.")

        parsed = urlparse(url)
        if parsed.scheme not in ("postgresql", "postgres"):
            raise ValueError(
                "DATABASE_URL must use the postgresql:// or postgres:// scheme."
            )
        if not parsed.hostname:
            raise ValueError("DATABASE_URL must include a database host.")

        if "pooler.supabase.com" in url:
            raise ValueError(
                "DATABASE_URL must use the direct Supabase connection "
                "(db.<ref>.supabase.co), not the transaction pooler "
                "(pooler.supabase.com)."
            )

        if parsed.hostname.endswith(".supabase.co") and not parsed.hostname.startswith(
            "db."
        ):
            raise ValueError(
                "DATABASE_URL must use Supabase's direct connection host "
                f"(db.<ref>.supabase.co); got {parsed.hostname!r}."
            )

        return url

    @model_validator(mode="after")
    def validate_supabase_project_refs_match(self) -> "Settings":
        supabase_ref = (
            self.supabase_url.rstrip("/").split("//")[-1].split(".")[0]
        )
        database_host = urlparse(self.database_url).hostname or ""
        database_user = urlparse(self.database_url).username or ""

        refs_match = (
            supabase_ref in database_host
            or supabase_ref in database_user
            or supabase_ref in self.database_url
        )
        if not refs_match:
            raise ValueError(
                "DATABASE_URL must target the same Supabase project as SUPABASE_URL. "
                f"Expected project ref {supabase_ref!r} in the database host or user."
            )

        return self

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return value
        return ["http://localhost:5173"]


settings = Settings()
