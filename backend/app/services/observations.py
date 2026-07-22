from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

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
        now = datetime.now(timezone.utc)
        stored = Observation(
            id="pending",
            **payload.model_dump(),
            created_at=now,
            updated_at=now,
            analysis=AnalysisBundle(),
        )
        return await self.repository.create(stored, Observation)

    async def get(self, observation_id: str) -> Observation | None:
        return await self.repository.get(observation_id, Observation)

    async def list(self, pet_id: str | None = None) -> list[Observation]:
        return await self.repository.list(Observation, {"pet_id": pet_id} if pet_id else None)

