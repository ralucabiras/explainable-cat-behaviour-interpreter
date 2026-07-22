from app.models.observation import ModalityResult, Observation


class TextAnalyser:
    """Boundary for the first analysis stage: taxonomy-backed text clue extraction."""

    async def analyse(self, observation: Observation) -> ModalityResult:
        raise NotImplementedError("Text analysis is the next implementation stage")

