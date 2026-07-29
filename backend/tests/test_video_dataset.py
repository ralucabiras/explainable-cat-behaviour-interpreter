from pathlib import Path

import cv2
import numpy as np
import pytest
from pydantic import ValidationError

from app.video_dataset.models import VideoDatasetManifest
from app.video_dataset.service import (
    assign_grouped_splits,
    build_report,
    inspect_media,
)


def test_included_clip_requires_path_permission_and_license() -> None:
    with pytest.raises(ValidationError, match="relative_path"):
        _manifest(
            [
                {
                    **_clip("clip-1", "group-1"),
                    "status": "included",
                    "research_use_permitted": True,
                    "license_id": "CC-BY-4.0",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                }
            ]
        )


def test_grouped_split_is_deterministic_and_never_splits_a_group() -> None:
    clips = []
    for index in range(20):
        clips.append(
            {
                **_clip(f"clip-{index}", f"group-{index // 2}"),
                "relative_path": f"clip-{index}.mp4",
                "status": "included",
                "research_use_permitted": True,
                "license_id": "CC-BY-4.0",
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
            }
        )
    manifest = _manifest(clips)
    first = assign_grouped_splits(manifest)
    second = assign_grouped_splits(manifest)
    assert first == second
    for group_id in {clip.group_id for clip in first.clips}:
        assert len({clip.split for clip in first.clips if clip.group_id == group_id}) == 1


def test_inspection_adds_video_metadata_and_duplicate_report(tmp_path: Path) -> None:
    video = tmp_path / "clip.avi"
    writer = cv2.VideoWriter(
        str(video),
        cv2.VideoWriter_fourcc(*"MJPG"),
        10,
        (96, 64),
    )
    for _ in range(5):
        writer.write(np.zeros((64, 96, 3), dtype=np.uint8))
    writer.release()
    base = {
        "relative_path": "clip.avi",
        "status": "included",
        "research_use_permitted": True,
        "license_id": "CC-BY-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
    }
    inspected = inspect_media(
        _manifest(
            [
                {**_clip("clip-1", "group-1"), **base},
                {**_clip("clip-2", "group-2"), **base},
            ]
        ),
        tmp_path,
    )
    assert inspected.clips[0].sha256
    assert inspected.clips[0].duration_seconds == 0.5
    report = build_report(inspected)
    assert report["exact_duplicate_groups"] == [["clip-1", "clip-2"]]
    assert report["feasibility_verdict"] == "insufficient_data"


def _manifest(clips: list[dict]) -> VideoDatasetManifest:
    return VideoDatasetManifest.model_validate(
        {
            "schema_version": "1.0.0",
            "dataset_version": "test",
            "description": "Test manifest",
            "sources": [
                {
                    "id": "source",
                    "name": "Test source",
                    "homepage": "https://example.com",
                    "status": "available",
                }
            ],
            "clips": clips,
        }
    )


def _clip(clip_id: str, group_id: str) -> dict:
    return {
        "id": clip_id,
        "source_id": "source",
        "source_clip_id": clip_id,
        "source_url": f"https://example.com/{clip_id}",
        "action": "resting",
        "group_id": group_id,
    }
