"""UE bağlantısının Python karşılığı — sözleşmeyi canlı test etmek için.

Bu dosya Unreal tarafındaki `AshAIClient` sınıfının birebir aynısıdır:
aynı endpoint, aynı JSON, aynı alanlar. Unreal'da plugin açmadan önce
buradan akışı doğrulayabilirsin.

Kullanım:
    python tools/unreal/echo_ai_client.py
    python tools/unreal/echo_ai_client.py --base-url http://localhost:8000 --npc mira_the_sutler
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "http://127.0.0.1:8000"


class AshAIClient:
    """UE tarafındaki sınıfla aynı yüzey. Senkron, bağımlılıksız."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # --- düşük seviye -----------------------------------------------------
    def _post(self, path: str, payload: dict) -> dict:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _get(self, path: str) -> dict | list:
        with urllib.request.urlopen(f"{self.base_url}{path}", timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # --- yüksek seviye (Blueprint node karşılıkları) ----------------------
    def health(self) -> dict:
        return self._get("/health")  # type: ignore[return-value]

    def list_npcs(self) -> list[dict]:
        return self._get("/v1/npcs")  # type: ignore[return-value]

    def dialogue(
        self,
        npc_id: str,
        player_message: str,
        *,
        history: list[dict] | None = None,
        player_state: dict | None = None,
        world_events: list[dict] | None = None,
        locale: str = "tr",
    ) -> dict:
        payload = {
            "npc_id": npc_id,
            "player_message": player_message,
            "locale": locale,
            "history": history or [],
            "player_state": player_state
            or {"level": 1, "hp": 100, "max_hp": 100, "gold": 0, "inventory": [], "flags": {}},
            "world_events": world_events or [],
        }
        return self._post("/v1/dialogue", payload)


def _demo(base_url: str, npc: str) -> int:
    client = AshAIClient(base_url)

    try:
        health = client.health()
    except (urllib.error.URLError, ConnectionError) as exc:
        print(f"[!] Sunucuya ulaşılamadı: {exc}")
        print("    Önce: cd backend && uvicorn app.main:app --reload")
        return 1

    print(f"[+] Sağlayıcı: {health['provider']} / model: {health['model']}")
    if health.get("offline_mode"):
        print("    (offline/mock mod — gerçek model bağlı değil)")

    npcs = client.list_npcs()
    print(f"[+] {len(npcs)} NPC yüklü: {', '.join(n['name'] for n in npcs)}")

    history: list[dict] = []
    print("\nKonuşma başlıyor. Çıkmak için 'q'.\n")

    while True:
        try:
            message = input("Sen: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not message or message.lower() in {"q", "quit", "exit"}:
            break

        result = client.dialogue(npc, message, history=history)
        print(f"{npc}: {result['text']}   [{result['emotion']}]")

        for call in result.get("tool_calls", []):
            flag = " (onay gerekir)" if call.get("requires_confirmation") else ""
            print(f"   -> araç: {call['name']} {call['arguments']}{flag}")

        usage = result.get("usage", {})
        if usage.get("fallback_used"):
            print("   !! yedek moda düşüldü (ağ/anahtar sorunu)")

        history.append({"role": "player", "content": message})
        history.append({"role": "npc", "content": result["text"]})
        history = history[-20:]

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Kararsızlık AI backend istemcisi")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--npc", default="kapi_muhafizi_sabri")
    parser.add_argument("--once", metavar="MESAJ", help="tek mesaj gönder ve çık")
    args = parser.parse_args()

    if args.once:
        client = AshAIClient(args.base_url)
        print(json.dumps(client.dialogue(args.npc, args.once), ensure_ascii=False, indent=2))
        return 0

    return _demo(args.base_url, args.npc)


if __name__ == "__main__":
    sys.exit(main())
