import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.ai.context_analyser import ContextAnalyser
from app.ai.fusion import FusionEngine
from app.ai.safety import assess_safety
from app.ai.text_analyser import TextAnalyser
from app.evaluation import EVALUATOR_VERSION, TAXONOMY_VERSION
from app.evaluation.metrics import STATE_NAMES, classification_metrics, safety_metrics
from app.evaluation.models import EvaluationDataset, EvaluationScenario
from app.models.observation import AnalysisStatus, ModalityResult, Observation
from app.models.pet import Pet

CONFIGURATIONS = ("text_only", "context_only", "fused")


def load_dataset(path: Path) -> EvaluationDataset:
    return EvaluationDataset.model_validate_json(path.read_text(encoding="utf-8"))


async def evaluate_dataset(dataset: EvaluationDataset) -> dict[str, Any]:
    predictions = []
    for scenario in sorted(dataset.scenarios, key=lambda item: item.id):
        predictions.extend(await _evaluate_scenario(scenario))

    by_configuration = {}
    for configuration in CONFIGURATIONS:
        rows = [row for row in predictions if row["configuration"] == configuration]
        by_configuration[configuration] = {
            **classification_metrics(rows),
            "safety": safety_metrics(rows),
        }
    return {
        "dataset_version": dataset.dataset_version,
        "evaluator_version": EVALUATOR_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "synthetic_data_notice": dataset.synthetic_data_notice,
        "metrics": by_configuration,
        "predictions": predictions,
    }


async def _evaluate_scenario(scenario: EvaluationScenario) -> list[dict[str, Any]]:
    fixed_time = datetime(2025, 1, 1, tzinfo=UTC)
    pet = Pet(
        id=f"evaluation-pet-{scenario.id}",
        **scenario.pet.model_dump(),
        created_at=fixed_time,
        updated_at=fixed_time,
    )
    observation = Observation(
        id=f"evaluation-observation-{scenario.id}",
        pet_id=pet.id,
        **scenario.observation.model_dump(),
        created_at=fixed_time,
        updated_at=fixed_time,
    )
    text_result = await TextAnalyser().analyse(observation)
    context_result = await ContextAnalyser().analyse(observation, pet)
    safety_text = " ".join(
        part
        for part in (
            observation.text_description,
            observation.context.routine_changes,
            " ".join(observation.context.known_triggers),
        )
        if part
    )
    safety = assess_safety(safety_text)
    empty = ModalityResult(status=AnalysisStatus.COMPLETED)
    results = {
        "text_only": await FusionEngine().combine(text_result, empty, safety),
        "context_only": await FusionEngine().combine(empty, context_result, safety),
        "fused": await FusionEngine().combine(text_result, context_result, safety),
    }
    rows = []
    for configuration, result in results.items():
        predicted_state = result.label.value if result.label else "uncertain"
        rows.append(
            {
                "scenario_id": scenario.id,
                "configuration": configuration,
                "expected_state": scenario.expected_state.value,
                "predicted_state": predicted_state,
                "confidence": result.confidence or 0.0,
                "correct": predicted_state == scenario.expected_state.value,
                "expected_safety_escalation": scenario.expected_safety_escalation,
                "predicted_safety_escalation": result.safety_escalation,
                "evidence": [item.model_dump(mode="json") for item in result.evidence],
                "alternatives": [item.model_dump(mode="json") for item in result.alternatives],
            }
        )
    return rows


def write_artifacts(report: dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary = {
        "dataset_version": report["dataset_version"],
        "evaluator_version": report["evaluator_version"],
        "taxonomy_version": report["taxonomy_version"],
        "synthetic_data_notice": report["synthetic_data_notice"],
        "configurations": {
            name: {
                key: metrics[key]
                for key in (
                    "total",
                    "correct",
                    "accuracy",
                    "macro_f1",
                    "weighted_f1",
                    "uncertain_coverage",
                    "safety",
                )
            }
            for name, metrics in report["metrics"].items()
        },
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (output / "predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "scenario_id",
            "configuration",
            "expected_state",
            "predicted_state",
            "confidence",
            "correct",
            "expected_safety_escalation",
            "predicted_safety_escalation",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in report["predictions"])
    for configuration in CONFIGURATIONS:
        matrix = report["metrics"][configuration]["confusion_matrix"]
        with (output / f"confusion_matrix_{configuration}.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.writer(handle)
            writer.writerow(["expected/predicted", *STATE_NAMES])
            for expected in STATE_NAMES:
                values = (matrix[expected][predicted] for predicted in STATE_NAMES)
                writer.writerow([expected, *values])


def compare_predictions(report: dict[str, Any], baseline_path: Path) -> list[str]:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if not isinstance(baseline, dict) or not isinstance(baseline.get("predictions"), list):
        raise ValueError("Comparison file must be an evaluation report containing predictions")
    baseline_rows = {
        (row["scenario_id"], row["configuration"]): (
            row["predicted_state"],
            row["predicted_safety_escalation"],
        )
        for row in baseline["predictions"]
    }
    current_rows = {
        (row["scenario_id"], row["configuration"]): (
            row["predicted_state"],
            row["predicted_safety_escalation"],
        )
        for row in report["predictions"]
    }
    changes = []
    for key in sorted(baseline_rows.keys() | current_rows.keys()):
        if baseline_rows.get(key) != current_rows.get(key):
            previous = baseline_rows.get(key)
            current = current_rows.get(key)
            changes.append(f"{key[0]} [{key[1]}]: {previous} -> {current}")
    return changes
