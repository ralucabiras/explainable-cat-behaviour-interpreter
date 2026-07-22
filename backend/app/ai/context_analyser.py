from app.models.observation import ModalityResult, Observation


class ContextAnalyser:
    async def analyse(self, observation: Observation) -> ModalityResult:
        raise NotImplementedError("Context reasoning is the next implementation stage")

