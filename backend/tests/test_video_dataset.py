import io
import json
import subprocess
import zipfile
from pathlib import Path

import cv2
import numpy as np
import pytest
from pydantic import ValidationError

from app.video_dataset.animal_kingdom import audit_action_archive, iter_annotation_rows
from app.video_dataset.cloud import GCloudStorage
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


def test_animal_kingdom_audit_aggregates_frames_and_preserves_multilabels(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "annotations.zip"
    _write_action_archive(archive)

    report, manifest = audit_action_archive(archive, dataset_version="test-ak")

    assert report["total_source_videos"] == 2
    assert report["target_source_videos"] == 2
    assert report["mapped_video_counts"] == {"eating": 1, "grooming": 2}
    assert report["media_archive_members_verified"] is False
    assert len(manifest.clips) == 3
    assert {clip.group_id for clip in manifest.clips} == {"ak-aaaaaaab", "ak-aaaaaaac"}
    assert all(clip.status.value == "candidate" for clip in manifest.clips)
    assert all(not clip.research_use_permitted for clip in manifest.clips)


def test_action_annotation_parser_rejects_malformed_rows() -> None:
    with pytest.raises(ValueError, match="Malformed action annotation"):
        list(iter_annotation_rows(io.BytesIO(b"header\nnot enough columns\n")))


def test_cloud_inventory_is_sorted_and_totals_bytes() -> None:
    payload = [
        _cloud_item("raw/z.zip", "20"),
        _cloud_item("raw/a.zip", "10"),
    ]

    class FakeStorage(GCloudStorage):
        def __init__(self) -> None:
            pass

        def _run(self, *arguments: str) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(arguments, 0, stdout=json.dumps(payload), stderr="")

    inventory = FakeStorage().inventory("bucket", "raw")
    assert inventory.total_bytes == 30
    assert [item.name for item in inventory.objects] == ["raw/a.zip", "raw/z.zip"]


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


def _write_action_archive(path: Path) -> None:
    workbook = io.BytesIO()
    shared = ["S/N", "action_category", "action", "index", "segment", "count"]
    shared.extend(["Feeding", "Eating", "middle", "Maintenance", "Grooming"])
    shared_xml = "".join(f"<si><t>{value}</t></si>" for value in shared)
    sheet_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
      <row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c>
        <c r="C1" t="s"><v>2</v></c><c r="D1" t="s"><v>3</v></c>
        <c r="E1" t="s"><v>4</v></c><c r="F1" t="s"><v>5</v></c></row>
      <row r="2"><c r="A2"><v>1</v></c><c r="B2" t="s"><v>6</v></c>
        <c r="C2" t="s"><v>7</v></c><c r="D2"><v>40</v></c>
        <c r="E2" t="s"><v>8</v></c><c r="F2"><v>2</v></c></row>
      <row r="3"><c r="A3"><v>2</v></c><c r="B3" t="s"><v>9</v></c>
        <c r="C3" t="s"><v>10</v></c><c r="D3"><v>58</v></c>
        <c r="E3" t="s"><v>8</v></c><c r="F3"><v>3</v></c></row>
    </sheetData></worksheet>"""
    with zipfile.ZipFile(workbook, "w") as nested:
        nested.writestr(
            "xl/sharedStrings.xml",
            "<?xml version='1.0'?><sst xmlns='http://schemas.openxmlformats.org/"
            f"spreadsheetml/2006/main'>{shared_xml}</sst>",
        )
        nested.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    header = "original_vido_id video_id frame_id path labels type\n"
    train = header + (
        "AAAAAAAB 1 1 AAAAAAAB/AAAAAAAB_t000001.jpg 40,58 train\n"
        "AAAAAAAB 1 2 AAAAAAAB/AAAAAAAB_t000002.jpg 40,58 train\n"
    )
    test = header + "AAAAAAAC 2 1 AAAAAAAC/AAAAAAAC_t000001.jpg 58 test\n"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("action_recognition/annotation/df_action.xlsx", workbook.getvalue())
        archive.writestr("action_recognition/annotation/train.csv", train)
        archive.writestr("action_recognition/annotation/val.csv", test)


def _cloud_item(name: str, size: str) -> dict:
    return {
        "type": "cloud_object",
        "metadata": {
            "name": name,
            "size": size,
            "crc32c": "checksum",
            "generation": "1",
            "storageClass": "STANDARD",
        },
    }
