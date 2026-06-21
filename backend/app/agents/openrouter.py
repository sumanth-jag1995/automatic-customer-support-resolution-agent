import httpx
import json
from typing import Any

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

async def chat(
    key: str,
    model: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    response_format: dict | None = None,
) -> dict:
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    body: dict[str, Any] = {"model": model, "messages": messages}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    if response_format:
        body["response_format"] = response_format

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        return resp.json()

async def list_models(key: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{OPENROUTER_BASE}/models",
            headers={"Authorization": f"Bearer {key}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            m for m in data.get("data", [])
            if ("free" in m.get("id", "") or m.get("pricing", {}).get("prompt") == "0")
            and m.get("id")
        ]
