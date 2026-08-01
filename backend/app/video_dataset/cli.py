import argparse
import json
import sys
import tempfile
from pathlib import Path

from pydantic import ValidationError

from app.core.config import get_settings
from app.video_dataset.animal_kingdom import (
    EXPECTED_ACTION_ARCHIVES,
    audit_action_archive,
    save_json,
)
from app.video_dataset.cloud import GCloudStorage
from app.video_dataset.review import (
    ReviewPlan,
    ReviewSubmission,
    build_review_plan,
    save_review_plan,
    validate_review_submission,
)
from app.video_dataset.service import (
    assign_grouped_splits,
    build_report,
    inspect_media,
    load_manifest,
    save_manifest,
)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Prepare a licensed cat-action video dataset.")
    subcommands = command.add_subparsers(dest="command", required=True)
    validate = subcommands.add_parser("validate")
    validate.add_argument("--manifest", type=Path, required=True)
    inspect = subcommands.add_parser("inspect")
    inspect.add_argument("--manifest", type=Path, required=True)
    inspect.add_argument("--media-root", type=Path, required=True)
    inspect.add_argument("--output", type=Path, required=True)
    split = subcommands.add_parser("split")
    split.add_argument("--manifest", type=Path, required=True)
    split.add_argument("--output", type=Path, required=True)
    split.add_argument("--seed", type=int, default=2026)
    report = subcommands.add_parser("report")
    report.add_argument("--manifest", type=Path, required=True)
    report.add_argument("--output", type=Path)
    cloud_inventory = subcommands.add_parser(
        "cloud-inventory", description="Inventory a private GCS dataset prefix."
    )
    _add_cloud_arguments(cloud_inventory)
    cloud_inventory.add_argument("--output", type=Path, required=True)
    animal_kingdom = subcommands.add_parser(
        "animal-kingdom-audit",
        description="Parse local Animal Kingdom annotations without reading media archives.",
    )
    animal_kingdom.add_argument("--annotation-zip", type=Path, required=True)
    animal_kingdom.add_argument("--output-dir", type=Path, required=True)
    cloud_audit = subcommands.add_parser(
        "animal-kingdom-cloud-audit",
        description="Inventory GCS and download only the small action annotation ZIP.",
    )
    _add_cloud_arguments(cloud_audit)
    cloud_audit.add_argument("--output-dir", type=Path, required=True)
    cloud_audit.add_argument("--work-dir", type=Path)
    review_sample = subcommands.add_parser(
        "review-sample",
        description="Create a deterministic species-review plan from action candidates.",
    )
    review_sample.add_argument("--manifest", type=Path, required=True)
    review_sample.add_argument("--output", type=Path, required=True)
    review_sample.add_argument("--source-archive-uri", required=True)
    review_sample.add_argument("--per-action", type=int, default=20)
    review_sample.add_argument("--seed", type=int, default=2026)
    review_sample.add_argument("--plan-version", default="review-v1")
    review_validate = subcommands.add_parser(
        "review-validate", description="Validate species-review labels against their plan."
    )
    review_validate.add_argument("--plan", type=Path, required=True)
    review_validate.add_argument("--labels", type=Path, required=True)
    review_validate.add_argument("--require-complete", action="store_true")
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "cloud-inventory":
            storage = GCloudStorage(args.gcloud)
            inventory = storage.inventory(_bucket(args.bucket), args.prefix)
            save_json(inventory.model_dump(mode="json"), args.output)
            print(f"Inventoried {len(inventory.objects)} objects ({inventory.total_bytes} bytes)")
            return 0
        if args.command == "animal-kingdom-audit":
            _write_animal_kingdom_audit(args.annotation_zip, args.output_dir)
            return 0
        if args.command == "animal-kingdom-cloud-audit":
            _run_cloud_audit(args)
            return 0
        if args.command == "review-sample":
            manifest = load_manifest(args.manifest)
            plan = build_review_plan(
                manifest,
                source_archive_uri=args.source_archive_uri,
                per_action=args.per_action,
                seed=args.seed,
                plan_version=args.plan_version,
            )
            save_review_plan(plan, args.output)
            print(f"Selected {len(plan.items)} unique source videos; wrote {args.output}")
            return 0
        if args.command == "review-validate":
            plan = ReviewPlan.model_validate_json(args.plan.read_text(encoding="utf-8"))
            submission = ReviewSubmission.model_validate_json(
                args.labels.read_text(encoding="utf-8")
            )
            result = validate_review_submission(plan, submission, args.require_complete)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        manifest = load_manifest(args.manifest)
        if args.command == "validate":
            print(f"Valid manifest: {len(manifest.clips)} clip records")
        elif args.command == "inspect":
            save_manifest(inspect_media(manifest, args.media_root), args.output)
            print(f"Inspected media and wrote {args.output}")
        elif args.command == "split":
            save_manifest(assign_grouped_splits(manifest, args.seed), args.output)
            print(f"Assigned grouped splits and wrote {args.output}")
        else:
            report = json.dumps(build_report(manifest), indent=2, sort_keys=True) + "\n"
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(report, encoding="utf-8")
            else:
                print(report, end="")
        return 0
    except (OSError, ValueError, ValidationError) as error:
        print(f"Dataset preparation failed: {error}", file=sys.stderr)
        return 2


