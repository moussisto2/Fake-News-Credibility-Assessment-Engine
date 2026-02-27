from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


def _to_bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def _to_int(v: str | None, default: int) -> int:
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    raison_api_key: str
    raison_execution_url: str
    raison_timeout_seconds: int
    app_debug: bool


def load_settings() -> Settings:
    load_dotenv()

    api_key = os.getenv("RAISON_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing RAISON_API_KEY. Put it in the .env file at project root.")

    execution_url = os.getenv("RAISON_EXECUTION_URL", "").strip()
    if not execution_url:
        raise RuntimeError(
            "Missing RAISON_EXECUTION_URL. Put the full URL in .env, "
            "e.g. https://api.ai-raison.com/executions/PRJ29925/latest"
        )

    timeout_seconds = _to_int(os.getenv("RAISON_TIMEOUT_SECONDS"), default=20)
    app_debug = _to_bool(os.getenv("APP_DEBUG"), default=False)

    return Settings(
        raison_api_key=api_key,
        raison_execution_url=execution_url.rstrip("/"),
        raison_timeout_seconds=timeout_seconds,
        app_debug=app_debug,
    )
