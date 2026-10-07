from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AssistantInput:
    role: str
    content: str


class AIProvider(Protocol):
    def generate(self, messages: Sequence[AssistantInput]) -> str:
        ...


class ProviderError(RuntimeError):
    pass
