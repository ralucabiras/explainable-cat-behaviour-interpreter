import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

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
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
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


if __name__ == "__main__":
    raise SystemExit(main())
