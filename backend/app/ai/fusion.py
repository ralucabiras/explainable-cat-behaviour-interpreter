from app.models.observation import ModalityResult


class FusionEngine:
    """Boundary for explainable late fusion across whichever modalities are available."""

    async def combine(self, results: list[ModalityResult]) -> ModalityResult:
        raise NotImplementedError("Multimodal fusion has not been implemented yet")

