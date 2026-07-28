from collections import Counter
from typing import Any

from app.models.observation import BehaviourState

STATE_NAMES = [state.value for state in BehaviourState]


def classification_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    correct = sum(row["correct"] for row in rows)
    expected_counts = Counter(row["expected_state"] for row in rows)
    per_state: dict[str, dict[str, float | int]] = {}
    matrix = {expected: {predicted: 0 for predicted in STATE_NAMES} for expected in STATE_NAMES}

    for row in rows:
        matrix[row["expected_state"]][row["predicted_state"]] += 1

    for state in STATE_NAMES:
        true_positive = matrix[state][state]
        false_positive = sum(matrix[other][state] for other in STATE_NAMES if other != state)
        false_negative = sum(matrix[state][other] for other in STATE_NAMES if other != state)
        precision = _divide(true_positive, true_positive + false_positive)
        recall = _divide(true_positive, true_positive + false_negative)
        f1 = _divide(2 * precision * recall, precision + recall)
        per_state[state] = {
            "support": expected_counts[state],
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    macro_f1 = sum(float(item["f1"]) for item in per_state.values()) / len(STATE_NAMES)
    weighted_f1 = _divide(
        sum(float(per_state[state]["f1"]) * expected_counts[state] for state in STATE_NAMES),
        total,
    )
    uncertain_count = sum(row["predicted_state"] == BehaviourState.UNCERTAIN.value for row in rows)
    return {
        "total": total,
        "correct": correct,
        "accuracy": round(_divide(correct, total), 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "uncertain_coverage": round(_divide(uncertain_count, total), 4),
        "per_state": per_state,
        "confusion_matrix": matrix,
        "calibration": calibration_metrics(rows),
    }


def safety_metrics(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    true_positive = sum(
        row["expected_safety_escalation"] and row["predicted_safety_escalation"] for row in rows
    )
    false_positive = sum(
        not row["expected_safety_escalation"] and row["predicted_safety_escalation"]
        for row in rows
    )
    false_negative = sum(
        row["expected_safety_escalation"] and not row["predicted_safety_escalation"]
        for row in rows
    )
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": round(_divide(true_positive, true_positive + false_positive), 4),
        "recall": round(_divide(true_positive, true_positive + false_negative), 4),
    }


def calibration_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    bins = []
    weighted_gap = 0.0
    for index in range(5):
        lower = index / 5
        upper = (index + 1) / 5
        members = [
            row
            for row in rows
            if lower <= row["confidence"] <= upper
            and (index == 4 or row["confidence"] < upper)
        ]
        mean_confidence = _divide(sum(row["confidence"] for row in members), len(members))
        accuracy = _divide(sum(row["correct"] for row in members), len(members))
        gap = abs(mean_confidence - accuracy)
        weighted_gap += gap * len(members)
        bins.append(
            {
                "lower": lower,
                "upper": upper,
                "count": len(members),
                "mean_evidence_strength": round(mean_confidence, 4),
                "accuracy": round(accuracy, 4),
                "gap": round(gap, 4),
            }
        )
    return {
        "notice": (
            "Confidence is deterministic rule-evidence strength, not a medically validated "
            "probability."
        ),
        "expected_calibration_error": round(_divide(weighted_gap, len(rows)), 4),
        "bins": bins,
    }


def _divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
