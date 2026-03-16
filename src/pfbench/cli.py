from __future__ import annotations

import json
import platform
from pathlib import Path

import typer

from pfbench import __version__
from pfbench.evaluation import write_leaderboard, write_report
from pfbench.generation import generate_dataset_bundle
from pfbench.powerflow.cases import available_cases
from pfbench.release import build_release_package
from pfbench.utils import repo_root

app = typer.Typer(help="pfbench command line interface")


@app.command("doctor")
def doctor() -> None:
    checks = {
        "pfbench_version": __version__,
        "python": platform.python_version(),
        "repo_root": str(repo_root()),
        "expected_files_present": all(
            (repo_root() / rel).exists()
            for rel in [
                "README.md",
                "environment.yml",
                "configs/dataset.yaml",
                "configs/solver.yaml",
                "schemas/question_item.schema.json",
                "schemas/scenario_record.schema.json",
            ]
        ),
        "supported_cases": available_cases(),
    }
    try:
        import pandapower

        checks["pandapower"] = {"installed": True, "version": pandapower.__version__}
    except Exception as exc:
        checks["pandapower"] = {"installed": False, "error": str(exc)}
    typer.echo(json.dumps(checks, ensure_ascii=False, indent=2))


@app.command("generate-demo")
def generate_demo(
    config: Path = typer.Option(Path("configs/dataset.yaml"), exists=True, readable=True, help="Dataset YAML config."),
    out: Path = typer.Option(Path("examples/demo_questions.jsonl"), help="Output question JSONL path."),
) -> None:
    bundle = generate_dataset_bundle(config_path=config, out_path=out)
    if bundle["questions"]:
        reference_question = out.parent / "reference_question_item.json"
        reference_question.write_text(json.dumps(bundle["questions"][0], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if bundle["scenarios"]:
        reference_scenario = out.parent / "reference_scenario_record.json"
        reference_scenario.write_text(json.dumps(bundle["scenarios"][0], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    typer.echo(json.dumps({
        "num_questions": len(bundle["questions"]),
        "num_scenarios": len(bundle["scenarios"]),
        "num_failed_scenarios": len(bundle["failed_scenarios"]),
        "questions_path": str(bundle["questions_path"]),
        "scenarios_path": str(bundle["scenarios_path"]),
        "failed_scenarios_path": str(bundle["failed_scenarios_path"]),
        "manifest_path": str(bundle["manifest_path"]),
    }, ensure_ascii=False, indent=2))


@app.command("report")
def report(
    dataset: Path = typer.Option(..., exists=True, readable=True, help="Question dataset JSONL path."),
    out: Path | None = typer.Option(None, help="Optional markdown report path."),
) -> None:
    summary, report_path = write_report(dataset_path=dataset, report_path=out)
    typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))
    typer.echo(f"Report written to {report_path}")


@app.command("leaderboard")
def leaderboard(
    predictions: Path = typer.Option(..., exists=True, readable=True, help="Prediction JSONL path."),
    dataset: Path = typer.Option(Path("examples/demo_questions.jsonl"), exists=True, readable=True, help="Question dataset JSONL path."),
    out: Path | None = typer.Option(None, help="Optional leaderboard JSON path."),
) -> None:
    summary, leaderboard_path = write_leaderboard(
        dataset_path=dataset,
        predictions_path=predictions,
        out_path=out,
    )
    typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))
    typer.echo(f"Leaderboard written to {leaderboard_path}")


@app.command("build-release")
def build_release(
    config: Path = typer.Option(Path("configs/release_v1.yaml"), exists=True, readable=True, help="Frozen release YAML config."),
    out: Path = typer.Option(Path("datasets/pfbench/v1"), help="Output release directory."),
) -> None:
    release = build_release_package(config_path=config, release_dir=out)
    typer.echo(json.dumps({
        "dataset_id": release["manifest"]["dataset_id"],
        "dataset_version": release["manifest"]["dataset_version"],
        "num_questions": release["summary"]["num_questions"],
        "num_scenarios": release["summary"]["num_scenarios"],
        "num_failed_scenarios": release["summary"]["num_failed_scenarios"],
        "release_dir": str(release["release_dir"]),
        "questions_path": str(release["questions_path"]),
        "report_path": str(release["report_path"]),
        "checksum_path": str(release["checksum_path"]),
    }, ensure_ascii=False, indent=2))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
