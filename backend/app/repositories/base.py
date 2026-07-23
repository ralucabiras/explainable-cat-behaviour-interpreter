from typing import Any, TypeVar

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def serialise_document(document: dict[str, Any]) -> dict[str, Any]:
    result = dict(document)
    result["id"] = str(result.pop("_id"))
    return result


class MongoRepository:
    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self.collection = collection

    async def create(self, payload: BaseModel, output_model: type[T]) -> T:
        document = payload.model_dump(mode="json", exclude={"id"})
        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id
        return output_model.model_validate(serialise_document(document))

    async def get(
        self,
        item_id: str,
        output_model: type[T],
        query: dict[str, Any] | None = None,
    ) -> T | None:
        if not ObjectId.is_valid(item_id):
            return None
        filters = {"_id": ObjectId(item_id), **(query or {})}
        document = await self.collection.find_one(filters)
        return output_model.model_validate(serialise_document(document)) if document else None

    async def list(
        self,
        output_model: type[T],
        query: dict[str, Any] | None = None,
        *,
        skip: int = 0,
        limit: int | None = None,
    ) -> list[T]:
        cursor = self.collection.find(query or {}).sort("created_at", -1)
        if skip:
            cursor = cursor.skip(skip)
        if limit is not None:
            cursor = cursor.limit(limit)
        return [output_model.model_validate(serialise_document(item)) async for item in cursor]

    async def update(
        self,
        item_id: str,
        payload: dict[str, Any],
        output_model: type[T],
        query: dict[str, Any] | None = None,
    ) -> T | None:
        if not ObjectId.is_valid(item_id):
            return None
        filters = {"_id": ObjectId(item_id), **(query or {})}
        document = await self.collection.find_one_and_update(
            filters,
            {"$set": payload},
            return_document=True,
        )
        return output_model.model_validate(serialise_document(document)) if document else None

    async def delete(self, item_id: str, query: dict[str, Any] | None = None) -> bool:
        if not ObjectId.is_valid(item_id):
            return False
        filters = {"_id": ObjectId(item_id), **(query or {})}
        result = await self.collection.delete_one(filters)
        return result.deleted_count == 1
