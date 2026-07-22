from collections import defaultdict

from app.ai.scoring import modality_result
from app.models.observation import (
    BehaviourState,
    EvidenceItem,
    EvidenceSource,
    FeedingStatus,
    ModalityResult,
    Observation,
)


class ContextAnalyser:
    async def analyse(self, observation: Observation) -> ModalityResult:
        context = observation.context
        scores = defaultdict(float)
        evidence: list[EvidenceItem] = []

        def add(key: str, description: str, weights: dict[BehaviourState, float]) -> None:
            evidence.append(
                EvidenceItem(key=key, observation=description, source=EvidenceSource.CONTEXT)
            )
            for state, weight in weights.items():
                scores[state] += weight

        if context.recent_travel_or_relocation:
            add(
                "recent_relocation",
                "recent travel or relocation",
                {
                    BehaviourState.STRESSED_OR_FRUSTRATED: 1.5,
                    BehaviourState.ALERT_OR_CURIOUS: 0.7,
                    BehaviourState.FEARFUL: 0.5,
                },
            )
        if context.unfamiliar_people_present:
            add(
                "unfamiliar_people",
                "unfamiliar people were present",
                {BehaviourState.FEARFUL: 1.0, BehaviourState.ALERT_OR_CURIOUS: 0.5},
            )
        if context.unfamiliar_animals_present:
            add(
                "unfamiliar_animals",
                "unfamiliar animals were present",
                {BehaviourState.FEARFUL: 1.1, BehaviourState.DEFENSIVE_OR_AGGRESSIVE: 0.7},
            )
        if context.recent_play:
            add(
                "recent_play",
                "recent interactive play",
                {BehaviourState.PLAYFUL: 1.2, BehaviourState.RELAXED: 0.4},
            )
        if context.feeding_status == FeedingStatus.OVERDUE:
            add(
                "feeding_overdue",
                "a usual feeding time was overdue",
                {BehaviourState.ATTENTION_SEEKING: 1.0, BehaviourState.STRESSED_OR_FRUSTRATED: 0.5},
            )
        if context.routine_changes:
            add(
                "routine_change",
                "a recent change in routine",
                {BehaviourState.STRESSED_OR_FRUSTRATED: 1.2, BehaviourState.ALERT_OR_CURIOUS: 0.4},
            )
        if context.known_triggers:
            add(
                "known_trigger",
                "one or more known triggers were present",
                {BehaviourState.FEARFUL: 1.0, BehaviourState.STRESSED_OR_FRUSTRATED: 0.8},
            )
        return modality_result(scores, evidence)
