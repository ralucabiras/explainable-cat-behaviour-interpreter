import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cv2

from app.video_dataset.models import (
    ClipStatus,
    DatasetSplit,
    ObservableAction,
    VideoDatasetManifest,
)


def load_manifest(path: Path) -> VideoDatasetManifest:
    return VideoDatasetManifest.model_validate_json(path.read_text(encoding="utf-8"))


def save_manifest(manifest: VideoDatasetManifest, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def inspect_media(manifest: VideoDatasetManifest, media_root: Path) -> VideoDatasetManifest:
    updated = []
    for clip in manifest.clips:
        if not clip.relative_path or clip.status == ClipStatus.EXCLUDED:
            updated.append(clip)
            continue
        path = (media_root / clip.relative_path).resolve()
        if media_root.resolve() not in path.parents:
            raise ValueError(f"{clip.id}: relative_path escapes the media root")
        if not path.is_file():
            raise ValueError(f"{clip.id}: media file does not exist: {clip.relative_path}")
        capture = cv2.VideoCapture(str(path))
        try:
            fps = float(capture.get(cv2.CAP_PROP_FPS))
            frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            ok, first_frame = capture.read()
            if not capture.isOpened() or not ok or fps <= 0 or frames < 2:
                raise ValueError(f"{clip.id}: file is not a decodable video")
        finally:
            capture.release()
        updated.append(
            clip.model_copy(
                update={
                    "sha256": _sha256(path),
                    "perceptual_signature": _difference_hash(first_frame),
                    "duration_seconds": round(frames / fps, 3),
                    "fps": round(fps, 3),
                    "width": width,
                    "height": height,
                }
            )
        )
    return manifest.model_copy(update={"clips": updated})


def assign_grouped_splits(
    manifest: VideoDatasetManifest, seed: int = 2026
) -> VideoDatasetManifest:
    included = [clip for clip in manifest.clips if clip.status == ClipStatus.INCLUDED]
    groups: dict[str, list] = defaultdict(list)
    for clip in included:
        groups[clip.group_id].append(clip)
    group_ids = sorted(groups)
    random.Random(seed).shuffle(group_ids)
    targets = {
        DatasetSplit.TRAIN: 0.70 * len(included),
        DatasetSplit.VALIDATION: 0.15 * len(included),
        DatasetSplit.TEST: 0.15 * len(included),
    }
    counts = Counter()
    assignments = {}
    for group_id in group_ids:
        split = min(targets, key=lambda item: (counts[item] / max(targets[item], 1), item.value))
        assignments[group_id] = split
        counts[split] += len(groups[group_id])
    return manifest.model_copy(
        update={
            "clips": [
                clip.model_copy(update={"split": assignments[clip.group_id]})
                if clip.status == ClipStatus.INCLUDED
                else clip
                for clip in manifest.clips
            ]
        }
    )


def build_report(manifest: VideoDatasetManifest) -> dict[str, Any]:
    included = [clip for clip in manifest.clips if clip.status == ClipStatus.INCLUDED]
    class_counts = Counter(clip.action.value for clip in included)
    group_counts = {
        action.value: len({clip.group_id for clip in included if clip.action == action})
        for action in ObservableAction
        if action != ObservableAction.UNCERTAIN
    }
    exact_duplicates = _duplicate_groups(included, "sha256")
    perceptual_duplicates = _duplicate_groups(included, "perceptual_signature")
    trainable_actions = [
        action
        for action, count in sorted(class_counts.items())
        if action != ObservableAction.UNCERTAIN.value
        and count >= 40
        and group_counts.get(action, 0) >= 5
    ]
    if len(included) >= 250 and len(trainable_actions) >= 4:
        verdict = "training_ready"
    elif len(included) >= 100:
        verdict = "exploratory_only"
    else:
        verdict = "insufficient_data"
    return {
        "dataset_version": manifest.dataset_version,
        "total_candidates": len(manifest.clips),
        "included_clips": len(included),
        "class_counts": dict(sorted(class_counts.items())),
        "independent_groups_by_action": group_counts,
        "split_counts": dict(sorted(Counter(clip.split.value for clip in included).items())),
        "exact_duplicate_groups": exact_duplicates,
        "possible_visual_duplicate_groups": perceptual_duplicates,
        "trainable_actions": trainable_actions,
        "feasibility_verdict": verdict,
        "thresholds": {
            "minimum_total_for_training": 250,
            "minimum_clips_per_action": 40,
            "minimum_groups_per_action": 5,
        },
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _difference_hash(frame) -> str:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (9, 8))
    bits = resized[:, 1:] > resized[:, :-1]
    value = sum(int(bit) << index for index, bit in enumerate(bits.flatten()))
    return f"{value:016x}"


def _duplicate_groups(clips: list, field: str) -> list[list[str]]:
    values: dict[str, list[str]] = defaultdict(list)
    for clip in clips:
        value = getattr(clip, field)
        if value:
            values[value].append(clip.id)
    return sorted((sorted(ids) for ids in values.values() if len(ids) > 1), key=lambda ids: ids[0])
