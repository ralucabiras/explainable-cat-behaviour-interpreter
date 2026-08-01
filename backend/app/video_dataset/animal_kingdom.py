import json
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any

from app.video_dataset.models import (
    ClipStatus,
    DatasetSource,
    ObservableAction,
    SourceStatus,
    VideoClip,
    VideoDatasetManifest,
)

ACTION_MAPPING = {
    "Drinking": ObservableAction.DRINKING,
    "Eating": ObservableAction.EATING,
    "Exploring": ObservableAction.EXPLORING,
    "Grooming": ObservableAction.GROOMING,
    "Hissing": ObservableAction.HISSING,
    "Keeping still": ObservableAction.KEEPING_STILL,
    "Licking": ObservableAction.LICKING,
    "Lying Down": ObservableAction.LYING_DOWN,
    "Moving": ObservableAction.LOCOMOTION,
    "Playing": ObservableAction.PLAYING,
    "Resting": ObservableAction.RESTING,
    "Running": ObservableAction.RUNNING,
    "Sitting": ObservableAction.SITTING,
    "Sleeping": ObservableAction.SLEEPING,
    "Walking": ObservableAction.WALKING,
}

EXPECTED_ACTION_ARCHIVES = {
    "action_recognition-20260729T113648Z-1-001.zip",
    "video-002.tar.gz",
}


@dataclass
class _VideoAggregate:
    original_video_id: str
    numeric_video_id: int
    split: str
    frame_count: int = 0
    label_ids: set[int] = field(default_factory=set)


def parse_action_taxonomy(archive: zipfile.ZipFile) -> dict[int, dict[str, Any]]:
    name = _single_entry(archive, "annotation/df_action.xlsx")
    with archive.open(name) as workbook:
        return _read_taxonomy_workbook(workbook)


def iter_annotation_rows(handle: IO[bytes]) -> Iterator[tuple[str, int, int, str, set[int], str]]:
    for line_number, raw in enumerate(handle, start=1):
        line = raw.decode("utf-8-sig").strip()
        if not line or line_number == 1:
            continue
        columns = line.split()
        if len(columns) != 6:
            raise ValueError(f"Malformed action annotation at line {line_number}: {line[:120]}")
        original_id, numeric_id, frame_id, path, labels, split = columns
        if not re.fullmatch(r"[A-Z]{8}", original_id):
            raise ValueError(f"Invalid original video ID at line {line_number}: {original_id}")
        yield (
            original_id,
            int(numeric_id),
            int(frame_id),
            path,
            {int(label) for label in labels.split(",")},
            split,
        )