def _add_cloud_arguments(command: argparse.ArgumentParser) -> None:
    settings = get_settings()
    command.add_argument("--bucket", default=settings.gcs_dataset_bucket)
    command.add_argument("--prefix", default=settings.gcs_dataset_prefix)
    command.add_argument("--gcloud", help="Optional path to gcloud or gcloud.cmd")


def _bucket(value: str | None) -> str:
    if not value:
        raise ValueError("A bucket is required via --bucket or GCS_DATASET_BUCKET")
    return value.removeprefix("gs://").strip("/")


def _write_animal_kingdom_audit(annotation_zip: Path, output_dir: Path) -> dict:
    report, manifest = audit_action_archive(annotation_zip)
    save_json(report, output_dir / "action-report.json")
    save_manifest(manifest, output_dir / "candidate-manifest.json")
    print(
        f"Indexed {report['total_source_videos']} source videos; "
        f"wrote {report['candidate_action_records']} action candidates"
    )
    return report


def _run_cloud_audit(args: argparse.Namespace) -> None:
    bucket = _bucket(args.bucket)
    prefix = args.prefix.strip("/")
    storage = GCloudStorage(args.gcloud)
    inventory = storage.inventory(bucket, prefix)
    present_names = {Path(item.name).name for item in inventory.objects}
    missing = sorted(EXPECTED_ACTION_ARCHIVES - present_names)
    if missing:
        raise ValueError(f"Required action-recognition cloud objects are missing: {missing}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    save_json(inventory.model_dump(mode="json"), args.output_dir / "cloud-inventory.json")
    annotation_name = next(
        name
        for name in present_names
        if name.startswith("action_recognition-") and name.endswith(".zip")
    )
    if args.work_dir:
        work_dir = args.work_dir
        work_dir.mkdir(parents=True, exist_ok=True)
        annotation_zip = work_dir / annotation_name
        storage.download(f"gs://{bucket}/{prefix}/{annotation_name}", annotation_zip)
        report = _write_animal_kingdom_audit(annotation_zip, args.output_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="animal-kingdom-") as temporary:
            annotation_zip = Path(temporary) / annotation_name
            storage.download(f"gs://{bucket}/{prefix}/{annotation_name}", annotation_zip)
            report = _write_animal_kingdom_audit(annotation_zip, args.output_dir)
    cloud_report = {
        "mode": "no-large-download",
        "bucket": bucket,
        "prefix": prefix,
        "cloud_objects": len(inventory.objects),
        "cloud_bytes": inventory.total_bytes,
        "downloaded_object": annotation_name,
        "downloaded_large_media": False,
        "required_action_archives_present": True,
        "indexed_source_videos": report["total_source_videos"],
        "target_source_videos": report["target_source_videos"],
    }
    save_json(cloud_report, args.output_dir / "cloud-audit-summary.json")


if __name__ == "__main__":
    raise SystemExit(main())
