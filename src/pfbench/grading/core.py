from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _grade_json_fields(item: dict[str, Any], prediction: dict[str, Any], exact: bool) -> dict[str, Any]:
    gold = item["gold_answer"]
    grader = item["grader"]
    required_fields = grader.get("required_fields", list(gold.keys()))
    float_tol = float(grader.get("float_tol", 0.0))

    missing = [field for field in required_fields if field not in prediction]
    if missing:
        return {
            "question_id": item["question_id"],
            "passed": False,
            "score": 0.0,
            "details": {"missing_fields": missing},
        }

    field_results: dict[str, Any] = {}
    correct = 0
    for field in required_fields:
        pred = prediction[field]
        gold_value = gold[field]
        pred_num = _to_float(pred)
        gold_num = _to_float(gold_value)
        if not exact and pred_num is not None and gold_num is not None:
            passed = abs(pred_num - gold_num) <= float_tol
        else:
            passed = pred == gold_value
        field_results[field] = {
            "pred": pred,
            "gold": gold_value,
            "passed": passed,
        }
        if passed:
            correct += 1

    score = correct / len(required_fields) if required_fields else 0.0
    return {
        "question_id": item["question_id"],
        "passed": correct == len(required_fields),
        "score": score,
        "details": {"field_results": field_results},
    }


def grade_answer(item: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    grader = item["grader"]
    grader_type = grader.get("type", "json_numeric_tolerance")
    if grader_type == "json_numeric_tolerance":
        return _grade_json_fields(item, prediction, exact=False)
    if grader_type in {"json_exact", "ranking", "argmax", "argmin"}:
        return _grade_json_fields(item, prediction, exact=True)
    raise ValueError(f"Unsupported grader type: {grader_type}")
