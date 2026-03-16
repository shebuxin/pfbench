from __future__ import annotations

from typer.testing import CliRunner

from pfbench.cli import app

RUNNER = CliRunner()


def test_cli_help_smoke() -> None:
    result = RUNNER.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "cross-validate" in result.stdout
    assert "generate-demo" in result.stdout
    assert "report" in result.stdout
    assert "build-release" in result.stdout


def test_doctor_smoke() -> None:
    result = RUNNER.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "supported_cases" in result.stdout
