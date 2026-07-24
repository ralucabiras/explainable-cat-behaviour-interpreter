from datetime import date
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from app.models.common import APIModel, StoredModel


class Sex(StrEnum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"


class FeedingMethod(StrEnum):
    FREE_FED = "free_fed"
    SCHEDULED_ONCE_DAILY = "scheduled_once_daily"
    SCHEDULED_TWICE_DAILY = "scheduled_twice_daily"
    SCHEDULED_THREE_PLUS = "scheduled_three_plus"
    MIXED = "mixed"
    OTHER = "other"
    UNKNOWN = "unknown"


class ActivityLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    UNKNOWN = "unknown"


class Sociability(StrEnum):
    SOCIAL = "social"
    SELECTIVE = "selective"
    SHY = "shy"
    UNKNOWN = "unknown"


class RoutineSensitivity(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    UNKNOWN = "unknown"


class PetCreate(APIModel):
    name: str = Field(min_length=1, max_length=80)
    species: str = Field(default="cat", pattern="^cat$")
    breed: str | None = Field(default=None, max_length=100)
    sex: Sex = Sex.UNKNOWN
    date_of_birth: date | None = None
    notes: str | None = Field(default=None, max_length=1000)
    feeding_method: FeedingMethod = FeedingMethod.UNKNOWN
    feeding_notes: str | None = Field(default=None, max_length=500)
    activity_level: ActivityLevel = ActivityLevel.UNKNOWN
    sociability_with_people: Sociability = Sociability.UNKNOWN
    sociability_with_animals: Sociability = Sociability.UNKNOWN
    routine_sensitivity: RoutineSensitivity = RoutineSensitivity.UNKNOWN
    known_triggers: list[str] = Field(default_factory=list, max_length=20)
    personality_notes: str | None = Field(default=None, max_length=1500)

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("known_triggers")
    @classmethod
    def clean_triggers(cls, values: list[str]) -> list[str]:
        cleaned: dict[str, str] = {}
        for value in values:
            trigger = " ".join(value.split())
            if trigger:
                cleaned.setdefault(trigger.casefold(), trigger)
        return list(cleaned.values())


class PetUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    breed: str | None = Field(default=None, max_length=100)
    sex: Sex | None = None
    date_of_birth: date | None = None
    notes: str | None = Field(default=None, max_length=1000)
    feeding_method: FeedingMethod | None = None
    feeding_notes: str | None = Field(default=None, max_length=500)
    activity_level: ActivityLevel | None = None
    sociability_with_people: Sociability | None = None
    sociability_with_animals: Sociability | None = None
    routine_sensitivity: RoutineSensitivity | None = None
    known_triggers: list[str] | None = Field(default=None, max_length=20)
    personality_notes: str | None = Field(default=None, max_length=1500)

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        return " ".join(value.split()) if value is not None else None

    @field_validator("known_triggers")
    @classmethod
    def clean_triggers(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        cleaned: dict[str, str] = {}
        for value in values:
            trigger = " ".join(value.split())
            if trigger:
                cleaned.setdefault(trigger.casefold(), trigger)
        return list(cleaned.values())

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
