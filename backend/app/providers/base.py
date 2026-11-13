"""Sağlayıcıdan bağımsız model arayüzü ve mock (test/offline) sağlayıcı."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ModelReply:
    text: str = ""
    emotion: str = "neutral"
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    provider: str = ""


class ProviderError(RuntimeError):
    """Sağlayıcı hatası — çağıran taraf fallback'e düşer."""


class Provider(Protocol):
    name: str
    model: str

    async def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> ModelReply: ...


def to_openai_tool_format(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Basit ToolSpec listesini OpenAI 'tools' formatına çevirir."""
    out: list[dict[str, Any]] = []
    for spec in specs:
        props = {k: {"type": v} for k, v in (spec.get("params") or {}).items()}
        out.append(
            {
                "type": "function",
                "function": {
                    "name": spec["name"],
                    "description": spec.get("description", ""),
                    "parameters": {
                        "type": "object",
                        "properties": props,
                        "required": list(props.keys()),
                    },
                },
            }
        )
    return out


# --------------------------------------------------------------------------
# Modelin düz metin cevabını sözleşmeye çevirme
# --------------------------------------------------------------------------

# Modeller function-calling desteklemese bile aynı sözleşmeyi üretebilsin diye
# "text protocol" kullanıyoruz. JSON'u yakalayamazsak düz metin kabul edilir.
_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def parse_model_output(raw: str) -> ModelReply:
    """Modelin ham metnini ModelReply'a çevirir. Asla exception fırlatmaz."""
    raw = (raw or "").strip()
    if not raw:
        return ModelReply(text="", emotion="neutral")

    candidate = raw
    match = _JSON_BLOCK.search(raw)
    if match:
        candidate = match.group(1)
    elif raw.startswith("{") and raw.endswith("}"):
        candidate = raw
    else:
        # Metnin içinde gömülü JSON olabilir
        start = raw.find("{")
        end = raw.rfind("}")
        candidate = raw[start : end + 1] if 0 <= start < end else ""

    if candidate:
        try:
            data = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            data = None
        if isinstance(data, dict) and ("say" in data or "tool_calls" in data):
            calls = data.get("tool_calls") or []
            if not isinstance(calls, list):
                calls = []
            clean: list[dict[str, Any]] = []
            for call in calls:
                if isinstance(call, dict) and isinstance(call.get("name"), str):
                    args = call.get("arguments")
                    clean.append(
                        {
                            "name": call["name"],
                            "arguments": args if isinstance(args, dict) else {},
                        }
                    )
            return ModelReply(
                text=str(data.get("say") or "").strip(),
                emotion=str(data.get("emotion") or "neutral").strip() or "neutral",
                tool_calls=clean,
            )

    # JSON yok: düz metin olarak kullan
    return ModelReply(text=raw, emotion="neutral")


# --------------------------------------------------------------------------
# Mock sağlayıcı: API anahtarı olmadan tüm akışı test etmek için
# --------------------------------------------------------------------------


class MockProvider:
    """Deterministik, ağsız sağlayıcı.

    Gerçek modelin sözleşmesini taklit eder: JSON + tool_call döndürür.
    Testler ve UE entegrasyon provası bununla yapılır.
    """

    name = "mock"
    model = "mock-ember-1"

    #: Test edilebilirlik için dışarıdan zorlanabilir
    fail_next: bool = False

    async def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> ModelReply:
        if MockProvider.fail_next:
            MockProvider.fail_next = False
            raise ProviderError("mock: kasıtlı hata")

        player = ""
        for msg in reversed(messages):
            if msg.get("role") == "player":
                player = msg.get("content", "")
                break

        payload = {
            "say": f"Gülümse. Konuşmak istiyorsan önce gülümse. ...Duyduğum: {player[:120]}",
            "emotion": "neutral",
            "tool_calls": [],
        }
        return ModelReply(
            text=json.dumps(payload, ensure_ascii=False),
            input_tokens=len(system) // 4,
            output_tokens=40,
            model=self.model,
            provider=self.name,
        )
