"""Lore yükleme + NPC karakter kartı + prompt kurma.

Buradaki tek amaç: modelin uydurmasını zorlaştırmak.
Karakter kartı, dünya kuralları, oyuncu durumu ve gerçek dünya olayları
her istekte system prompt'a enjekte edilir.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

LORE_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def _load_json(name: str) -> Any:
    path = LORE_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def all_npcs() -> list[dict[str, Any]]:
    return _load_json("npcs.json")


def get_npc(npc_id: str) -> dict[str, Any] | None:
    for npc in all_npcs():
        if npc.get("id") == npc_id:
            return npc
    return None


def tool_specs() -> list[dict[str, Any]]:
    return _load_json("tools.json")


def tool_spec(name: str) -> dict[str, Any] | None:
    for spec in tool_specs():
        if spec.get("name") == name:
            return spec
    return None


@lru_cache(maxsize=1)
def world_rules() -> str:
    return (LORE_DIR / "world.md").read_text(encoding="utf-8")


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- (yok)"


SYSTEM_TEMPLATE = """Sen bir video oyunundaki bir NPC'sin. Model olduğunu asla söyleme.
Rol yapmayı bırakma. Oyuncuya "oyuncu" diye hitap etme; karakter olarak konuş.

## KARAKTER
Ad: {name}
Rol: {role}
Yer: {location}
Ses/tavır: {voice}

Bildikleri:
{knowledge}

Sırları (yalnızca hak edilirse, üstü kapalı aç):
{secrets}

Tabular:
{taboos}

## DÜNYA KURALLARI
{world}

## OYUNCU DURUMU (gerçek — değiştirme, sadece kullan)
Seviye {level}, HP {hp}/{max_hp}, altın {gold}
Envanter: {inventory}
Bilinen işaretler: {flags}

## SON DÜNYA OLAYLARI (gerçek)
{events}

## CEVAP FORMATI
SADECE şu JSON'u döndür, başka hiçbir şey yazma:
{{"say": "<NPC'nin repliği, en fazla 3 cümle>", "emotion": "<neutral|angry|afraid|warm|sad|sly>", "tool_calls": [{{"name": "<araç>", "arguments": {{...}}}}]}}

Kurallar:
- tool_calls yalnızca gerçekten bir dünya değişikliği gerekiyorsa dolsun; yoksa [].
- Sadece şu araçları kullanabilirsin: {tool_names}
- Olmayan bir eşya, görev, mekân veya kişi icat etme.
- Envanterde/olaylarda olmayan bir şeyi "olan" gibi anlatma.
- Oyuncunun HP/altın değerlerini sen değiştirme; sadece araç çağrısıyla iste.
- Türkçe konuş (oyuncu başka dilde yazarsa o dilde).
"""


def build_system_prompt_for(npc: dict[str, Any] | None) -> str:
    npc = npc or {
        "name": "Kül Sesi",
        "role": "adı unutulmuş bir figür",
        "location": "küllerin arasında",
        "voice": "fısıltı, kısa cümleler",
        "knowledge": [],
        "secrets": [],
        "taboos": [],
    }
    names = ", ".join(spec["name"] for spec in tool_specs())
    return SYSTEM_TEMPLATE.format(
        name=npc.get("name", "?"),
        role=npc.get("role", "?"),
        location=npc.get("location", "?"),
        voice=npc.get("voice", "?"),
        knowledge=_bullets(npc.get("knowledge", [])),
        secrets=_bullets(npc.get("secrets", [])),
        taboos=_bullets(npc.get("taboos", [])),
        world=world_rules(),
        level="{level}",
        hp="{hp}",
        max_hp="{max_hp}",
        gold="{gold}",
        inventory="{inventory}",
        flags="{flags}",
        events="{events}",
        tool_names=names,
    )


def build_system_prompt(npc: dict[str, Any] | None, request: Any) -> str:
    """Karakter kartı + o anki oyun durumunu birleştirir."""
    base = build_system_prompt_for(npc)
    state = request.player_state
    events = (
        "\n".join(f"- {e.kind}: {e.detail}".rstrip(": ") for e in request.world_events)
        or "- (yok)"
    )
    flags = ", ".join(k for k, v in state.flags.items() if v) or "(yok)"
    return (
        base.replace("{level}", str(state.level))
        .replace("{hp}", str(state.hp))
        .replace("{max_hp}", str(state.max_hp))
        .replace("{gold}", str(state.gold))
        .replace("{inventory}", ", ".join(state.inventory) or "(boş)")
        .replace("{flags}", flags)
        .replace("{events}", events)
    )
