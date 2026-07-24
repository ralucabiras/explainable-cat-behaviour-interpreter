from collections import defaultdict

from app.ai.scoring import modality_result, phrase_is_present
from app.models.observation import (
    BehaviourState,
    EvidenceItem,
    EvidenceSource,
    FeedingStatus,
    ModalityResult,
    Observation,
)
from app.models.pet import Pet, RoutineSensitivity, Sociability


class ContextAnalyser:
    async def analyse(self, observation: Observation, pet: Pet | None = None) -> ModalityResult:
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
        if (
            pet
            and pet.routine_sensitivity == RoutineSensitivity.HIGH
            and (context.recent_travel_or_relocation or context.routine_changes)
        ):
            add(
                "profile_routine_sensitivity",
                "a profile history of high sensitivity to routine changes",
                {BehaviourState.STRESSED_OR_FRUSTRATED: 0.8},
            )
        if (
            pet
            and pet.sociability_with_people == Sociability.SHY
            and context.unfamiliar_people_present
        ):
            add(
                "profile_people_sociability",
                "a profile history of shyness around people",
                {BehaviourState.FEARFUL: 0.8},
            )
        if (
            pet
            and pet.sociability_with_animals == Sociability.SHY
            and context.unfamiliar_animals_present
        ):
            add(
                "profile_animal_sociability",
                "a profile history of shyness around other animals",
                {BehaviourState.FEARFUL: 0.8},
            )
        if pet and pet.known_triggers:
            situational_text = " ".join(
                part for part in (observation.text_description, context.routine_changes) if part
            )
            matched_triggers = [
                trigger
                for trigger in pet.known_triggers
                if phrase_is_present(situational_text, trigger)
            ]
            if matched_triggers:
                add(
                    "profile_known_trigger",
                    f"a known profile trigger was mentioned ({', '.join(matched_triggers)})",
                    {
                        BehaviourState.FEARFUL: 0.9,
                        BehaviourState.STRESSED_OR_FRUSTRATED: 0.7,
                    },
                )
        return modality_result(scores, evidence)