def audit_action_archive(
    path: Path, dataset_version: str = "animal-kingdom-v1"
) -> tuple[dict, VideoDatasetManifest]:
    aggregates: dict[str, _VideoAggregate] = {}
    with zipfile.ZipFile(path) as archive:
        taxonomy = parse_action_taxonomy(archive)
        csv_names = sorted(
            name for name in archive.namelist() if name.endswith(("/train.csv", "/val.csv"))
        )
        if len(csv_names) != 2:
            raise ValueError("Action archive must contain train.csv and val.csv")
        for csv_name in csv_names:
            with archive.open(csv_name) as handle:
                for original_id, numeric_id, _, _, labels, split in iter_annotation_rows(handle):
                    record = aggregates.setdefault(
                        original_id, _VideoAggregate(original_id, numeric_id, split)
                    )
                    if record.numeric_video_id != numeric_id or record.split != split:
                        raise ValueError(f"Conflicting metadata for video {original_id}")
                    record.frame_count += 1
                    record.label_ids.update(labels)

    unknown_label_ids = sorted(
        {label for record in aggregates.values() for label in record.label_ids} - set(taxonomy)
    )
    if unknown_label_ids:
        raise ValueError(f"Annotations reference unknown labels: {unknown_label_ids}")

    original_counts = Counter()
    mapped_video_counts = Counter()
    split_counts = Counter(record.split for record in aggregates.values())
    candidates = []
    videos_with_target_actions = set()
    for record in sorted(aggregates.values(), key=lambda item: item.original_video_id):
        mapped = set()
        for label_id in record.label_ids:
            name = taxonomy[label_id]["name"]
            original_counts[name] += 1
            if action := ACTION_MAPPING.get(name):
                mapped.add(action)
        for action in sorted(mapped, key=lambda item: item.value):
            mapped_video_counts[action.value] += 1
            videos_with_target_actions.add(record.original_video_id)
            candidates.append(
                VideoClip(
                    id=f"ak-{record.original_video_id.lower()}-{action.value.replace('_', '-')}",
                    source_id="animal_kingdom",
                    source_clip_id=record.original_video_id,
                    source_url=f"video/{record.original_video_id}.mp4",
                    action=action,
                    status=ClipStatus.CANDIDATE,
                    group_id=f"ak-{record.original_video_id.lower()}",
                    annotation_notes=(
                        f"Animal Kingdom {record.split}; {record.frame_count} annotated frames. "
                        "Species and dataset terms require review before inclusion."
                    ),
                )
            )

    report = {
        "dataset_version": dataset_version,
        "source_archive": path.name,
        "total_source_videos": len(aggregates),
        "source_split_counts": dict(sorted(split_counts.items())),
        "target_source_videos": len(videos_with_target_actions),
        "candidate_action_records": len(candidates),
        "mapped_video_counts": dict(sorted(mapped_video_counts.items())),
        "original_action_video_counts": dict(sorted(original_counts.items())),
        "mapped_actions": {name: action.value for name, action in sorted(ACTION_MAPPING.items())},
        "media_member_pattern": "video/{original_video_id}.mp4",
        "media_archive_members_verified": False,
        "species_metadata_available": False,
        "limitations": [
            "Action annotations contain no species field; every candidate requires species review.",
            "Counts are source videos carrying a label, not independent domestic-cat examples.",
            "Archive member existence is not checked during the no-large-download audit.",
            "Dataset licence identifier and redistribution terms must be recorded "
            "before inclusion.",
        ],
    }
    manifest = VideoDatasetManifest(
        schema_version="1.0.0",
        dataset_version=dataset_version,
        description=(
            "Animal Kingdom observable-action candidates aggregated by source video. "
            "Candidates are not approved domestic-cat training data."
        ),
        sources=[
            DatasetSource(
                id="animal_kingdom",
                name="Animal Kingdom",
                homepage="https://sutdcv.github.io/Animal-Kingdom/",
                status=SourceStatus.NEEDS_REVIEW,
                notes="Private research dataset; record the supplied agreement before inclusion.",
            )
        ],
        clips=candidates,
    )
    return report, manifest


def save_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _single_entry(archive: zipfile.ZipFile, suffix: str) -> str:
    matches = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one archive entry ending with {suffix!r}")
    return matches[0]


def _read_taxonomy_workbook(handle: IO[bytes]) -> dict[int, dict[str, Any]]:
    with zipfile.ZipFile(handle) as workbook:
        namespace = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        strings = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
            strings = [
                "".join(node.text or "" for node in item.iterfind(".//m:t", namespace))
                for item in root.findall("m:si", namespace)
            ]
        sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        rows = []
        for row in sheet.findall(".//m:row", namespace):
            values = {}
            for cell in row.findall("m:c", namespace):
                value_node = cell.find("m:v", namespace)
                value = "" if value_node is None else value_node.text or ""
                if cell.get("t") == "s" and value:
                    value = strings[int(value)]
                column = re.match(r"[A-Z]+", cell.get("r", ""))
                if column:
                    values[column.group()] = value
            rows.append(values)
        taxonomy = {}
        for row in rows[1:]:
            label_id = int(row["D"])
            taxonomy[label_id] = {
                "name": row["C"],
                "category": row["B"],
                "segment": row["E"],
                "reported_count": int(float(row["F"])),
            }
        if not taxonomy:
            raise ValueError("Action taxonomy workbook is empty")
        return taxonomy
