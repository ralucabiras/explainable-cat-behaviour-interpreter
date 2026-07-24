from datetime import UTC, datetime

import pytest

from app.ai.context_analyser import ContextAnalyser
from app.ai.fusion import FusionEngine
from app.ai.safety import assess_safety
from app.ai.text_analyser import TextAnalyser
from app.models.observation import (
    AnalysisStatus,
    BehaviourState,
    Observation,
    ObservationContext,
)
from app.models.pet import Pet


def observation(text: str, context: ObservationContext | None = None) -> Observation:
    now = datetime.now(UTC)
    return Observation(
        id="test",
        pet_id="pet",
        text_description=text,
        context=context or ObservationContext(),
        created_at=now,
        updated_at=now,
    )


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ("She is resting with a loose body.", BehaviourState.RELAXED),
        ("He is playing and chasing a toy.", BehaviourState.PLAYFUL),
        ("She is exploring and sniffing around.", BehaviourState.ALERT_OR_CURIOUS),
        ("He is following me and pawing at me.", BehaviourState.ATTENTION_SEEKING),
        ("She is hiding under the bed.", BehaviourState.FEARFUL),
        ("He is pacing and cannot settle.", BehaviourState.STRESSED_OR_FRUSTRATED),
        ("She is hissing and swatting.", BehaviourState.DEFENSIVE_OR_AGGRESSIVE),
        ("He stopped eating and is less active.", BehaviourState.POTENTIALLY_UNWELL),
        ("He sat beside the blue chair.", BehaviourState.UNCERTAIN),
    ],
)
async def test_text_taxonomy_states(description: str, expected: BehaviourState) -> None:
    result = await TextAnalyser().analyse(observation(description))
    assert result.status == AnalysisStatus.COMPLETED
    assert result.label == expected
    assert 0 <= (result.confidence or 0) <= 1


async def test_matching_is_case_insensitive_and_respects_negation() -> None:
    positive = await TextAnalyser().analyse(observation("SHE IS HIDING UNDER THE BED"))
    negative = await TextAnalyser().analyse(observation("She is not hiding under the bed"))
    assert positive.label == BehaviourState.FEARFUL
    assert negative.label == BehaviourState.UNCERTAIN
    assert "hiding" not in negative.detected_features


async def test_conflicting_clues_return_uncertain_with_evidence() -> None:
    result = await TextAnalyser().analyse(observation("He is hiding but also playing."))
    assert result.label == BehaviourState.UNCERTAIN
    assert {item.key for item in result.evidence} == {"hiding", "play"}


async def test_synonyms_for_one_clue_are_not_double_counted() -> None:
    result = await TextAnalyser().analyse(observation("She is hiding under the bed."))
    assert [item.key for item in result.evidence].count("hiding") == 1


async def test_independent_supporting_clues_increase_confidence() -> None:
    single = await TextAnalyser().analyse(observation("She is pacing."))
    multiple = await TextAnalyser().analyse(observation("She is pacing and overgrooming."))
    assert (multiple.confidence or 0) > (single.confidence or 0)


async def test_context_can_produce_an_interpretation_without_text_clues() -> None:
    item = observation(
        "Something changed.",
        ObservationContext(recent_travel_or_relocation=True, routine_changes="New home"),
    )
    result = await ContextAnalyser().analyse(item)
    assert result.label == BehaviourState.STRESSED_OR_FRUSTRATED
    assert {evidence.source.value for evidence in result.evidence} == {"context"}


async def test_profile_traits_add_context_only_when_situation_is_relevant() -> None:
    item = observation(
        "The doorbell rang and she watched the visitor.",
        ObservationContext(unfamiliar_people_present=True),
    )
    pet = Pet(
        id="pet",
        owner_id="owner",
        name="Miso",
        sociability_with_people="shy",
        known_triggers=["doorbell"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    result = await ContextAnalyser().analyse(item, pet)
    assert "profile_people_sociability" in result.detected_features
    assert "profile_known_trigger" in result.detected_features


@pytest.mark.parametrize(
    "description",
    [
        "The cat has difficulty breathing.",
        "The cat collapsed.",
        "The cat cannot urinate.",
        "The cat keeps vomiting.",
        "The cat has severe lethargy.",
        "The cat had a seizure.",
        "There is suspected poisoning.",
        "The cat has a serious injury.",
    ],
)
async def test_safety_triggers_override_behaviour(description: str) -> None:
    item = observation(f"{description} She is also playing.")
    text = await TextAnalyser().analyse(item)
    context = await ContextAnalyser().analyse(item)
    result = await FusionEngine().combine(text, context, assess_safety(item.text_description))
    assert result.label == BehaviourState.POTENTIALLY_UNWELL
    assert result.safety_escalation is True
    assert result.safety_message
    assert result.recommendations == []
    assert "cannot determine" in (result.explanation or "")


def test_negated_safety_phrase_does_not_trigger() -> None:
    assert assess_safety("She is not struggling to breathe.").triggered is False


async def test_fusion_renormalises_when_context_has_no_evidence() -> None:
    item = observation("She is resting and slow blinking.")
    text = await TextAnalyser().analyse(item)
    context = await ContextAnalyser().analyse(item)
    result = await FusionEngine().combine(text, context, assess_safety(item.text_description))
    assert result.label == BehaviourState.RELAXED
    assert result.recommendations
    assert all(0 <= alternative.confidence <= 1 for alternative in result.alternatives)
