from dataclasses import dataclass

import httpx

from app.core.config import settings


class AssistantProviderError(Exception):
    """Raised when the configured AI provider cannot produce a response."""


@dataclass(frozen=True)
class AssistantProvider:
    api_key: str
    model: str
    base_url: str
    timeout_seconds: float

    async def generate(self, messages: list[dict[str, str]]) -> str:
        if not self.api_key or not self.model or not self.base_url:
            raise AssistantProviderError("AI provider is not configured")

        payload = {"model": self.model, "messages": messages, "temperature": 0.2}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        url = f"{self.base_url.rstrip('/')}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AssistantProviderError("AI provider request failed") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AssistantProviderError("AI provider returned an invalid response") from exc

        if not isinstance(content, str) or not content.strip():
            raise AssistantProviderError("AI provider returned an empty response")
        return content.strip()


def get_assistant_provider() -> AssistantProvider:
    return AssistantProvider(
        api_key=settings.ai_api_key,
        model=settings.ai_model,
        base_url=settings.ai_base_url,
        timeout_seconds=settings.ai_timeout_seconds,
    )


SYSTEM_PROMPT = (
    "You are the Helpful Hearts health assistant. Provide general health information and education only. "
    "Do not diagnose conditions, prescribe or change medication, or claim certainty about a medical condition. "
    "For urgent or emergency symptoms, advise the user to contact local emergency services or seek immediate medical care. "
    "Encourage consultation with a qualified healthcare professional when symptoms are persistent, severe, or unclear. "
    "Keep answers clear, calm, practical, and concise."
)
