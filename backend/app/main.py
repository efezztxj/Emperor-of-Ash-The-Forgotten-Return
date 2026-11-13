"""Kararsızlık — AI oyun backend'i.

Unreal Engine bu servisi HTTP ile çağırır. Servis modele bağımlı değildir:
aynı kod OpenAI, Claude (OpenAI-uyumlu proxy), Gemini, Ollama ya da LM Studio
ile çalışır. Anahtar sadece burada durur, oyunun içinde asla bulunmaz.
"""

from __future__ import annotations

import json
import time
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import lore
from .config import settings
from .game.ratelimit import RateLimiter
from .game.validation import validate_tool_calls
from .providers import generate
from .schemas import (
    DialogueRequest,
    DialogueResponse,
    HealthResponse,
    ToolCall,
    Usage,
)

APP_VERSION = "0.1.0"

app = FastAPI(
    title="Kararsızlık — AI Backend",
    version=APP_VERSION,
    description="NPC diyalogu, doğrulanmış araç çağrıları ve model-bağımsız sağlayıcı katmanı.",
)

# Unreal ve tarayıcı tabanlı test araçları için. Üretimde kısıtla.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = RateLimiter(settings.max_requests_per_minute)


# --------------------------------------------------------------------------
# Yardımcılar
# --------------------------------------------------------------------------


def _build_messages(req: DialogueRequest) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for turn in req.history[-20:]:
        role = "player" if turn.role == "player" else "npc"
        messages.append({"role": role, "content": turn.content})
    messages.append({"role": "player", "content": req.player_message})
    return messages


def _finalize(raw: Any, req: DialogueRequest) -> DialogueResponse:
    """Model çıktısını doğrulayıp oyuna verilebilir hale getirir."""
    validation = validate_tool_calls(raw.tool_calls, req.player_state)

    text = (raw.text or "").strip()
    if not text:
        text = "..."  # boş replik yerine sessizlik

    # JSON sözleşmesi metin olarak kaçmışsa temizle
    if text.startswith("{") and '"say"' in text:
        try:
            payload = json.loads(text)
            text = str(payload.get("say") or text)
        except json.JSONDecodeError:
            pass

    return DialogueResponse(
        npc_id=req.npc_id,
        text=text,
        emotion=raw.emotion or "neutral",
        tool_calls=[
            ToolCall(
                name=call["name"],
                arguments=call["arguments"],
                requires_confirmation=call["requires_confirmation"],
            )
            for call in validation.accepted
        ],
        usage=Usage(
            input_tokens=raw.input_tokens,
            output_tokens=raw.output_tokens,
            model=raw.model,
            provider=raw.provider,
        ),
    )


