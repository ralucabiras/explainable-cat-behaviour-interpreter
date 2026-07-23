from datetime import date
from enum import StrEnum

from pydantic import Field, model_validator

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


class PetUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    breed: str | None = Field(default=None, max_length=100)
    sex: Sex | None = None
    date_of_birth: date | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def require_a_change(self) -> "PetUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one profile field must be supplied")
        return self


class Pet(StoredModel, PetCreate):
    owner_id: str | None = None


class PetDeleteResponse(APIModel):
    message: str
    deleted_observations: int = Field(ge=0)
