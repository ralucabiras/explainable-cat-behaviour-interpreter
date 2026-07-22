from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.pet import Pet, PetCreate
from app.repositories.base import MongoRepository


class PetService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.repository = MongoRepository(database.pets)

    async def create(self, payload: PetCreate) -> Pet:
        now = datetime.now(timezone.utc)
        document = payload.model_dump()
        document.update(created_at=now, updated_at=now)
        return await self.repository.create(Pet.model_validate({"id": "pending", **document}), Pet)

    async def get(self, pet_id: str) -> Pet | None:
        return await self.repository.get(pet_id, Pet)

    async def list(self) -> list[Pet]:
        return await self.repository.list(Pet)

