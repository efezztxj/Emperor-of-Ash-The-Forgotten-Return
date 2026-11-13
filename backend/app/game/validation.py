"""Araç çağrılarını DOĞRULAMA katmanı.

Modelin önerdiği hiçbir şey doğrudan oyuna uygulanmaz.
Buradan geçemeyen çağrı sessizce düşer ve `rejected` listesinde geri döner,
böylece UE tarafı loglar ve dengeyi bozan bir şey olmaz.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .. import lore


@dataclass
class ValidationResult:
    accepted: list[dict[str, Any]] = field(default_factory=list)
    rejected: list[dict[str, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.rejected


def _check_args(spec: dict[str, Any], args: dict[str, Any]) -> str | None:
    """Basit tip kontrolü. Hata varsa sebep döner."""
    params: dict[str, str] = spec.get("params") or {}
    unknown = [k for k in args if k not in params]
    if unknown:
        return f"bilinmeyen parametre: {', '.join(unknown)}"
    for key, expected in params.items():
        if key not in args:
            return f"eksik parametre: {key}"
        value = args[key]
        if expected == "integer" and not isinstance(value, int):
            return f"{key} integer olmalı"
        if expected == "number" and not isinstance(value, (int, float)):
            return f"{key} number olmalı"
        if expected == "boolean" and not isinstance(value, bool):
            return f"{key} boolean olmalı"
        if expected == "string" and not isinstance(value, str):
            return f"{key} string olmalı"
    return None


def validate_tool_calls(
    calls: list[dict[str, Any]],
    player_state: Any,
    max_calls: int = 3,
) -> ValidationResult:
    result = ValidationResult()

    if not calls:
        return result
    if len(calls) > max_calls:
        result.rejected.append(
            {"name": "*", "reason": f"tek turda en fazla {max_calls} araç çağrısı"}
        )
        calls = calls[:max_calls]

    for call in calls:
        name = str(call.get("name") or "")
        args = call.get("arguments")
        if not isinstance(args, dict):
            args = {}

        spec = lore.tool_spec(name)
        if not spec:
            result.rejected.append({"name": name, "reason": "tanımsız araç (whitelist dışı)"})
            continue

        error = _check_args(spec, args)
        if error:
            result.rejected.append({"name": name, "reason": error})
            continue

        # --- Ekonomi / denge garantileri (oyun kuralları) ---
        if name == "transfer_gold":
            amount = args.get("amount", 0)
            if amount < 0 and abs(amount) > player_state.gold:
                result.rejected.append(
                    {"name": name, "reason": f"oyuncunun {player_state.gold} altını var"}
                )
                continue
            if abs(amount) > 100000:
                result.rejected.append({"name": name, "reason": "tutar sınırı aşıldı"})
                continue

        if name == "take_item":
            item = args.get("item_id")
            if item not in player_state.inventory:
                result.rejected.append(
                    {"name": name, "reason": f"envanterde yok: {item}"}
                )
                continue

        result.accepted.append(
            {
                "name": name,
                "arguments": args,
                "requires_confirmation": bool(spec.get("requires_confirmation")),
            }
        )

    return result
