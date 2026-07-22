from dataclasses import dataclass

from app.ai.scoring import phrase_is_present
from app.ai.taxonomy import SAFETY_TRIGGERS


@dataclass(frozen=True)
class SafetyAssessment:
    triggered: bool
    trigger_keys: tuple[str, ...] = ()


def assess_safety(text: str) -> SafetyAssessment:
    matches = tuple(
        key
        for key, phrases in SAFETY_TRIGGERS.items()
        if any(phrase_is_present(text, phrase) for phrase in phrases)
    )
    return SafetyAssessment(triggered=bool(matches), trigger_keys=matches)
