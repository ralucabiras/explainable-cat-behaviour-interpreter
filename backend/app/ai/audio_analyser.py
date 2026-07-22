from app.models.observation import ModalityResult, Observation


class AudioAnalyser:
    async def analyse(self, observation: Observation) -> ModalityResult:
        raise NotImplementedError("Audio analysis is deliberately deferred")
