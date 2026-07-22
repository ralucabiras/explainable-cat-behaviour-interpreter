from dataclasses import dataclass

from app.models.observation import BehaviourState


@dataclass(frozen=True)
class TextClue:
    key: str
    observation: str
    phrases: tuple[str, ...]
    scores: dict[BehaviourState, float]


TEXT_CLUES = (
    TextClue(
        "resting",
        "resting with a loose body",
        ("relaxed", "resting", "loose body", "slow blinking", "purring softly"),
        {BehaviourState.RELAXED: 2.0},
    ),
    TextClue(
        "play",
        "active play behaviour",
        ("playing", "chasing a toy", "pouncing", "zoomies", "play bow"),
        {BehaviourState.PLAYFUL: 2.0, BehaviourState.ALERT_OR_CURIOUS: 0.4},
    ),
    TextClue(
        "exploration",
        "active exploration",
        ("exploring", "sniffing around", "watching closely", "looking around", "investigating"),
        {BehaviourState.ALERT_OR_CURIOUS: 1.8},
    ),
    TextClue(
        "attention",
        "repeated bids for attention",
        (
            "seeking attention",
            "following me",
            "pawing at me",
            "rubbing against me",
            "meowing at me",
        ),
        {BehaviourState.ATTENTION_SEEKING: 1.8},
    ),
    TextClue(
        "hiding",
        "hiding or withdrawal",
        ("hiding", "under the bed", "avoiding everyone", "trying to escape"),
        {BehaviourState.FEARFUL: 1.8, BehaviourState.STRESSED_OR_FRUSTRATED: 0.6},
    ),
    TextClue(
        "fear_posture",
        "a fearful body posture",
        ("crouching", "flattened ears", "tail tucked", "trembling", "wide eyes"),
        {BehaviourState.FEARFUL: 1.8, BehaviourState.DEFENSIVE_OR_AGGRESSIVE: 0.4},
    ),
    TextClue(
        "pacing",
        "repetitive pacing",
        ("pacing", "walking back and forth", "restless", "cannot settle", "can't settle"),
        {BehaviourState.STRESSED_OR_FRUSTRATED: 1.8, BehaviourState.ALERT_OR_CURIOUS: 0.3},
    ),
    TextClue(
        "overgrooming",
        "repetitive or excessive grooming",
        ("overgrooming", "excessive grooming", "licking constantly"),
        {BehaviourState.STRESSED_OR_FRUSTRATED: 1.5, BehaviourState.POTENTIALLY_UNWELL: 0.8},
    ),
    TextClue(
        "defensive",
        "defensive signals",
        ("hissing", "growling", "swatting", "lunging", "biting", "arched back"),
        {BehaviourState.DEFENSIVE_OR_AGGRESSIVE: 2.0, BehaviourState.FEARFUL: 0.5},
    ),
    TextClue(
        "low_activity",
        "an unusual reduction in activity",
        ("reduced activity", "less active", "not moving much", "very tired", "withdrawn"),
        {BehaviourState.POTENTIALLY_UNWELL: 1.6, BehaviourState.STRESSED_OR_FRUSTRATED: 0.4},
    ),
    TextClue(
        "appetite_change",
        "a change in eating",
        ("not eating", "stopped eating", "eating less", "loss of appetite", "eating much more"),
        {BehaviourState.POTENTIALLY_UNWELL: 2.0},
    ),
    TextClue(
        "litter_change",
        "a change in litter-box behaviour",
        (
            "outside the litter box",
            "litter box change",
            "straining in the litter box",
            "frequent litter box visits",
        ),
        {BehaviourState.POTENTIALLY_UNWELL: 2.0, BehaviourState.STRESSED_OR_FRUSTRATED: 0.5},
    ),
    TextClue(
        "vocalising",
        "frequent vocalisation",
        ("meowing repeatedly", "constant meowing", "vocalising", "yowling"),
        {BehaviourState.ATTENTION_SEEKING: 1.0, BehaviourState.STRESSED_OR_FRUSTRATED: 0.8},
    ),
)


STATE_EXPLANATIONS = {
    BehaviourState.RELAXED: "The described behaviour may be consistent with a relaxed state.",
    BehaviourState.PLAYFUL: "The described activity may reflect play and positive engagement.",
    BehaviourState.ALERT_OR_CURIOUS: "The cat may be alert or curious about its surroundings.",
    BehaviourState.ATTENTION_SEEKING: (
        "The behaviour may be an attempt to obtain social contact or another resource."
    ),
    BehaviourState.FEARFUL: (
        "The cat may be fearful and trying to create distance from a perceived threat."
    ),
    BehaviourState.STRESSED_OR_FRUSTRATED: (
        "The pattern may reflect stress or frustration in the current environment."
    ),
    BehaviourState.DEFENSIVE_OR_AGGRESSIVE: (
        "The signals may be defensive behaviour intended to increase distance."
    ),
    BehaviourState.POTENTIALLY_UNWELL: (
        "The reported change could be associated with discomfort or reduced wellbeing."
    ),
    BehaviourState.UNCERTAIN: "There is not enough distinct evidence to favour one interpretation.",
}


RECOMMENDATIONS = {
    BehaviourState.RELAXED: (
        "Maintain access to familiar resting places and the cat's usual routine.",
    ),
    BehaviourState.PLAYFUL: (
        "Offer a short, supervised interactive play session and allow time to settle afterward.",
    ),
    BehaviourState.ALERT_OR_CURIOUS: (
        "Allow safe exploration and provide an easy route back to a familiar hiding place.",
    ),
    BehaviourState.ATTENTION_SEEKING: (
        "Check routine needs, then offer calm attention or a short play session.",
    ),
    BehaviourState.FEARFUL: (
        "Reduce noise and pressure, provide a quiet hiding place, and let the cat "
        "approach in its own time.",
    ),
    BehaviourState.STRESSED_OR_FRUSTRATED: (
        "Restore a predictable routine and provide quiet space, familiar objects, and "
        "appropriate enrichment.",
    ),
    BehaviourState.DEFENSIVE_OR_AGGRESSIVE: (
        "Give the cat space, avoid punishment or forced handling, and remove immediate "
        "stressors when safe.",
    ),
    BehaviourState.POTENTIALLY_UNWELL: (
        "Monitor changes closely and contact a veterinarian if they are sudden, "
        "persistent, or worsening.",
    ),
    BehaviourState.UNCERTAIN: (
        "Observe duration, frequency, body posture, appetite, and litter-box use, then "
        "record a more detailed example.",
    ),
}


SAFETY_TRIGGERS = {
    "breathing_difficulty": (
        "difficulty breathing",
        "breathing difficulty",
        "struggling to breathe",
        "open mouth breathing",
    ),
    "collapse": ("collapsed", "collapse", "fainted", "unresponsive"),
    "unable_to_urinate": (
        "unable to urinate",
        "cannot urinate",
        "can't urinate",
        "not passing urine",
    ),
    "repeated_vomiting": ("repeated vomiting", "vomiting repeatedly", "keeps vomiting"),
    "severe_lethargy": ("severe lethargy", "extremely lethargic", "barely responsive"),
    "seizure": ("seizure", "seizures", "convulsing"),
    "suspected_poisoning": (
        "suspected poisoning",
        "may have eaten poison",
        "ingested poison",
        "toxic substance",
    ),
    "serious_injury": ("serious injury", "badly injured", "heavy bleeding", "deep wound"),
}
