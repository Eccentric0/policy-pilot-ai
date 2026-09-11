from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class OpenAICompatibleClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.model)

    def chat(self, system: str, user: str, timeout: int = 30) -> str:
        if not self.enabled:
            raise RuntimeError("模型未配置")
        payload = json.dumps(
            {
                "model": self.model,
                "temperature": 0.1,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body: dict[str, Any] = json.loads(response.read().decode("utf-8"))
            return str(body["choices"][0]["message"]["content"])
        except (urllib.error.URLError, TimeoutError, OSError, KeyError, IndexError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"模型调用失败: {exc}") from exc
