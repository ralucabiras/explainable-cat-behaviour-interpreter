from typing import Protocol

from app.models.observation import ModalityResult, Observation


class Analyser(Protocol):
    async def analyse(self, observation: Observation) -> ModalityResult: ...

