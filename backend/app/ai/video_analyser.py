from app.models.observation import ModalityResult, Observation


class VideoAnalyser:
    async def analyse(self, observation: Observation) -> ModalityResult:
        raise NotImplementedError("Video analysis follows stable text and context analysis")
