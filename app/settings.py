from __future__ import annotations

import re
from functools import lru_cache

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All comments and logs must remain in English.
    """

    # Database
    database_url: str = Field(alias="DATABASE_URL")

    # Celery broker/backends
    celery_broker_url: str = Field(alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(alias="CELERY_RESULT_BACKEND")

    # Schedules (human-friendly: e.g. 15m, 1h, 30s)
    users_every: str = Field("15m", alias="USERS_EVERY")
    enrich_addr_every: str = Field("10m", alias="ENRICH_ADDR_EVERY")
    enrich_card_every: str = Field("10m", alias="ENRICH_CARD_EVERY")
    batch_size: PositiveInt = Field(20, alias="BATCH_SIZE")

    # Data provider switch
    data_provider: str = Field("dummyjson", alias="DATA_PROVIDER")

    # External APIs
    jsonplaceholder_base_url: str = Field(
        "https://jsonplaceholder.typicode.com", alias="JSONPLACEHOLDER_BASE_URL"
    )
    random_data_api_base_url: str = Field(
        "https://random-data-api.com/api/v2", alias="RANDOM_DATA_API_BASE_URL"
    )
    dummyjson_base_url: str = Field("https://dummyjson.com", alias="DUMMYJSON_BASE_URL")

    request_timeout_seconds: PositiveInt = Field(10, alias="REQUEST_TIMEOUT_SECONDS")

    # Pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @staticmethod
    def parse_duration(text: str) -> int:
        """Parse duration like '15m', '1h', '30s' into seconds.

        Valid suffixes: s, m, h. Defaults to seconds if suffix missing.
        """
        m = re.fullmatch(r"(\d+)([smh]?)", text.strip())
        if not m:
            raise ValueError(f"Invalid duration: {text!r}")
        value = int(m.group(1))
        suffix = m.group(2) or "s"
        factor = {"s": 1, "m": 60, "h": 3600}[suffix]
        return value * factor


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
