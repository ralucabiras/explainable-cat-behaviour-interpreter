from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.pet import Pet, PetCreate
from app.repositories.base import MongoRepository


class PetService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.repository = MongoRepository(database.pets)

    async def create(self, payload: PetCreate, owner_id: str) -> Pet:
        now = datetime.now(UTC)
        document = payload.model_dump()
        document.update(created_at=now, updated_at=now, owner_id=owner_id)
        return await self.repository.create(Pet.model_validate({"id": "pending", **document}), Pet)

    async def get(self, pet_id: str, owner_id: str) -> Pet | None:
        return await self.repository.get(pet_id, Pet, {"owner_id": owner_id})

    async def list(self, owner_id: str) -> list[Pet]:
        return await self.repository.list(Pet, {"owner_id": owner_id})
