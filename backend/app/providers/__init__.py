"""Sağlayıcı seçimi ve yedekleme (fallback) mantığı."""

from __future__ import annotations

from ..config import settings
from .base import (
    MockProvider,
    ModelReply,
    ProviderError,
    parse_model_output,
    to_openai_tool_format,
)
from .gemini import GeminiProvider
from .openai_compatible import OpenAICompatibleProvider


def build_provider(name: str | None = None):
    """İsimden sağlayıcı üretir. Bilinmeyen/eksik ayarda mock'a düşer."""
    key = (name or settings.provider or "mock").lower()

    if key in {"openai", "openai_compatible", "cloud"}:
        if not settings.openai_api_key:
            return MockProvider(), "openai (anahtar yok -> mock)"
        return (
            OpenAICompatibleProvider(
                settings.openai_base_url, settings.openai_model, settings.openai_api_key, "openai"
            ),
            "openai",
        )

    if key in {"local", "ollama", "vllm", "lmstudio"}:
        return (
            OpenAICompatibleProvider(
                settings.local_base_url, settings.local_model, "", key
            ),
            key,
        )

    if key == "gemini":
        if not settings.gemini_api_key:
            return MockProvider(), "gemini (anahtar yok -> mock)"
        return (
            GeminiProvider(settings.gemini_api_key, settings.gemini_model, settings.gemini_base_url),
            "gemini",
        )

    if key == "openrouter":
        return (
            OpenAICompatibleProvider(
                "https://openrouter.ai/api/v1",
                settings.openai_model,
                settings.openai_api_key,
                "openrouter",
            ),
            "openrouter",
        )

    return MockProvider(), "mock"


async def generate(
    *,
    system: str,
    messages: list[dict[str, str]],
    tool_specs: list[dict],
    temperature: float,
    max_tokens: int,
    provider_name: str | None = None,
) -> tuple[ModelReply, bool]:
    """Modeli çağırır. Hata olursa mock'a düşer.

    Dönüş: (ModelReply, fallback_kullanildi_mi)
    """
    provider, label = build_provider(provider_name)
    tools = to_openai_tool_format(tool_specs)

    try:
        if isinstance(provider, MockProvider):
            raw = await provider.complete(system, messages, tools, temperature, max_tokens)
            return raw, False
        reply = await provider.complete(
            system=system,
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=settings.request_timeout_s,
        )
        # Sağlayıcı kendi tool_calls'ını verdiyse metni olduğu gibi bırak;
        # JSON sözleşmesi de kabul edilir.
        if reply.tool_calls:
            return reply, False
        parsed = parse_model_output(reply.text)
        parsed.input_tokens = reply.input_tokens
        parsed.output_tokens = reply.output_tokens
        parsed.model = reply.model
        parsed.provider = reply.provider
        if not parsed.text and reply.text:
            parsed.text = reply.text
        return parsed, False

    except ProviderError:
        if not settings.offline_fallback:
            raise
        # Ağ/anahtar sorunu: oyunu durdurma, sabit cevaba düş
        mock = MockProvider()
        fallback = ModelReply(
            text="(bağlantı yok) ...Kül sustu. Şimdilik sadece bakıyor.",
            emotion="neutral",
            model=mock.model,
            provider=f"{label}->mock",
        )
        return fallback, True
