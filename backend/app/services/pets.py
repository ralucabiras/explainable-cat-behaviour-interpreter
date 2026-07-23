from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import OperationFailure

from app.models.pet import Pet, PetCreate, PetDeleteResponse, PetUpdate
from app.repositories.base import MongoRepository


class PetService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.database = database
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

    async def update(self, pet_id: str, payload: PetUpdate, owner_id: str) -> Pet | None:
        changes = payload.model_dump(exclude_unset=True, mode="json")
        changes["updated_at"] = datetime.now(UTC).isoformat()
        return await self.repository.update(
            pet_id,
            changes,
            Pet,
            {"owner_id": owner_id},
        )

    async def delete(self, pet_id: str, owner_id: str) -> PetDeleteResponse | None:
        pet = await self.get(pet_id, owner_id)
        if pet is None:
            return None
        try:
            deleted_count = await self._delete_in_transaction(pet_id, owner_id)
        except (AttributeError, NotImplementedError, OperationFailure):
            deleted_count = await self._delete_ordered(pet_id, owner_id)
        return PetDeleteResponse(
            message="Cat profile and its observations were deleted",
            deleted_observations=deleted_count,
        )

    async def _delete_in_transaction(self, pet_id: str, owner_id: str) -> int:
        session = await self.database.client.start_session()
        async with session:
            async with session.start_transaction():
                pet_result = await self.database.pets.delete_one(
                    {"_id": ObjectId(pet_id), "owner_id": owner_id},
                    session=session,
                )
                if pet_result.deleted_count != 1:
                    raise OperationFailure("Pet disappeared before deletion")
                observation_result = await self.database.observations.delete_many(
                    {"pet_id": pet_id, "owner_id": owner_id},
                    session=session,
                )
        return observation_result.deleted_count

    async def _delete_ordered(self, pet_id: str, owner_id: str) -> int:
        deleted = await self.repository.delete(pet_id, {"owner_id": owner_id})
        if not deleted:
            return 0
        result = await self.database.observations.delete_many(
            {"pet_id": pet_id, "owner_id": owner_id}
        )
        return result.deleted_count
