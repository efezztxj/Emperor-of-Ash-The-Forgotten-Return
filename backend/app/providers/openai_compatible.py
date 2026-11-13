"""OpenAI-uyumlu sağlayıcı.

Bu tek sınıf şunların hepsini kapsar:
  OpenAI, Ollama, LM Studio, vLLM, OpenRouter, Groq, DeepSeek, Together, Azure-uyumlu
Sadece OPENAI_BASE_URL + OPENAI_MODEL (veya LOCAL_* ) değişir.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from .base import ModelReply, ProviderError


class OpenAICompatibleProvider:
    def __init__(self, base_url: str, model: str, api_key: str = "", name: str = "openai") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.name = name

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        # Ollama/LM Studio anahtar istemez
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        timeout: float = 30.0,
    ) -> ModelReply:
        body: dict[str, Any] = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, *messages],
        }
        if tools:
            body["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=body,
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name}: bağlantı hatası: {exc}") from exc

        if resp.status_code >= 400:
            raise ProviderError(f"{self.name}: HTTP {resp.status_code}: {resp.text[:300]}")

        try:
            data = resp.json()
            choice = data["choices"][0]
        except (KeyError, IndexError, ValueError) as exc:
            raise ProviderError(f"{self.name}: beklenmeyen yanıt: {resp.text[:300]}") from exc

        message = choice.get("message") or {}
        content = message.get("content") or ""

        # Yerel modeller content'i liste olarak döndürebilir
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )

        calls: list[dict[str, Any]] = []
        for call in message.get("tool_calls") or []:
            fn = (call or {}).get("function") or {}
            args = fn.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            calls.append(
                {
                    "name": fn.get("name", ""),
                    "arguments": args if isinstance(args, dict) else {},
                }
            )

        usage = data.get("usage") or {}
        return ModelReply(
            text=content,
            tool_calls=calls,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            model=data.get("model", self.model),
            provider=self.name,
        )
