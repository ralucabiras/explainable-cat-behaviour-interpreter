from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.context_analyser import ContextAnalyser
from app.ai.fusion import FusionEngine
from app.ai.safety import assess_safety
from app.ai.text_analyser import TextAnalyser
from app.models.observation import AnalysisBundle, Observation, ObservationCreate
from app.repositories.base import MongoRepository


class ObservationService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.database = database
        self.repository = MongoRepository(database.observations)

    async def create(self, payload: ObservationCreate) -> Observation | None:
        if not ObjectId.is_valid(payload.pet_id):
            return None
        if await self.database.pets.find_one({"_id": ObjectId(payload.pet_id)}) is None:
            return None
        now = datetime.now(UTC)
        stored = Observation(
            id="pending",
            **payload.model_dump(),
            created_at=now,
            updated_at=now,
            analysis=AnalysisBundle(),
        )
        text_result = await TextAnalyser().analyse(stored)
        context_result = await ContextAnalyser().analyse(stored)
        safety_text = " ".join(
            part
            for part in (
                stored.text_description,
                stored.context.routine_changes,
                " ".join(stored.context.known_triggers),
            )
            if part
        )
        fusion_result = await FusionEngine().combine(
            text_result,
            context_result,
            assess_safety(safety_text),
        )
        stored = stored.model_copy(
            update={
                "analysis": AnalysisBundle(
                    text=text_result,
                    context=context_result,
                    fusion=fusion_result,
                )
            }
        )
        return await self.repository.create(stored, Observation)

    async def get(self, observation_id: str) -> Observation | None:
        return await self.repository.get(observation_id, Observation)

    async def list(self, pet_id: str | None = None) -> list[Observation]:
        return await self.repository.list(Observation, {"pet_id": pet_id} if pet_id else None)
