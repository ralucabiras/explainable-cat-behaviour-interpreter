import hashlib
import json
from collections import Counter, defaultdict
from enum import StrEnum
from pathlib import Path

from pydantic import Field, model_validator

from app.models.common import APIModel
from app.video_dataset.models import ClipStatus, ObservableAction, VideoDatasetManifest


class SpeciesCategory(StrEnum):
    UNREVIEWED = "unreviewed"
    DOMESTIC_CAT = "domestic_cat"
    WILD_FELINE = "wild_feline"
    OTHER_MAMMAL = "other_mammal"
    NON_MAMMAL = "non_mammal"
    UNCLEAR = "unclear"


class ReviewSuitability(StrEnum):
    UNREVIEWED = "unreviewed"
    SUITABLE = "suitable"
    UNSUITABLE = "unsuitable"
    UNCLEAR = "unclear"


class ReviewItem(APIModel):
    id: str
    source_clip_id: str
    group_id: str
    archive_member: str
    actions: list[ObservableAction]
    selected_for: list[ObservableAction]


class ReviewPlan(APIModel):
    schema_version: str = "1.0.0"
    dataset_version: str
    plan_version: str
    source_archive_uri: str
    seed: int
    requested_per_action: int = Field(gt=0, le=100)
    coverage_by_action: dict[str, int]
    items: list[ReviewItem]

    @model_validator(mode="after")
    def item_ids_and_groups_must_be_unique(self) -> "ReviewPlan":
        if len({item.id for item in self.items}) != len(self.items):
            raise ValueError("Review item IDs must be unique")
        if len({item.group_id for item in self.items}) != len(self.items):
            raise ValueError("A source-video group may appear only once in a review plan")
        return self


class ReviewLabel(APIModel):
    item_id: str
    species: SpeciesCategory = SpeciesCategory.UNREVIEWED
    suitability: ReviewSuitability = ReviewSuitability.UNREVIEWED
    visible_actions: list[ObservableAction] = Field(default_factory=list)
    notes: str = ""


class ReviewSubmission(APIModel):
    schema_version: str = "1.0.0"
    plan_version: str
    labels: list[ReviewLabel]

    @model_validator(mode="after")
    def item_ids_must_be_unique(self) -> "ReviewSubmission":
        ids = [label.item_id for label in self.labels]
        if len(set(ids)) != len(ids):
            raise ValueError("Review label item IDs must be unique")
        return self


def build_review_plan(
    manifest: VideoDatasetManifest,
    source_archive_uri: str,
    per_action: int = 20,
    seed: int = 2026,
    plan_version: str = "review-v1",
) -> ReviewPlan:
    candidates = [clip for clip in manifest.clips if clip.status == ClipStatus.CANDIDATE]
    by_group = defaultdict(list)
    for clip in candidates:
        by_group[clip.group_id].append(clip)
    groups_by_action = defaultdict(list)
    for group_id, clips in by_group.items():
        for action in {clip.action for clip in clips}:
            groups_by_action[action].append(group_id)

    selected: set[str] = set()
    selected_for = defaultdict(set)
    coverage = Counter()
    actions = sorted(
        groups_by_action,
        key=lambda action: (len(groups_by_action[action]), action.value),
    )
    for action in actions:
        ranked = sorted(
            groups_by_action[action],
            key=lambda group_id: (_stable_rank(seed, action.value, group_id), group_id),
        )
        for group_id in ranked:
            if coverage[action.value] >= per_action:
                break
            if group_id in selected:
                continue
            selected.add(group_id)
            selected_for[group_id].add(action)
            for covered in {clip.action for clip in by_group[group_id]}:
                coverage[covered.value] += 1

    items = []
    for group_id in sorted(selected):
        clips = by_group[group_id]
        source_ids = {clip.source_clip_id for clip in clips}
        members = {clip.source_url for clip in clips}
        if len(source_ids) != 1 or len(members) != 1:
            raise ValueError(f"Conflicting source metadata in group {group_id}")
        source_clip_id = next(iter(source_ids))
        items.append(
            ReviewItem(
                id=f"review-{source_clip_id.lower()}",
                source_clip_id=source_clip_id,
                group_id=group_id,
                archive_member=next(iter(members)),
                actions=sorted({clip.action for clip in clips}, key=lambda action: action.value),
                selected_for=sorted(selected_for[group_id], key=lambda action: action.value),
            )
        )
    return ReviewPlan(
        dataset_version=manifest.dataset_version,
        plan_version=plan_version,
        source_archive_uri=source_archive_uri,
        seed=seed,
        requested_per_action=per_action,
        coverage_by_action={action.value: coverage[action.value] for action in actions},
        items=items,
    )


def save_review_plan(plan: ReviewPlan, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(plan.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_review_submission(
    plan: ReviewPlan, submission: ReviewSubmission, require_complete: bool = False
) -> dict:
    if submission.plan_version != plan.plan_version:
        raise ValueError("Review submission plan_version does not match the plan")
    planned = {item.id for item in plan.items}
    submitted = {label.item_id for label in submission.labels}
    unknown = sorted(submitted - planned)
    if unknown:
        raise ValueError(f"Review submission contains unknown item IDs: {unknown[:5]}")
    unreviewed = sorted(planned - submitted)
    incomplete = sorted(
        label.item_id
        for label in submission.labels
        if label.species == SpeciesCategory.UNREVIEWED
        or label.suitability == ReviewSuitability.UNREVIEWED
    )
    if require_complete and (unreviewed or incomplete):
        raise ValueError(
            f"Review is incomplete: {len(unreviewed)} missing and {len(incomplete)} unreviewed"
        )
    return {
        "plan_version": plan.plan_version,
        "planned_items": len(planned),
        "submitted_items": len(submitted),
        "missing_items": len(unreviewed),
        "incomplete_items": len(incomplete),
        "complete": not unreviewed and not incomplete,
        "species_counts": dict(
            sorted(Counter(label.species.value for label in submission.labels).items())
        ),
        "suitability_counts": dict(
            sorted(Counter(label.suitability.value for label in submission.labels).items())
        ),
    }


def _stable_rank(seed: int, action: str, group_id: str) -> str:
    return hashlib.sha256(f"{seed}:{action}:{group_id}".encode()).hexdigest()
