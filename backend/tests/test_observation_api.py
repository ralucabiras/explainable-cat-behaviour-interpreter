import json

from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.db.mongodb import get_database
from app.main import app
from app.models.user import User


class InsertResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class FakeCollection:
    def __init__(self) -> None:
        self.inserted: list[dict] = []

    async def find_one(self, _query: dict) -> dict:
        return {
            "_id": ObjectId(),
            "name": "Miso",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }

    async def insert_one(self, document: dict) -> InsertResult:
        self.inserted.append(document)
        return InsertResult(ObjectId())


class FakeDatabase:
    def __init__(self) -> None:
        self.pets = FakeCollection()
        self.observations = FakeCollection()


def test_create_endpoint_returns_explainable_analysis() -> None:
    database = FakeDatabase()

    async def override_database():
        yield database

    async def override_user():
        return User(
            id=str(ObjectId()),
            display_name="Test Owner",
            email="owner@example.com",
            email_verified=True,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )

    app.dependency_overrides[get_database] = override_database
    app.dependency_overrides[get_current_user] = override_user
    try:
        response = TestClient(app).post(
            "/api/v1/observations",
            json={
                "pet_id": str(ObjectId()),
                "text_description": "She is pacing after moving to a new apartment.",
                "context": {"recent_travel_or_relocation": True},
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    interpretation = response.json()["analysis"]["fusion"]
    assert interpretation["status"] == "completed"
    assert interpretation["label"] == "stressed_or_frustrated"
    assert interpretation["evidence"]
    assert interpretation["explanation"]


def test_video_endpoint_requires_consent_and_supported_type() -> None:
    database = FakeDatabase()

    async def override_database():
        yield database

    async def override_user():
        return User(
            id=str(ObjectId()),
            display_name="Test Owner",
            email="owner@example.com",
            email_verified=True,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )

    payload = {
        "pet_id": str(ObjectId()),
        "text_description": "The cat moved around.",
    }
    app.dependency_overrides[get_database] = override_database
    app.dependency_overrides[get_current_user] = override_user
    try:
        client = TestClient(app)
        missing_consent = client.post(
            "/api/v1/observations/with-video",
            data={"payload": json.dumps(payload), "media_consent_confirmed": "false"},
            files={"video": ("clip.mp4", b"content", "video/mp4")},
        )
        unsupported = client.post(
            "/api/v1/observations/with-video",
            data={"payload": json.dumps(payload), "media_consent_confirmed": "true"},
            files={"video": ("clip.txt", b"content", "text/plain")},
        )
    finally:
        app.dependency_overrides.clear()

    assert missing_consent.status_code == 422
    assert unsupported.status_code == 415
