import argparse
import asyncio
import sys
from pathlib import Path

from pydantic import ValidationError

from app.evaluation.runner import (
    compare_predictions,
    evaluate_dataset,
    load_dataset,
    write_artifacts,
)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Evaluate the deterministic behaviour baseline.")
    command.add_argument("--dataset", type=Path, required=True, help="Versioned JSON dataset.")
    command.add_argument("--output", type=Path, required=True, help="Artifact output directory.")
    command.add_argument(
        "--compare", type=Path, help="Prior report.json to compare predictions with."
    )
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        dataset = load_dataset(args.dataset)
        report = asyncio.run(evaluate_dataset(dataset))
        write_artifacts(report, args.output)
        print(
            f"Evaluated {len(dataset.scenarios)} scenarios from dataset "
            f"{dataset.dataset_version}; artifacts: {args.output}"
        )
        if args.compare:
            changes = compare_predictions(report, args.compare)
            if changes:
                print("Prediction regression detected:", file=sys.stderr)
                for change in changes:
                    print(f"- {change}", file=sys.stderr)
                return 1
            print("Predictions match the comparison baseline.")
        return 0
    except (OSError, ValueError, ValidationError) as error:
        print(f"Evaluation failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
