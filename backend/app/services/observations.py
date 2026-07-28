from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.context_analyser import ContextAnalyser
from app.ai.fusion import FusionEngine
from app.ai.safety import assess_safety
from app.ai.text_analyser import TextAnalyser
from app.ai.video_analyser import VideoAnalysis
from app.models.observation import (
    AnalysisBundle,
    BehaviourState,
    MediaReference,
    Observation,
    ObservationCreate,
)
from app.models.pet import Pet
from app.repositories.base import MongoRepository, serialise_document


class ObservationService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.database = database
        self.repository = MongoRepository(database.observations)

    async def create(self, payload: ObservationCreate, owner_id: str) -> Observation | None:
        return await self._create_analysed(payload, owner_id)

    async def create_with_video(
        self,
        payload: ObservationCreate,
        owner_id: str,
        media_id: str,
        video_path: str,
        frame_paths: list[str],
        size_bytes: int,
        analysis: VideoAnalysis,
        original_filename: str,
        content_type: str,
    ) -> Observation | None:
        reference = MediaReference(
            media_id=media_id,
            filename=original_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            duration_seconds=round(analysis.duration, 3),
            width=analysis.width,
            height=analysis.height,
        )
        observation = await self._create_analysed(
            payload.model_copy(update={"video": reference}),
            owner_id,
            analysis.result,
        )
        if observation is None:
            return None
        try:
            await self.database.media.insert_one(
                {
                    "_id": ObjectId(media_id),
                    "owner_id": owner_id,
                    "observation_id": observation.id,
                    "filename": original_filename,
                    "content_type": content_type,
                    "size_bytes": size_bytes,
                    "duration_seconds": analysis.duration,
                    "width": analysis.width,
                    "height": analysis.height,
                    "path": video_path,
                    "frame_paths": frame_paths,
                    "consent_confirmed": True,
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
        except Exception:
            await self.repository.delete(observation.id, {"owner_id": owner_id})
            raise
        return observation

    async def _create_analysed(
        self,
        payload: ObservationCreate,
        owner_id: str,
        video_result=None,
    ) -> Observation | None:
        if not ObjectId.is_valid(payload.pet_id):
            return None
        pet_document = await self.database.pets.find_one(
            {"_id": ObjectId(payload.pet_id), "owner_id": owner_id}
        )
        if pet_document is None:
            return None
        pet = Pet.model_validate(serialise_document(pet_document))
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
        context_result = await ContextAnalyser().analyse(stored, pet)
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
                    video=video_result or AnalysisBundle().video,
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
        deleted = await self.repository.delete(observation_id, {"owner_id": owner_id})
        if deleted and hasattr(self.database, "media"):
            from app.services.media import MediaService

            await MediaService(self.database).delete_for_observation(observation_id, owner_id)
        return deleted

    @staticmethod
    def _utc_iso(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat()
