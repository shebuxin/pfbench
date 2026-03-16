from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pfbench.grading import grade_answer
from pfbench.io import read_jsonl


def _prediction_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    for key in ("prediction", "answer", "response"):
        value = row.get(key)
        if isinstance(value, dict):
            return value
    return None


def summarize_predictions(dataset_path: Path, predictions_path: Path) -> dict[str, Any]:
    questions = {
        str(row["question_id"]): row
        for row in read_jsonl(dataset_path)
    }
    predictions = list(read_jsonl(predictions_path))

    matched_question_ids: set[str] = set()
    unknown_question_ids: list[str] = []
    query_stats: dict[str, list[float]] = defaultdict(list)
    split_stats: dict[str, list[float]] = defaultdict(list)
    passed = 0
    total_score = 0.0

    for row in predictions:
        question_id = str(row.get("question_id", ""))
        question = questions.get(question_id)
        if question is None:
            unknown_question_ids.append(question_id)
            continue

        matched_question_ids.add(question_id)
        payload = _prediction_payload(row)
        if payload is None:
            result = {
                "passed": False,
                "score": 0.0,
            }
        else:
            result = grade_answer(question, payload)

        score = float(result["score"])
        total_score += score
        passed += int(bool(result["passed"]))
        query_stats[str(question["query_family"])].append(score)
        split_stats[str(question["split"])].append(score)

    def _stats_map(values_by_key: dict[str, list[float]]) -> dict[str, dict[str, Any]]:
        output: dict[str, dict[str, Any]] = {}
        for key, scores in sorted(values_by_key.items()):
            count = len(scores)
            passed_count = sum(1 for score in scores if score >= 1.0)
            output[key] = {
                "count": count,
                "num_passed": passed_count,
                "accuracy": 0.0 if count == 0 else round(passed_count / count, 6),
                "mean_score": 0.0 if count == 0 else round(sum(scores) / count, 6),
            }
        return output

    matched_count = len(matched_question_ids)
    missing_question_ids = sorted(set(questions) - matched_question_ids)
    return {
        "dataset_path": str(dataset_path),
        "predictions_path": str(predictions_path),
        "num_questions_in_dataset": len(questions),
        "num_predictions_read": len(predictions),
        "num_predictions_matched": matched_count,
        "num_missing_predictions": len(missing_question_ids),
        "num_unknown_question_ids": len(unknown_question_ids),
        "num_passed": passed,
        "accuracy": 0.0 if matched_count == 0 else round(passed / matched_count, 6),
        "mean_score": 0.0 if matched_count == 0 else round(total_score / matched_count, 6),
        "by_query_family": _stats_map(query_stats),
        "by_split": _stats_map(split_stats),
        "missing_question_ids": missing_question_ids,
        "unknown_question_ids": sorted(question_id for question_id in unknown_question_ids if question_id),
        "prediction_formats_seen": dict(sorted(Counter(
            next(
                (key for key in ("prediction", "answer", "response") if isinstance(row.get(key), dict)),
                "missing",
            )
            for row in predictions
        ).items())),
    }


def write_leaderboard(
    dataset_path: Path,
    predictions_path: Path,
    out_path: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    summary = summarize_predictions(dataset_path=dataset_path, predictions_path=predictions_path)
    if out_path is None:
        out_path = predictions_path.with_name(f"{predictions_path.stem}_leaderboard.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary, out_path
