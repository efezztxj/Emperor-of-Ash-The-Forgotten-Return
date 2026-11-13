"""Testler: kapalı ağ, mock sağlayıcı. `pytest -q` ile çalışır."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.providers.base import MockProvider, parse_model_output

client = TestClient(app)


@pytest.fixture(autouse=True)
def _mock_provider(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "mock")
    # config modülü import anında okunduğu için sağlayıcı seçimini zorluyoruz
    import app.providers as providers

    monkeypatch.setattr(providers, "build_provider", lambda name=None: (MockProvider(), "mock"))
    MockProvider.fail_next = False
    yield


def _payload(**overrides):
    base = {
        "npc_id": "ash_warden",
        "player_message": "Bu geçit nereye çıkıyor?",
        "locale": "tr",
        "history": [],
        "player_state": {
            "level": 3,
            "hp": 62,
            "max_hp": 100,
            "gold": 25,
            "inventory": ["rusty_key"],
            "flags": {},
        },
        "world_events": [{"kind": "player_entered_hall", "detail": "kuzey girişi"}],
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------
# Sağlayıcı sözleşmesi
# --------------------------------------------------------------------------


def test_parse_plain_text():
    reply = parse_model_output("Küller konuşur.")
    assert reply.text == "Küller konuşur."
    assert reply.tool_calls == []


def test_parse_fenced_json():
    raw = '```json\n{"say":"Geçit kapalı.","emotion":"sly","tool_calls":[]}\n```'
    reply = parse_model_output(raw)
    assert reply.text == "Geçit kapalı."
    assert reply.emotion == "sly"


def test_parse_json_with_tool_call():
    raw = json.dumps(
        {
            "say": "Al, hak ettin.",
            "emotion": "warm",
            "tool_calls": [{"name": "give_item", "arguments": {"item_id": "warden_key"}}],
        }
    )
    reply = parse_model_output(raw)
    assert reply.emotion == "warm"
    assert reply.tool_calls[0]["name"] == "give_item"
    assert reply.tool_calls[0]["arguments"]["item_id"] == "warden_key"


def test_parse_garbage_does_not_raise():
    reply = parse_model_output("}{ bozuk json {")
    assert isinstance(reply.text, str)


# --------------------------------------------------------------------------
# Uç noktalar
# --------------------------------------------------------------------------


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "degraded"
    assert body["tool_count"] > 0


def test_npc_list_and_detail():
    r = client.get("/v1/npcs")
    assert r.status_code == 200
    ids = [n["id"] for n in r.json()]
    assert "ash_warden" in ids

    assert client.get("/v1/npcs/ash_warden").status_code == 200
    assert client.get("/v1/npcs/yok_boyle").status_code == 404


def test_dialogue_basic():
    r = client.post("/v1/dialogue", json=_payload())
    assert r.status_code == 200
    body = r.json()
    assert body["npc_id"] == "ash_warden"
    assert body["text"]
    assert "tool_calls" in body


def test_dialogue_rejects_unknown_npc_gracefully():
    """Bilinmeyen NPC 500 değil, genel 'Kül Sesi' personası ile cevap vermeli."""
    r = client.post("/v1/dialogue", json=_payload(npc_id="hayalet"))
    assert r.status_code == 200


def test_stream_returns_sse_and_done():
    r = client.post("/v1/dialogue/stream", json=_payload(stream=True))
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    assert '"type":"done"' in r.text.replace(" ", "")
    assert "data: " in r.text


def test_missing_message_validation():
    r = client.post("/v1/dialogue", json={"npc_id": "ash_warden", "player_message": ""})
    assert r.status_code == 422
