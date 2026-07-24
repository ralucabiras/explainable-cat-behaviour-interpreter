import re
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from bson import ObjectId

from app.models.observation import BehaviourState
from app.models.pet import PetUpdate
from app.services.observations import ObservationService
from app.services.pets import DuplicatePetNameError, PetService


def matches(document: dict, query: dict) -> bool:
    for key, expected in query.items():
        if key == "$or":
            if not any(matches(document, option) for option in expected):
                return False
            continue
        value = document
        for part in key.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if isinstance(expected, dict):
            if (
                "$regex" in expected
                and re.search(
                    expected["$regex"],
                    str(value),
                    re.IGNORECASE if expected.get("$options") == "i" else 0,
                )
                is None
            ):
                return False
            if "$gte" in expected and value < expected["$gte"]:
                return False
            if "$lte" in expected and value > expected["$lte"]:
                return False
        elif value != expected:
            return False
    return True


class Cursor:
    def __init__(self, documents: list[dict]) -> None:
        self.documents = documents

    def sort(self, key: str, direction: int) -> "Cursor":
        self.documents.sort(key=lambda item: item[key], reverse=direction < 0)
        return self

    def skip(self, count: int) -> "Cursor":
        self.documents = self.documents[count:]
        return self

    def limit(self, count: int) -> "Cursor":
        self.documents = self.documents[:count]
        return self

    def __aiter__(self):
        async def iterate():
            for document in self.documents:
                yield document

        return iterate()


class Collection:
    def __init__(self, documents: list[dict] | None = None) -> None:
        self.documents = documents or []
        self.last_query: dict | None = None

    def find(self, query: dict) -> Cursor:
        self.last_query = query
        return Cursor([item.copy() for item in self.documents if matches(item, query)])

    async def find_one(self, query: dict) -> dict | None:
        self.last_query = query
        return next((item.copy() for item in self.documents if matches(item, query)), None)

    async def find_one_and_update(
        self, query: dict, update: dict, return_document: bool
    ) -> dict | None:
        del return_document
        for document in self.documents:
            if matches(document, query):
                document.update(update["$set"])
                return document.copy()
        return None

    async def delete_one(self, query: dict, **_kwargs) -> SimpleNamespace:
        before = len(self.documents)
        self.documents = [item for item in self.documents if not matches(item, query)]
        return SimpleNamespace(deleted_count=before - len(self.documents))

    async def delete_many(self, query: dict, **_kwargs) -> SimpleNamespace:
        before = len(self.documents)
        self.documents = [item for item in self.documents if not matches(item, query)]
        return SimpleNamespace(deleted_count=before - len(self.documents))


class Database:
    def __init__(self, pets: list[dict] | None = None, observations: list[dict] | None = None):
        self.pets = Collection(pets)
        self.observations = Collection(observations)


def pet_document(owner_id: str) -> dict:
    return {
        "_id": ObjectId(),
        "owner_id": owner_id,
        "name": "Miso",
        "species": "cat",
        "breed": None,
        "sex": "unknown",
        "date_of_birth": None,
        "notes": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


async def test_pet_update_is_owner_scoped_and_partial() -> None:
    document = pet_document("owner-1")
    database = Database([document])
    updated = await PetService(database).update(
        str(document["_id"]), PetUpdate(name="New name"), "owner-1"
    )
    assert updated is not None
    assert updated.name == "New name"
    assert updated.sex.value == "unknown"
    assert (
        await PetService(database).update(str(document["_id"]), PetUpdate(name="Stolen"), "owner-2")
        is None
    )


async def test_duplicate_cat_names_are_case_insensitive_per_owner() -> None:
    miso = pet_document("owner-1")
    luna = pet_document("owner-1")
    luna["name"] = "Luna"
    other_owner_miso = pet_document("owner-2")
    database = Database([miso, luna, other_owner_miso])
    with pytest.raises(DuplicatePetNameError):
        await PetService(database).update(
            str(luna["_id"]),
            PetUpdate(name="  MISO  "),
            "owner-1",
        )
    await PetService(database)._ensure_unique_name("owner-2", "Luna")


def test_empty_pet_update_is_invalid() -> None:
    with pytest.raises(ValueError, match="At least one"):
        PetUpdate()


async def test_observation_filters_are_owned_and_paginated() -> None:
    database = Database()
    await ObservationService(database).list(
        "owner-1",
        pet_id="pet-1",
        state=BehaviourState.FEARFUL,
        date_from=datetime(2026, 1, 1, tzinfo=UTC),
        date_to=datetime(2026, 2, 1, tzinfo=UTC),
        skip=20,
        limit=10,
    )
    assert database.observations.last_query == {
        "owner_id": "owner-1",
        "pet_id": "pet-1",
        "analysis.fusion.label": "fearful",
        "created_at": {
            "$gte": "2026-01-01T00:00:00+00:00",
            "$lte": "2026-02-01T00:00:00+00:00",
        },
    }


async def test_observation_delete_does_not_delete_another_owners_record() -> None:
    observation_id = ObjectId()
    database = Database(observations=[{"_id": observation_id, "owner_id": "owner-2"}])
    assert await ObservationService(database).delete(str(observation_id), "owner-1") is False
    assert len(database.observations.documents) == 1


async def test_standalone_cat_delete_cascades_only_owned_observations() -> None:
    pet = pet_document("owner-1")
    pet_id = str(pet["_id"])
    database = Database(
        pets=[pet, pet_document("owner-2")],
        observations=[
            {"_id": ObjectId(), "owner_id": "owner-1", "pet_id": pet_id},
            {"_id": ObjectId(), "owner_id": "owner-2", "pet_id": pet_id},
        ],
    )
    result = await PetService(database).delete(pet_id, "owner-1")
    assert result is not None
    assert result.deleted_observations == 1
    assert all(item["owner_id"] != "owner-1" for item in database.pets.documents)
    assert [item["owner_id"] for item in database.observations.documents] == ["owner-2"]
