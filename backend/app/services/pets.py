import re
from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, OperationFailure

from app.models.pet import Pet, PetCreate, PetDeleteResponse, PetUpdate
from app.repositories.base import MongoRepository


class PetService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.database = database
        self.repository = MongoRepository(database.pets)

    async def create(self, payload: PetCreate, owner_id: str) -> Pet:
        normalised_name = self.normalise_name(payload.name)
        await self._ensure_unique_name(owner_id, payload.name)
        now = datetime.now(UTC)
        document = payload.model_dump()
        document.update(created_at=now, updated_at=now, owner_id=owner_id)
        try:
            return await self.repository.create(
                Pet.model_validate({"id": "pending", **document}),
                Pet,
                {"name_normalized": normalised_name},
            )
        except DuplicateKeyError as error:
            raise DuplicatePetNameError from error

    async def get(self, pet_id: str, owner_id: str) -> Pet | None:
        return await self.repository.get(pet_id, Pet, {"owner_id": owner_id})

    async def list(self, owner_id: str) -> list[Pet]:
        return await self.repository.list(Pet, {"owner_id": owner_id})

    async def update(self, pet_id: str, payload: PetUpdate, owner_id: str) -> Pet | None:
        current = await self.get(pet_id, owner_id)
        if current is None:
            return None
        changes = payload.model_dump(exclude_unset=True, mode="json")
        if "name" in changes:
            await self._ensure_unique_name(owner_id, changes["name"], pet_id)
            changes["name_normalized"] = self.normalise_name(changes["name"])
        changes["updated_at"] = datetime.now(UTC).isoformat()
        try:
            return await self.repository.update(
                pet_id,
                changes,
                Pet,
                {"owner_id": owner_id},
            )
        except DuplicateKeyError as error:
            raise DuplicatePetNameError from error

    async def delete(self, pet_id: str, owner_id: str) -> PetDeleteResponse | None:
        pet = await self.get(pet_id, owner_id)
        if pet is None:
            return None
        media_documents: list[dict] = []
        if hasattr(self.database, "media"):
            observation_ids = [
                str(document["_id"])
                async for document in self.database.observations.find(
                    {"pet_id": pet_id, "owner_id": owner_id},
                    {"_id": 1},
                )
            ]
            media_documents = [
                document
                async for document in self.database.media.find(
                    {"owner_id": owner_id, "observation_id": {"$in": observation_ids}}
                )
            ]
        try:
            deleted_count = await self._delete_in_transaction(pet_id, owner_id)
        except (AttributeError, NotImplementedError, OperationFailure):
            deleted_count = await self._delete_ordered(pet_id, owner_id)
        if media_documents:
            from app.services.media import MediaService

            media = MediaService(self.database)
            for document in media_documents:
                await media.delete_paths([document["path"], *document.get("frame_paths", [])])
            await self.database.media.delete_many(
                {"_id": {"$in": [document["_id"] for document in media_documents]}}
            )
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

    @staticmethod
    def normalise_name(name: str) -> str:
        return " ".join(name.split()).casefold()

    async def _ensure_unique_name(
        self,
        owner_id: str,
        name: str,
        exclude_pet_id: str | None = None,
    ) -> None:
        query: dict = {
            "owner_id": owner_id,
            "$or": [
                {"name_normalized": self.normalise_name(name)},
                {"name": {"$regex": f"^{re.escape(name.strip())}$", "$options": "i"}},
            ],
        }
        existing = await self.database.pets.find_one(query)
        if existing is not None and str(existing["_id"]) != exclude_pet_id:
            raise DuplicatePetNameError


class DuplicatePetNameError(Exception):
    pass
