from collections.abc import AsyncIterator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

_client: AsyncIOMotorClient | None = None


async def connect_to_mongo() -> None:
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_url)
    await _client.admin.command("ping")
    database = _client[settings.mongodb_database]
    await database.users.create_index("email", unique=True)
    await database.pets.create_index([("owner_id", 1), ("created_at", -1)])
    await database.pets.create_index(
        [("owner_id", 1), ("name_normalized", 1)],
        unique=True,
        partialFilterExpression={"name_normalized": {"$type": "string"}},
    )
    await database.observations.create_index([("owner_id", 1), ("pet_id", 1), ("created_at", -1)])
    await database.observations.create_index(
        [("owner_id", 1), ("analysis.fusion.label", 1), ("created_at", -1)]
    )


async def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def get_database() -> AsyncIterator[AsyncIOMotorDatabase]:
    if _client is None:
        raise RuntimeError("MongoDB connection has not been initialised")
    yield _client[get_settings().mongodb_database]
