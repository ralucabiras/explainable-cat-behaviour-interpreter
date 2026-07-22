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

    async def get(self, item_id: str, output_model: type[T]) -> T | None:
        if not ObjectId.is_valid(item_id):
            return None
        document = await self.collection.find_one({"_id": ObjectId(item_id)})
        return output_model.model_validate(serialise_document(document)) if document else None

    async def list(self, output_model: type[T], query: dict[str, Any] | None = None) -> list[T]:
        cursor = self.collection.find(query or {}).sort("created_at", -1)
        return [output_model.model_validate(serialise_document(item)) async for item in cursor]
