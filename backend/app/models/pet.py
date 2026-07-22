from datetime import date
from enum import StrEnum

from pydantic import Field

from app.models.common import APIModel, StoredModel


class Sex(StrEnum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"


class PetCreate(APIModel):
    name: str = Field(min_length=1, max_length=80)
    species: str = Field(default="cat", pattern="^cat$")
    breed: str | None = Field(default=None, max_length=100)
    sex: Sex = Sex.UNKNOWN
    date_of_birth: date | None = None
    notes: str | None = Field(default=None, max_length=1000)


class Pet(StoredModel, PetCreate):
    pass

