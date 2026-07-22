import re
from collections.abc import Iterable, Mapping

from app.ai.taxonomy import STATE_EXPLANATIONS
from app.models.observation import (
    AnalysisStatus,
    BehaviourState,
    EvidenceItem,
    ModalityResult,
    StateScore,
)

NEGATIONS = {"no", "not", "never", "without", "isn't", "wasn't", "doesn't", "didn't"}


def normalise_text(text: str) -> str:
    return " ".join(text.lower().replace("’", "'").split())


def phrase_is_present(text: str, phrase: str) -> bool:
    normalised = normalise_text(text)
    escaped = re.escape(normalise_text(phrase)).replace(r"\ ", r"\s+")
    match = re.search(rf"(?<!\w){escaped}(?!\w)", normalised)
    if match is None:
        return False
    preceding = re.findall(r"[a-z]+(?:'[a-z]+)?", normalised[: match.start()])[-3:]
    return not any(token in NEGATIONS for token in preceding)


def sorted_scores(scores: Mapping[BehaviourState, float]) -> list[StateScore]:
    return [
        StateScore(state=state, score=round(score, 3))
        for state, score in sorted(scores.items(), key=lambda item: (-item[1], item[0].value))
        if score > 0
    ]


def classify_scores(
    scores: Mapping[BehaviourState, float], evidence_count: int
) -> tuple[BehaviourState, float]:
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0].value))
    if not ranked or ranked[0][1] <= 0:
        return BehaviourState.UNCERTAIN, 0.15
    top_state, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    if second_score > 0 and (top_score - second_score) / top_score < 0.18:
        return BehaviourState.UNCERTAIN, 0.3
    total = sum(score for _, score in ranked)
    dominance = top_score / total if total else 0
    confidence = min(0.88, 0.25 + 0.08 * min(evidence_count, 4) + 0.22 * dominance)
    return top_state, round(confidence, 2)


def modality_result(
    scores: Mapping[BehaviourState, float], evidence: Iterable[EvidenceItem]
) -> ModalityResult:
    evidence_list = list(evidence)
    label, confidence = classify_scores(scores, len(evidence_list))
    observations = ", ".join(item.observation for item in evidence_list)
    explanation = STATE_EXPLANATIONS[label]
    if observations:
        explanation = f"{explanation} Supporting observations: {observations}."
    return ModalityResult(
        status=AnalysisStatus.COMPLETED,
        label=label,
        confidence=confidence,
        detected_features=[item.key for item in evidence_list],
        evidence=evidence_list,
        state_scores=sorted_scores(scores),
        explanation=explanation,
    )
