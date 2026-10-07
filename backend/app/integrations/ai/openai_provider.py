from collections.abc import Sequence

import httpx

from app.core.config import settings
from app.integrations.ai.provider import AIProvider, AssistantInput, ProviderError

SYSTEM_PROMPT = """You are the Helpful Hearts Health Assistant.
Provide general health information only. Do not diagnose diseases.
Do not prescribe or recommend starting, stopping, or changing medicines or dosages.
Be clear about uncertainty. For potentially urgent symptoms, recommend appropriate
professional or emergency care. Do not claim to replace a clinician.
"""

class OpenAIProvider(AIProvider):
    def generate(self, messages: Sequence[AssistantInput]) -> str:
        if not settings.openai_api_key:
            raise ProviderError("AI provider is not configured")
        payload = {"model": settings.openai_model, "input": [{"role": "developer", "content": SYSTEM_PROMPT}, *[{"role": m.role, "content": m.content} for m in messages]], "max_output_tokens": settings.openai_max_output_tokens}
        try:
            response = httpx.post("https://api.openai.com/v1/responses", json=payload, headers={"Authorization": f"Bearer {settings.openai_api_key}"}, timeout=settings.ai_timeout_seconds)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError("AI provider request failed") from exc
        data = response.json()
        output_text = data.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()
        parts = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    parts.append(content["text"])
        if not parts:
            raise ProviderError("AI provider returned no text")
        return "".join(parts).strip()
