from enum import StrEnum

from pydantic import Field, model_validator

from app.models.common import APIModel, StoredModel


class FeedingStatus(StrEnum):
    FED = "fed"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    UNKNOWN = "unknown"


class ObservationContext(APIModel):
    location: str | None = Field(default=None, max_length=120)
    time_of_day: str | None = Field(default=None, max_length=60)
    feeding_status: FeedingStatus = FeedingStatus.UNKNOWN
    unfamiliar_people_present: bool = False
    unfamiliar_animals_present: bool = False
    recent_travel_or_relocation: bool = False
    recent_play: bool = False
    routine_changes: str | None = Field(default=None, max_length=500)
    known_triggers: list[str] = Field(default_factory=list, max_length=20)


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaReference(APIModel):
    filename: str
    content_type: str
    storage_key: str | None = None


class ModalityResult(APIModel):
    status: AnalysisStatus = AnalysisStatus.PENDING
    label: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    detected_features: list[str] = Field(default_factory=list)
    explanation: str | None = None


class AnalysisBundle(APIModel):
    text: ModalityResult = Field(default_factory=ModalityResult)
    context: ModalityResult = Field(default_factory=ModalityResult)
    video: ModalityResult = Field(default_factory=ModalityResult)
    audio: ModalityResult = Field(default_factory=ModalityResult)
    fusion: ModalityResult = Field(default_factory=ModalityResult)


class ObservationCreate(APIModel):
    pet_id: str = Field(min_length=1)
    text_description: str = Field(min_length=1, max_length=5000)
    context: ObservationContext = Field(default_factory=ObservationContext)
    video: MediaReference | None = None
    audio: MediaReference | None = None

    @model_validator(mode="after")
    def require_consent_for_people_in_media(self) -> "ObservationCreate":
        # Consent capture belongs in the upload flow; media references are placeholders for now.
        return self


class Observation(StoredModel, ObservationCreate):
    analysis: AnalysisBundle = Field(default_factory=AnalysisBundle)

