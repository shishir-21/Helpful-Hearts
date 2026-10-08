from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyResult:
    blocked: bool
    response: str | None = None


EMERGENCY_RESPONSE = (
    "Some symptoms can be emergencies. If you have severe trouble breathing, "
    "chest pain, severe bleeding, loss of consciousness, or another life-threatening "
    "symptom, seek emergency medical care now or contact your local emergency service. "
    "Do not rely on this assistant for urgent care."
)


_EMERGENCY_TERMS = (
    "can't breathe",
    "cannot breathe",
    "difficulty breathing",
    "trouble breathing",
    "severe chest pain",
    "chest pain and sweating",
    "unconscious",
    "passed out",
    "loss of consciousness",
    "severe bleeding",
    "bleeding won't stop",
)


def evaluate_message(content: str) -> SafetyResult:
    normalized = " ".join(content.lower().split())
    if any(term in normalized for term in _EMERGENCY_TERMS):
        return SafetyResult(blocked=True, response=EMERGENCY_RESPONSE)
    return SafetyResult(blocked=False)
