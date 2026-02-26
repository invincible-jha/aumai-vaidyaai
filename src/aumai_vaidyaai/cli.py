"""CLI entry point for aumai-vaidyaai."""

from __future__ import annotations

import sys

import click

from .core import HealthAdvisor, SymptomDatabase
from .models import MEDICAL_DISCLAIMER, MedicalSystem, SimpleSymptom


@click.group()
@click.version_option()
def main() -> None:
    """AumAI VaidyaAI — AYUSH + allopathy symptom checker for rural health."""


@main.command("assess")
@click.option(
    "--symptoms",
    required=True,
    help="Comma-separated symptom names (e.g. 'fever,headache,body_ache')",
)
@click.option(
    "--system",
    default="allopathy",
    type=click.Choice([s.value for s in MedicalSystem]),
    help="Medical system for recommendations",
)
def assess(symptoms: str, system: str) -> None:
    """Assess symptoms and generate health recommendations."""
    symptom_db = SymptomDatabase()
    advisor = HealthAdvisor()

    # Parse comma-separated symptom list
    raw_symptoms = [s.strip().replace("_", " ") for s in symptoms.split(",") if s.strip()]
    symptom_objects: list[SimpleSymptom] = [symptom_db.normalise(s) for s in raw_symptoms]

    medical_system = MedicalSystem(system)
    assessment = advisor.assess(symptom_objects, medical_system)

    click.echo(f"\n{'='*60}")
    click.echo(f"HEALTH ASSESSMENT ({medical_system.value.upper()} PERSPECTIVE)")
    click.echo(f"{'='*60}")

    click.echo(f"\nURGENCY LEVEL: {assessment.urgency.upper()}")
    if assessment.urgency == "emergency":
        click.echo("*** SEEK EMERGENCY MEDICAL CARE IMMEDIATELY ***")

    click.echo(f"\nSYMPTOMS ASSESSED:")
    for s in assessment.symptoms:
        click.echo(f"  - {s.name} ({s.body_area}, {s.severity})")

    if assessment.possible_conditions:
        click.echo(f"\nPOSSIBLE CONDITIONS:")
        for cond in assessment.possible_conditions[:5]:
            click.echo(f"  - {cond['name']} [ICD: {cond.get('icd_code', 'N/A')}]")
            click.echo(f"    Likelihood: {cond.get('likelihood_pct', 0)}%")
            click.echo(f"    {cond.get('description', '')}")
    else:
        click.echo("\nNo specific conditions matched. Consult a healthcare professional.")

    click.echo(f"\nRECOMMENDED ACTIONS:")
    for action in assessment.recommended_actions:
        click.echo(f"  - {action}")

    click.echo(f"\nDISCLAIMER: {MEDICAL_DISCLAIMER}\n")


@main.command("symptoms")
def symptoms() -> None:
    """List all known symptoms in the database."""
    db = SymptomDatabase()
    all_symptoms = db.all_symptom_names()
    click.echo(f"\nKNOWN SYMPTOMS ({len(all_symptoms)} total):")
    for i, symptom in enumerate(sorted(all_symptoms), 1):
        click.echo(f"  {i:3}. {symptom}")
    click.echo(f"\n{MEDICAL_DISCLAIMER}\n")


@main.command("serve")
@click.option("--port", default=8000, help="Port to serve on")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
def serve(port: int, host: str) -> None:
    """Start the VaidyaAI API server."""
    try:
        import uvicorn
    except ImportError:
        click.echo("Error: uvicorn is required. Install with: pip install uvicorn", err=True)
        sys.exit(1)
    uvicorn.run("aumai_vaidyaai.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
