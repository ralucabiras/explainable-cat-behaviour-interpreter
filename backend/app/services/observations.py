from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.context_analyser import ContextAnalyser
from app.ai.fusion import FusionEngine
from app.ai.safety import assess_safety
from app.ai.text_analyser import TextAnalyser
from app.models.observation import (
    AnalysisBundle,
    BehaviourState,
    Observation,
    ObservationCreate,
)
from app.repositories.base import MongoRepository


class ObservationService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.database = database
        self.repository = MongoRepository(database.observations)

    async def create(self, payload: ObservationCreate, owner_id: str) -> Observation | None:
        if not ObjectId.is_valid(payload.pet_id):
            return None
        if (
            await self.database.pets.find_one(
                {"_id": ObjectId(payload.pet_id), "owner_id": owner_id}
            )
            is None
        ):
            return None
        now = datetime.now(UTC)
        stored = Observation(
            id="pending",
            **payload.model_dump(),
            created_at=now,
            updated_at=now,
            owner_id=owner_id,
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

    async def get(self, observation_id: str, owner_id: str) -> Observation | None:
        return await self.repository.get(observation_id, Observation, {"owner_id": owner_id})

    async def list(
        self,
        owner_id: str,
        pet_id: str | None = None,
        state: BehaviourState | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Observation]:
        query = {"owner_id": owner_id}
        if pet_id:
            query["pet_id"] = pet_id
        if state:
            query["analysis.fusion.label"] = state.value
        if date_from or date_to:
            created_at: dict[str, str] = {}
            if date_from:
                created_at["$gte"] = self._utc_iso(date_from)
            if date_to:
                created_at["$lte"] = self._utc_iso(date_to)
            query["created_at"] = created_at
        return await self.repository.list(
            Observation,
            query,
            skip=skip,
            limit=limit,
        )

    async def delete(self, observation_id: str, owner_id: str) -> bool:
        return await self.repository.delete(observation_id, {"owner_id": owner_id})

    @staticmethod
    def _utc_iso(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat()
