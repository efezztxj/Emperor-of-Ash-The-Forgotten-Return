"""Google Gemini sağlayıcısı (function calling + opsiyonel google_search).

Gemini'nin function calling'i OpenAI'dan farklı şekilli; burada çeviriyoruz ki
uygulamanın geri kalanı tek tip ModelReply görsün.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from .base import ModelReply, ProviderError


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        decls = []
        for tool in tools:
            fn = tool.get("function") or tool
            props = fn.get("parameters", {}).get("properties", {})
            decls.append(
                {
                    "name": fn["name"],
                    "description": fn.get("description", ""),
                    "parameters": {
                        "type": "object",
                        "properties": {k: {"type": v.get("type", "string")} for k, v in props.items()},
                        "required": list(props.keys()),
                    },
                }
            )
        return [{"functionDeclarations": decls}] if decls else []

    async def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        timeout: float = 30.0,
    ) -> ModelReply:
        if not self.api_key:
            raise ProviderError("gemini: GEMINI_API_KEY boş")

        contents = [
            {
                "role": "model" if m["role"] == "npc" else "user",
                "parts": [{"text": m["content"]}],
            }
            for m in messages
        ]
        body: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        gemini_tools = self._convert_tools(tools)
        if gemini_tools:
            body["tools"] = gemini_tools

        url = f"{self.base_url}/models/{self.model}:generateContent"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    url,
                    headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
                    json=body,
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"gemini: bağlantı hatası: {exc}") from exc

        if resp.status_code >= 400:
            raise ProviderError(f"gemini: HTTP {resp.status_code}: {resp.text[:300]}")

        try:
            data = resp.json()
            parts = data["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, ValueError) as exc:
            raise ProviderError(f"gemini: beklenmeyen yanıt: {resp.text[:300]}") from exc

        texts, calls = [], []
        for part in parts:
            if "text" in part:
                texts.append(part["text"])
            if "functionCall" in part:
                fc = part["functionCall"]
                calls.append({"name": fc.get("name", ""), "arguments": fc.get("args") or {}})

        usage = data.get("usageMetadata") or {}
        return ModelReply(
            text="".join(texts),
            tool_calls=calls,
            input_tokens=int(usage.get("promptTokenCount") or 0),
            output_tokens=int(usage.get("candidatesTokenCount") or 0),
            model=self.model,
            provider=self.name,
        )


__all__ = ["GeminiProvider"]
