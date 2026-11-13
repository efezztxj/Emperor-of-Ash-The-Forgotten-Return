"""Araç çağrısı doğrulama testleri — oyunun dengesini bozan model çıktıları."""

from __future__ import annotations

from app.game.validation import validate_tool_calls
from app.schemas import PlayerState


def test_accepts_valid_give_item():
    result = validate_tool_calls(
        [{"name": "give_item", "arguments": {"item_id": "warden_key"}}],
        PlayerState(),
    )
    assert result.ok
    assert result.accepted[0]["name"] == "give_item"


def test_rejects_unknown_tool():
    result = validate_tool_calls(
        [{"name": "delete_save_file", "arguments": {}}], PlayerState()
    )
    assert not result.ok
    assert "whitelist" in result.rejected[0]["reason"]


def test_rejects_missing_and_unknown_params():
    missing = validate_tool_calls([{"name": "give_item", "arguments": {}}], PlayerState())
    assert not missing.ok

    extra = validate_tool_calls(
        [{"name": "give_item", "arguments": {"item_id": "x", "sneaky": 1}}], PlayerState()
    )
    assert not extra.ok


def test_rejects_wrong_type():
    result = validate_tool_calls(
        [{"name": "transfer_gold", "arguments": {"amount": "1000"}}], PlayerState()
    )
    assert not result.ok


def test_gold_guard_prevents_negative_balance():
    state = PlayerState(gold=10)
    result = validate_tool_calls(
        [{"name": "transfer_gold", "arguments": {"amount": -500}}], state
    )
    assert not result.ok


def test_gold_guard_allows_spending_within_balance():
    state = PlayerState(gold=10)
    result = validate_tool_calls(
        [{"name": "transfer_gold", "arguments": {"amount": -10}}], state
    )
    assert result.ok


def test_take_item_requires_ownership():
    state = PlayerState(inventory=["rusty_key"])
    ok = validate_tool_calls([{"name": "take_item", "arguments": {"item_id": "rusty_key"}}], state)
    assert ok.ok

    bad = validate_tool_calls([{"name": "take_item", "arguments": {"item_id": "crown"}}], state)
    assert not bad.ok


def test_confirmation_flag_is_propagated():
    result = validate_tool_calls(
        [{"name": "open_passage", "arguments": {"passage_id": "under_hall"}}], PlayerState()
    )
    assert result.ok
    assert result.accepted[0]["requires_confirmation"] is True


def test_call_count_is_capped():
    calls = [
        {"name": "give_item", "arguments": {"item_id": f"i{n}"}} for n in range(6)
    ]
    result = validate_tool_calls(calls, PlayerState(), max_calls=3)
    assert any("en fazla" in r["reason"] for r in result.rejected)
