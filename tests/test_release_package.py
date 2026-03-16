from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from pfbench.cli import app
from pfbench.release import build_release_package

RUNNER = CliRunner()


def _write_release_config(path: Path) -> None:
    path.write_text(
        """
dataset:
  dataset_id: pfbench_release_test
  dataset_version: "1.0.0-test"
  generated_at: "2026-03-15T00:00:00Z"
  seed: 123
  cases:
    - case14
  num_scenarios_per_case: 1
  split_ratios:
    dev: 1.0
    public_test: 0.0
    private_test: 0.0
  query_families:
    - direct_bus_vm
    - is_voltage_violation_present
  export:
    jsonl: true
    parquet: true
""".strip() + "\n",
        encoding="utf-8",
    )


def test_build_release_package(tmp_path: Path) -> None:
    config = tmp_path / "release.yaml"
    release_dir = tmp_path / "datasets" / "pfbench" / "v1"
    _write_release_config(config)

    release = build_release_package(config_path=config, release_dir=release_dir)

    assert release["questions_path"] == release_dir / "questions.jsonl"
    assert (release_dir / "scenarios.jsonl").exists()
    assert (release_dir / "failed_scenarios.jsonl").exists()
    assert (release_dir / "questions.parquet").exists()
    assert (release_dir / "scenarios.parquet").exists()
    assert (release_dir / "manifest.json").exists()
    assert (release_dir / "report.md").exists()
    assert (release_dir / "README.md").exists()
    assert (release_dir / "RELEASE_NOTES.md").exists()
    assert (release_dir / "LICENSE_AND_REDISTRIBUTION.md").exists()
    assert (release_dir / "FIELD_DICTIONARY.md").exists()
    assert (release_dir / "SCHEMA_DOCS.md").exists()
    assert (release_dir / "QUALITY_REPORT.md").exists()
    assert (release_dir / "SUBMISSION_FRAMING.md").exists()
    assert (release_dir / "VALIDATION_SUMMARY.json").exists()
    assert (release_dir / "FAIR_METADATA.json").exists()
    assert (release_dir / "CHECKSUMS.sha256").exists()
    assert (release_dir / "configs" / "generation_config.yaml").exists()
    assert (release_dir / "configs" / "solver.yaml").exists()
    assert (release_dir / "schemas" / "question_item.schema.json").exists()
    assert (release_dir / "schemas" / "scenario_record.schema.json").exists()

    validation = json.loads((release_dir / "VALIDATION_SUMMARY.json").read_text(encoding="utf-8"))
    assert validation["validation_passed"] is True
    assert validation["manifest_counts_match_files"] is True
    assert validation["questions_reference_known_scenarios"] is True

    license_text = (release_dir / "LICENSE_AND_REDISTRIBUTION.md").read_text(encoding="utf-8")
    assert "BSD 3-Clause" in license_text

    checksum_text = (release_dir / "CHECKSUMS.sha256").read_text(encoding="utf-8")
    assert "questions.jsonl" in checksum_text
    assert "README.md" in checksum_text


def test_build_release_cli(tmp_path: Path) -> None:
    config = tmp_path / "release.yaml"
    release_dir = tmp_path / "datasets" / "pfbench" / "v1"
    _write_release_config(config)

    result = RUNNER.invoke(app, ["build-release", "--config", str(config), "--out", str(release_dir)])
    assert result.exit_code == 0, result.stdout
    assert (release_dir / "questions.jsonl").exists()
    assert "dataset_version" in result.stdout
