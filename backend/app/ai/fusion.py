from collections import defaultdict

from app.ai.safety import SafetyAssessment
from app.ai.scoring import classify_scores, sorted_scores
from app.ai.taxonomy import RECOMMENDATIONS, STATE_EXPLANATIONS
from app.models.observation import (
    AlternativeInterpretation,
    AnalysisStatus,
    BehaviourState,
    EvidenceItem,
    ModalityResult,
    StateScore,
)


class FusionEngine:
    """Boundary for explainable late fusion across whichever modalities are available."""

    async def combine(
        self,
        text_result: ModalityResult,
        context_result: ModalityResult,
        safety: SafetyAssessment,
    ) -> ModalityResult:
        evidence = self._unique_evidence(text_result.evidence + context_result.evidence)
        if safety.triggered:
            return ModalityResult(
                status=AnalysisStatus.COMPLETED,
                label=BehaviourState.POTENTIALLY_UNWELL,
                confidence=0.95,
                detected_features=list(safety.trigger_keys),
                evidence=evidence,
                state_scores=[StateScore(state=BehaviourState.POTENTIALLY_UNWELL, score=1.0)],
                explanation=(
                    "The description includes a potentially urgent health or safety sign. "
                    "This tool cannot determine its cause."
                ),
                safety_escalation=True,
                safety_message=(
                    "Contact a veterinarian or emergency veterinary service promptly for guidance."
                ),
            )

        available = [
            (text_result, 0.7),
            (context_result, 0.3),
        ]
        active = [(result, weight) for result, weight in available if result.state_scores]
        weight_total = sum(weight for _, weight in active)
        fused_scores = defaultdict(float)
        for result, weight in active:
            for item in result.state_scores:
                fused_scores[item.state] += item.score * weight / weight_total

        label, confidence = classify_scores(fused_scores, len(evidence))
        ranked = sorted(fused_scores.items(), key=lambda item: (-item[1], item[0].value))
        score_total = sum(score for _, score in ranked)
        alternatives = [
            AlternativeInterpretation(
                state=state,
                confidence=round(min(0.75, score / score_total), 2),
            )
            for state, score in ranked
            if score > 0 and state != label
        ][:2]
        observations = ", ".join(item.observation for item in evidence)
        explanation = STATE_EXPLANATIONS[label]
        if observations:
            explanation += f" This is based on {observations}."
        return ModalityResult(
            status=AnalysisStatus.COMPLETED,
            label=label,
            confidence=confidence,
            detected_features=[item.key for item in evidence],
            evidence=evidence,
            state_scores=sorted_scores(fused_scores),
            alternatives=alternatives,
            explanation=explanation,
            recommendations=list(RECOMMENDATIONS[label]),
        )

    @staticmethod
    def _unique_evidence(items: list[EvidenceItem]) -> list[EvidenceItem]:
        return list({(item.source, item.key): item for item in items}.values())
