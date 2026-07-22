import pytest
from bson import ObjectId

from app.models.observation import AnalysisStatus, BehaviourState, Observation, ObservationCreate
from app.services.observations import ObservationService


class InsertResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class FakeCollection:
    def __init__(self, existing_pet: bool = True) -> None:
        self.existing_pet = existing_pet
        self.inserted: list[dict] = []

    async def find_one(self, _query: dict) -> dict | None:
        return {"_id": ObjectId()} if self.existing_pet else None

    async def insert_one(self, document: dict) -> InsertResult:
        self.inserted.append(document)
        return InsertResult(ObjectId())


class FakeDatabase:
    def __init__(self, existing_pet: bool = True) -> None:
        self.pets = FakeCollection(existing_pet)
        self.observations = FakeCollection()


async def test_create_persists_completed_analysis() -> None:
    database = FakeDatabase()
    payload = ObservationCreate(
        pet_id=str(ObjectId()),
        text_description="She is pacing after we moved house.",
    )
    result = await ObservationService(database).create(payload)
    assert result is not None
    assert result.analysis.text.status == AnalysisStatus.COMPLETED
    assert result.analysis.context.status == AnalysisStatus.COMPLETED
    assert result.analysis.fusion.status == AnalysisStatus.COMPLETED
    assert result.analysis.fusion.label == BehaviourState.STRESSED_OR_FRUSTRATED
    assert len(database.observations.inserted) == 1


async def test_create_rejects_a_missing_pet_without_inserting() -> None:
    database = FakeDatabase(existing_pet=False)
    result = await ObservationService(database).create(
        ObservationCreate(pet_id=str(ObjectId()), text_description="She is hiding.")
    )
    assert result is None
    assert database.observations.inserted == []


async def test_analysis_failure_does_not_insert(monkeypatch) -> None:
    database = FakeDatabase()

    async def fail_analysis(*_args, **_kwargs):
        raise RuntimeError("analysis failed")

    monkeypatch.setattr("app.services.observations.TextAnalyser.analyse", fail_analysis)
    with pytest.raises(RuntimeError, match="analysis failed"):
        await ObservationService(database).create(
            ObservationCreate(pet_id=str(ObjectId()), text_description="She is hiding.")
        )
    assert database.observations.inserted == []


def test_older_observation_without_analysis_remains_readable() -> None:
    document = {
        "id": str(ObjectId()),
        "pet_id": str(ObjectId()),
        "text_description": "A historical observation",
        "context": {},
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    stored = Observation.model_validate(document)
    assert stored.analysis.fusion.status == AnalysisStatus.PENDING
