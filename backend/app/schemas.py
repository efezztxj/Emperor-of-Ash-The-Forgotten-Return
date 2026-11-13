"""Ortak veri şemaları.

Bu dosya UE tarafıyla imzalanan sözleşmedir (contract).
`tools/unreal/echo_ai_client.py` ve Blueprint yapısı birebir bunu yansıtır.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------
# Model sağlayıcıdan BAĞIMSIZ tool tanımı
# --------------------------------------------------------------------------


class ToolSpec(BaseModel):
    """Bir yan etki (side effect) tanımı.

    `params` alanı basit bir JSON-Schema alt kümesidir. Gerçek JSON-Schema
    kullanmak da mümkün; burada kasıtlı olarak sade tutuldu ki hem OpenAI hem
    Gemini hem yerel modelin function-calling'i aynı tanımı anlayabilsin.
    """

    name: str
    description: str
    params: dict[str, Literal["string", "integer", "boolean", "number"]] = Field(
        default_factory=dict
    )
    # Oyuncunun bu çağrıyı UI'da onaylaması gerekiyor mu?
    requires_confirmation: bool = False


# --------------------------------------------------------------------------
# İstek / yanıt
# --------------------------------------------------------------------------


class Turn(BaseModel):
    role: Literal["player", "npc", "system"]
    content: str


class GameEvent(BaseModel):
    """Yerel oyun simülasyonundan gelen gerçek. Modal icat etmesin diye verilir."""

    kind: str  # örn: "player_killed_guard", "item_gained"
    detail: str = ""


class PlayerState(BaseModel):
    level: int = 1
    hp: int = 100
    max_hp: int = 100
    gold: int = 0
    inventory: list[str] = Field(default_factory=list)
    flags: dict[str, bool] = Field(default_factory=dict)


class DialogueRequest(BaseModel):
    npc_id: str
    player_message: str = Field(min_length=1, max_length=2000)

    # Sağlayıcıdan bağımsız bağlam
    locale: str = "tr"
    history: list[Turn] = Field(default_factory=list, max_length=40)
    player_state: PlayerState = Field(default_factory=PlayerState)
    world_events: list[GameEvent] = Field(default_factory=list, max_length=20)

    # Sunucu tarafı zorlamalar
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    stream: bool = False  # True -> SSE (text/event-stream)


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    provider: str = ""
    latency_ms: int = 0
    fallback_used: bool = False


class DialogueResponse(BaseModel):
    npc_id: str
    text: str
    emotion: str = "neutral"
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"] = "ok"
    provider: str
    model: str
    offline_mode: bool = False
    tool_count: int = 0
