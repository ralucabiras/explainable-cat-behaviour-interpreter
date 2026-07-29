from enum import StrEnum

from pydantic import Field, model_validator

from app.models.common import APIModel


class ObservableAction(StrEnum):
    RESTING = "resting"
    LOCOMOTION = "locomotion"
    PLAYING = "playing"
    GROOMING = "grooming"
    EATING = "eating"
    UNCERTAIN = "uncertain"


class ClipStatus(StrEnum):
    CANDIDATE = "candidate"
    INCLUDED = "included"
    EXCLUDED = "excluded"


class DatasetSplit(StrEnum):
    UNASSIGNED = "unassigned"
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


class SourceStatus(StrEnum):
    AVAILABLE = "available"
    REQUIRES_REQUEST = "requires_request"
    UNAVAILABLE = "unavailable"
    NEEDS_REVIEW = "needs_review"


class DatasetSource(APIModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    name: str
    homepage: str
    status: SourceStatus
    license_id: str | None = None
    license_url: str | None = None
    notes: str | None = None


class VideoClip(APIModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    source_id: str
    source_clip_id: str
    source_url: str
    license_id: str | None = None
    license_url: str | None = None
    research_use_permitted: bool = False
    redistribution_permitted: bool = False
    attribution: str | None = None
    relative_path: str | None = None
    action: ObservableAction
    status: ClipStatus = ClipStatus.CANDIDATE
    exclusion_reason: str | None = None
    group_id: str
    cat_id: str | None = None
    uploader_id: str | None = None
    split: DatasetSplit = DatasetSplit.UNASSIGNED
    sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    perceptual_signature: str | None = Field(default=None, pattern=r"^[a-f0-9]{16}$")
    duration_seconds: float | None = Field(default=None, gt=0)
    fps: float | None = Field(default=None, gt=0)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    annotation_notes: str | None = None

    @model_validator(mode="after")
    def included_clip_must_be_usable(self) -> "VideoClip":
        if self.status == ClipStatus.INCLUDED:
            if not self.relative_path:
                raise ValueError("Included clips require relative_path")
            if not self.research_use_permitted:
                raise ValueError("Included clips must permit research use")
            if not self.license_id or not self.license_url:
                raise ValueError("Included clips require license provenance")
        if self.status == ClipStatus.EXCLUDED and not self.exclusion_reason:
            raise ValueError("Excluded clips require exclusion_reason")
        return self


class VideoDatasetManifest(APIModel):
    schema_version: str
    dataset_version: str
    description: str
    sources: list[DatasetSource] = Field(default_factory=list)
    clips: list[VideoClip] = Field(default_factory=list)

    @model_validator(mode="after")
    def references_must_be_valid(self) -> "VideoDatasetManifest":
        source_ids = [source.id for source in self.sources]
        clip_ids = [clip.id for clip in self.clips]
        duplicate_sources = _duplicates(source_ids)
        duplicate_clips = _duplicates(clip_ids)
        if duplicate_sources:
            raise ValueError(f"Duplicate source IDs: {', '.join(duplicate_sources)}")
        if duplicate_clips:
            raise ValueError(f"Duplicate clip IDs: {', '.join(duplicate_clips)}")
        unknown = sorted({clip.source_id for clip in self.clips} - set(source_ids))
        if unknown:
            raise ValueError(f"Unknown source IDs: {', '.join(unknown)}")
        return self


def _duplicates(values: list[str]) -> list[str]:
    return sorted({value for value in values if values.count(value) > 1})
