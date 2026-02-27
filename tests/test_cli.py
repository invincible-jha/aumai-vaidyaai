"""Tests for aumai-vaidyaai CLI."""

from __future__ import annotations

from click.testing import CliRunner

from aumai_vaidyaai.cli import main
from aumai_vaidyaai.models import MEDICAL_DISCLAIMER


def test_cli_version() -> None:
    """Version flag must report 0.1.0."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_help() -> None:
    """Help flag should return exit code 0."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "AYUSH" in result.output or "symptom" in result.output.lower()


def test_cli_assess_basic() -> None:
    """Assess command with fever should succeed."""
    runner = CliRunner()
    result = runner.invoke(main, ["assess", "--symptoms", "fever,cough"])
    assert result.exit_code == 0
    assert "fever" in result.output.lower()


def test_cli_assess_includes_disclaimer() -> None:
    """Assess output must include the medical disclaimer."""
    runner = CliRunner()
    result = runner.invoke(main, ["assess", "--symptoms", "fever"])
    assert result.exit_code == 0
    assert MEDICAL_DISCLAIMER in result.output


def test_cli_assess_shows_urgency() -> None:
    """Assess output should show URGENCY LEVEL."""
    runner = CliRunner()
    result = runner.invoke(main, ["assess", "--symptoms", "fever,headache"])
    assert result.exit_code == 0
    assert "URGENCY" in result.output.upper()


def test_cli_assess_allopathy_system() -> None:
    """Assess with allopathy system should succeed and show allopathy content."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["assess", "--symptoms", "fever", "--system", "allopathy"]
    )
    assert result.exit_code == 0
    assert "MBBS" in result.output or "physician" in result.output.lower()


def test_cli_assess_ayurveda_system() -> None:
    """Assess with ayurveda system should succeed and show Ayurvedic content."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["assess", "--symptoms", "fever", "--system", "ayurveda"]
    )
    assert result.exit_code == 0
    combined = result.output.lower()
    assert "ayurvedic" in combined or "giloy" in combined or "bams" in combined


def test_cli_assess_yoga_system() -> None:
    """Assess with yoga system should succeed."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["assess", "--symptoms", "fever", "--system", "yoga"]
    )
    assert result.exit_code == 0


def test_cli_assess_emergency_symptoms() -> None:
    """Assess with emergency symptoms should show emergency warning."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["assess", "--symptoms", "chest_pain,left_arm_pain"]
    )
    assert result.exit_code == 0
    assert "EMERGENCY" in result.output.upper() or "emergency" in result.output.lower()


def test_cli_assess_missing_symptoms_fails() -> None:
    """Assess command without --symptoms should fail."""
    runner = CliRunner()
    result = runner.invoke(main, ["assess"])
    assert result.exit_code != 0


def test_cli_assess_invalid_system_fails() -> None:
    """Assess with invalid --system should fail."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["assess", "--symptoms", "fever", "--system", "magic"]
    )
    assert result.exit_code != 0


def test_cli_symptoms_command() -> None:
    """Symptoms command should list all known symptoms."""
    runner = CliRunner()
    result = runner.invoke(main, ["symptoms"])
    assert result.exit_code == 0
    assert "fever" in result.output.lower()
    assert "KNOWN SYMPTOMS" in result.output.upper()


def test_cli_symptoms_command_includes_disclaimer() -> None:
    """Symptoms output must include the medical disclaimer."""
    runner = CliRunner()
    result = runner.invoke(main, ["symptoms"])
    assert result.exit_code == 0
    assert MEDICAL_DISCLAIMER in result.output


def test_cli_symptoms_shows_count() -> None:
    """Symptoms output should show a total count."""
    runner = CliRunner()
    result = runner.invoke(main, ["symptoms"])
    assert result.exit_code == 0
    # Should show something like "(N total)"
    assert "total" in result.output.lower()


def test_cli_assess_shows_possible_conditions() -> None:
    """Assess output should show possible conditions if any match."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["assess", "--symptoms", "high_fever,severe_headache,eye_pain"],
    )
    assert result.exit_code == 0
    assert "POSSIBLE CONDITIONS" in result.output.upper() or "conditions" in result.output.lower()


def test_cli_assess_comma_separated_symptoms() -> None:
    """Assess command should handle comma-separated symptoms properly."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["assess", "--symptoms", "fever,cough,headache,fatigue"],
    )
    assert result.exit_code == 0
    assert result.exit_code == 0


def test_cli_serve_help() -> None:
    """Serve command help should show port and host options."""
    runner = CliRunner()
    result = runner.invoke(main, ["serve", "--help"])
    assert result.exit_code == 0
    assert "port" in result.output.lower() or "host" in result.output.lower()
