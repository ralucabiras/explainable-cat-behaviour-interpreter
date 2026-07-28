import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.evaluation.cli import main
from app.evaluation.metrics import classification_metrics
from app.evaluation.models import EvaluationDataset
from app.evaluation.runner import CONFIGURATIONS, evaluate_dataset, load_dataset

DATASET_PATH = Path(__file__).parents[1] / "evaluation" / "datasets" / "v1.json"


def test_dataset_rejects_duplicate_scenario_ids() -> None:
    scenario = {
        "id": "duplicate",
        "pet": {"name": "Test Cat"},
        "observation": {"text_description": "Resting with a loose body."},
        "expected_state": "relaxed",
    }
    with pytest.raises(ValidationError, match="Duplicate scenario IDs"):
        EvaluationDataset.model_validate(
            {
                "dataset_version": "test",
                "description": "Test data",
                "synthetic_data_notice": "Synthetic only.",
                "scenarios": [scenario, scenario],
            }
        )


def test_classification_metrics_match_hand_calculation() -> None:
    rows = [
        _metric_row("relaxed", "relaxed", 0.8),
        _metric_row("relaxed", "playful", 0.6),
        _metric_row("playful", "playful", 0.9),
        _metric_row("playful", "relaxed", 0.7),
    ]
    metrics = classification_metrics(rows)
    assert metrics["accuracy"] == 0.5
    assert metrics["per_state"]["relaxed"]["precision"] == 0.5
    assert metrics["per_state"]["relaxed"]["recall"] == 0.5
    assert metrics["confusion_matrix"]["playful"]["relaxed"] == 1


async def test_versioned_dataset_runs_all_configurations_deterministically() -> None:
    dataset = load_dataset(DATASET_PATH)
    first = await evaluate_dataset(dataset)
    second = await evaluate_dataset(dataset)

    assert first == second
    assert len(first["predictions"]) == len(dataset.scenarios) * len(CONFIGURATIONS)
    assert set(first["metrics"]) == set(CONFIGURATIONS)
    safety_rows = [
        row for row in first["predictions"] if row["expected_safety_escalation"]
    ]
    assert safety_rows
    assert all(row["predicted_safety_escalation"] for row in safety_rows)
    assert all(row["predicted_state"] == "potentially_unwell" for row in safety_rows)


def test_cli_writes_artifacts_and_compares_baseline(tmp_path: Path) -> None:
    output = tmp_path / "first"
    assert main(["--dataset", str(DATASET_PATH), "--output", str(output)]) == 0
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert (output / "predictions.csv").exists()
    assert (output / "summary.json").exists()
    assert (output / "confusion_matrix_fused.csv").exists()
    assert report["dataset_version"] == "1.0.0"

    comparison = tmp_path / "comparison"
    assert (
        main(
            [
                "--dataset",
                str(DATASET_PATH),
                "--output",
                str(comparison),
                "--compare",
                str(output / "report.json"),
            ]
        )
        == 0
    )


def test_cli_reports_invalid_dataset(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{}", encoding="utf-8")
    assert main(["--dataset", str(invalid), "--output", str(tmp_path / "out")]) == 2


def _metric_row(expected: str, predicted: str, confidence: float) -> dict:
    return {
        "expected_state": expected,
        "predicted_state": predicted,
        "confidence": confidence,
        "correct": expected == predicted,
        "expected_safety_escalation": False,
        "predicted_safety_escalation": False,
    }