# --------------------------------------------------------------------------
# Uç noktalar
# --------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
async def index() -> Any:
    """İnsan için küçük bir durum sayfası (tarayıcıda açınca görünür)."""
    from fastapi.responses import HTMLResponse

    from .providers import build_provider

    provider, label = build_provider()
    offline = getattr(provider, "name", "") == "mock"
    state = "offline / mock" if offline else "bağlı"
    return HTMLResponse(
        f"""<!doctype html><html lang="tr"><meta charset="utf-8">
<title>Kararsızlık — AI Backend</title>
<style>
 body{{background:#0d0b0a;color:#e8dcc8;font:16px/1.6 ui-monospace,monospace;
      max-width:44rem;margin:6vh auto;padding:0 1.2rem}}
 h1{{font-weight:400;letter-spacing:.04em;border-bottom:1px solid #3a2f26;padding-bottom:.6rem}}
 code{{background:#1b1713;padding:.1rem .35rem;border-radius:3px;color:#e0b070}}
 .k{{color:#8c7a63}} .v{{color:#d8c9a8}} a{{color:#e0b070}}
</style>
<h1>Kararsızlık — AI Backend</h1>
<p class="k">sağlayıcı: <span class="v">{label}</span> · model:
<span class="v">{getattr(provider, "model", "?")}</span> · durum: <span class="v">{state}</span></p>
<p>Unreal bu servise HTTP ile bağlanır. Model burada, oyunun içinde değil.</p>
<p><a href="/docs">/docs</a> — interaktif API &nbsp;·&nbsp;
<a href="/health">/health</a> &nbsp;·&nbsp; <a href="/v1/npcs">/v1/npcs</a>
&nbsp;·&nbsp; <a href="/v1/tools">/v1/tools</a></p>
<p class="k">Gerçek model için <code>backend/.env</code>:<br>
<code>AI_PROVIDER=local</code> + <code>ollama serve</code> &nbsp;|&nbsp;
<code>AI_PROVIDER=openai</code> + <code>OPENAI_API_KEY</code></p>
</html>"""
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    from .providers import build_provider

    provider, label = build_provider()
    offline = getattr(provider, "name", "") == "mock"
    return HealthResponse(
        status="degraded" if offline else "ok",
        provider=label,
        model=getattr(provider, "model", ""),
        offline_mode=offline,
        tool_count=len(lore.tool_specs()),
    )


@app.get("/v1/npcs")
async def list_npcs() -> list[dict[str, Any]]:
    """UE tarafı karakter kartlarını buradan çekebilir (tek doğruluk kaynağı)."""
    return [
        {
            "id": npc["id"],
            "name": npc["name"],
            "role": npc.get("role", ""),
            "location": npc.get("location", ""),
            "greeting": npc.get("greeting", ""),
        }
        for npc in lore.all_npcs()
    ]


@app.get("/v1/npcs/{npc_id}")
async def get_npc(npc_id: str) -> dict[str, Any]:
    npc = lore.get_npc(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail=f"NPC bulunamadı: {npc_id}")
    return npc


@app.get("/v1/tools")
async def list_tools() -> list[dict[str, Any]]:
    return lore.tool_specs()


@app.post("/v1/dialogue", response_model=DialogueResponse)
async def dialogue(req: DialogueRequest) -> DialogueResponse:
    """Tek tur diyalog. Oyunun her zaman kullanacağı uç nokta."""
    if not limiter.allow():
        raise HTTPException(status_code=429, detail="istek sınırı aşıldı")

    npc = lore.get_npc(req.npc_id) or None
    system = lore.build_system_prompt(npc, req)
    started = time.perf_counter()

    raw, fallback_used = await generate(
        system=system,
        messages=_build_messages(req),
        tool_specs=lore.tool_specs(),
        temperature=req.temperature if req.temperature is not None else settings.default_temperature,
        max_tokens=settings.max_output_tokens,
    )

    response = _finalize(raw, req)
    response.usage.latency_ms = int((time.perf_counter() - started) * 1000)
    response.usage.fallback_used = fallback_used
    return response


@app.post("/v1/dialogue/stream")
async def dialogue_stream(req: DialogueRequest) -> StreamingResponse:
    """SSE akışı.

    Unreal tarafı `text/event-stream` okur; her olay şu formatta:
        data: {"type":"chunk","text":"..."}

    Not: Akışta araç çağrıları SONDA gelir (type="done"), çünkü model
    cümleyi bitirmeden çağrıyı kesinleştirmek riskli.
    """

    async def event_source():
        if not limiter.allow():
            yield 'data: {"type":"error","message":"rate_limited"}\n\n'
            return

        npc = lore.get_npc(req.npc_id) or None
        system = lore.build_system_prompt(npc, req)
        raw, fallback_used = await generate(
            system=system,
            messages=_build_messages(req),
            tool_specs=lore.tool_specs(),
            temperature=req.temperature
            if req.temperature is not None
            else settings.default_temperature,
            max_tokens=settings.max_output_tokens,
        )
        response = _finalize(raw, req)
        response.usage.fallback_used = fallback_used

        # Cümle öbekleri halinde gönder: TTS ve altyazı için doğal birim
        buffer = ""
        for char in response.text:
            buffer += char
            if char in ".!?…" and len(buffer) >= 12:
                yield f"data: {json.dumps({'type': 'chunk', 'text': buffer}, ensure_ascii=False)}\n\n"
                buffer = ""
        if buffer:
            yield f"data: {json.dumps({'type': 'chunk', 'text': buffer}, ensure_ascii=False)}\n\n"

        done = {
            "type": "done",
            "emotion": response.emotion,
            "tool_calls": [c.model_dump() for c in response.tool_calls],
            "usage": response.usage.model_dump(),
        }
        yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
