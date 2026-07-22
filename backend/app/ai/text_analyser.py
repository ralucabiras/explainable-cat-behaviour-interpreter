from collections import defaultdict

from app.ai.scoring import modality_result, phrase_is_present
from app.ai.taxonomy import TEXT_CLUES
from app.models.observation import EvidenceItem, EvidenceSource, ModalityResult, Observation


class TextAnalyser:
    """Boundary for the first analysis stage: taxonomy-backed text clue extraction."""

    async def analyse(self, observation: Observation) -> ModalityResult:
        scores = defaultdict(float)
        evidence: list[EvidenceItem] = []
        for clue in TEXT_CLUES:
            if not any(
                phrase_is_present(observation.text_description, phrase) for phrase in clue.phrases
            ):
                continue
            evidence.append(
                EvidenceItem(key=clue.key, observation=clue.observation, source=EvidenceSource.TEXT)
            )
            for state, weight in clue.scores.items():
                scores[state] += weight
        return modality_result(scores, evidence)
