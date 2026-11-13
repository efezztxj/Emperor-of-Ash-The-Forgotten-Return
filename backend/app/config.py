"""Tek yerden ayarlar. .env dosyası veya ortam değişkenleri ile okunur."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # backend/


def _load_dotenv() -> None:
    """Bağımlılık eklememek için minik .env okuyucu."""
    path = ROOT / ".env"
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _env_bool(key: str, default: bool = False) -> bool:
    raw = _env(key).lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _env_float(key: str, default: float) -> float:
    try:
        return float(_env(key) or default)
    except ValueError:
        return default


def _env_int(key: str, default: int) -> int:
    try:
        return int(_env(key) or default)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # "openai" | "gemini" | "mock"
    provider: str = field(default_factory=lambda: _env("AI_PROVIDER", "mock").lower())

    # OpenAI-uyumlu her şey buradan geçer: OpenAI, Ollama, LM Studio, vLLM,
    # OpenRouter, Groq, DeepSeek... Sadece base_url ve model değişir.
    openai_api_key: str = field(default_factory=lambda: _env("OPENAI_API_KEY"))
    openai_base_url: str = field(
        default_factory=lambda: _env("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
    openai_model: str = field(default_factory=lambda: _env("OPENAI_MODEL", "gpt-4.1-mini"))

    # Yerel model (Ollama vb.) varsayılanları
    local_base_url: str = field(
        default_factory=lambda: _env("LOCAL_BASE_URL", "http://127.0.0.1:11434/v1")
    )
    local_model: str = field(default_factory=lambda: _env("LOCAL_MODEL", "qwen3:8b"))

    gemini_api_key: str = field(default_factory=lambda: _env("GEMINI_API_KEY"))
    gemini_model: str = field(default_factory=lambda: _env("GEMINI_MODEL", "gemini-2.5-flash"))
    gemini_base_url: str = field(
        default_factory=lambda: _env(
            "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
        )
    )

    # Davranış
    request_timeout_s: float = field(default_factory=lambda: _env_float("REQUEST_TIMEOUT_S", 30.0))
    max_output_tokens: int = field(default_factory=lambda: _env_int("MAX_OUTPUT_TOKENS", 600))
    default_temperature: float = field(
        default_factory=lambda: _env_float("DEFAULT_TEMPERATURE", 0.8)
    )
    # Ağ yoksa/anahtar yoksa sabit diyaloga düş (oyun asla kilitlenmesin)
    offline_fallback: bool = field(default_factory=lambda: _env_bool("OFFLINE_FALLBACK", True))

    # Basit günlük maliyet koruması (0 = kapalı)
    max_requests_per_minute: int = field(
        default_factory=lambda: _env_int("MAX_REQUESTS_PER_MINUTE", 60)
    )


settings = Settings()
