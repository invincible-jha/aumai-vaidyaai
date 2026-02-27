"""Quickstart examples for aumai-vaidyaai.

IMPORTANT DISCLAIMER: This tool does not provide medical advice.
All outputs are for educational and informational purposes only.
Consult a qualified healthcare professional for any medical concern.
In an emergency, call 108 (India) or your local emergency number immediately.

Demonstrates symptom normalisation, condition matching, Ayurvedic perspectives,
triage urgency classification, and multi-system health assessments.

Run this file directly to verify your installation:

    python examples/quickstart.py
"""

from aumai_vaidyaai.core import AYUSHAdvisor, ConditionMatcher, HealthAdvisor, SymptomDatabase
from aumai_vaidyaai.models import (
    MEDICAL_DISCLAIMER,
    HealthAssessment,
    MedicalSystem,
    SimpleSymptom,
)


# ---------------------------------------------------------------------------
# Demo 1: Normalise symptom strings using SymptomDatabase
# ---------------------------------------------------------------------------


def demo_symptom_normalisation() -> None:
    """Convert plain symptom name strings into structured SimpleSymptom objects."""
    print("\n--- Demo 1: Symptom Normalisation ---")

    db = SymptomDatabase()

    raw_symptoms = ["fever", "headache", "cough", "joint pain", "fatigue"]
    print("Normalising symptoms:")
    for name in raw_symptoms:
        symptom: SimpleSymptom = db.normalise(name)
        print(
            f"  '{name}' -> name='{symptom.name}' "
            f"body_area='{symptom.body_area}' severity='{symptom.severity}'"
        )

    # get_body_area can be called directly without creating a SimpleSymptom
    print(f"\nbody_area('chest pain') = '{db.get_body_area('chest pain')}'")
    print(f"body_area('unknown xyz') = '{db.get_body_area('unknown xyz')}'  (default: general)")

    all_known = db.all_symptom_names()
    print(f"\nTotal known symptoms in database: {len(all_known)}")


# ---------------------------------------------------------------------------
# Demo 2: Rule-based condition matching and urgency triage
# ---------------------------------------------------------------------------


def demo_condition_matching() -> None:
    """Match a set of symptoms against the built-in condition knowledge base."""
    print("\n--- Demo 2: Condition Matching and Triage ---")

    # Routine scenario: common cold symptoms
    matcher = ConditionMatcher()
    cold_symptoms = [
        SimpleSymptom(name="runny nose", body_area="head", severity="mild"),
        SimpleSymptom(name="sneezing", body_area="head", severity="mild"),
        SimpleSymptom(name="sore throat", body_area="head", severity="mild"),
        SimpleSymptom(name="mild fever", body_area="general", severity="mild"),
    ]

    matched = matcher.match(cold_symptoms)
    urgency = matcher.assess_urgency(matched)

    print("Symptoms: runny nose, sneezing, sore throat, mild fever")
    print(f"Matched conditions ({len(matched)}):")
    for condition in matched[:3]:
        print(
            f"  {condition['name']} ({condition['icd_code']}) "
            f"likelihood={condition['likelihood_pct']}% urgency={condition['urgency']}"
        )
    print(f"Overall triage urgency: {urgency}")

    # Emergency scenario: acute coronary syndrome indicators
    print()
    chest_symptoms = [
        SimpleSymptom(name="chest pain", body_area="chest", severity="severe"),
        SimpleSymptom(name="left arm pain", body_area="chest", severity="severe"),
        SimpleSymptom(name="breathlessness", body_area="chest", severity="severe"),
        SimpleSymptom(name="sweating", body_area="general", severity="moderate"),
    ]

    matched_emergency = matcher.match(chest_symptoms)
    urgency_emergency = matcher.assess_urgency(matched_emergency)

    print("Symptoms: chest pain, left arm pain, breathlessness, sweating")
    print(f"Matched conditions ({len(matched_emergency)}):")
    for condition in matched_emergency[:2]:
        print(f"  {condition['name']} urgency={condition['urgency']}")
    print(f"Overall triage urgency: {urgency_emergency}  <- CALL 108 IMMEDIATELY")


# ---------------------------------------------------------------------------
# Demo 3: Ayurvedic wellness perspectives via AYUSHAdvisor
# ---------------------------------------------------------------------------


def demo_ayush_advisor() -> None:
    """Get Ayurvedic general wellness suggestions for a symptom set."""
    print("\n--- Demo 3: Ayurvedic Wellness Perspectives ---")

    advisor = AYUSHAdvisor()

    symptoms = [
        SimpleSymptom(name="fever", body_area="general", severity="mild"),
        SimpleSymptom(name="cough", body_area="chest", severity="mild"),
    ]

    suggestions = advisor.ayurvedic_perspective(symptoms)

    print("Symptoms: fever, cough")
    print("Ayurvedic wellness suggestions:")
    # Print all but the last two lines which are the boilerplate disclaimer/consult note
    for suggestion in suggestions[:-2]:
        print(f"  - {suggestion}")

    print(f"\n[Mandatory disclaimer appended: {bool(MEDICAL_DISCLAIMER in suggestions)}]")


# ---------------------------------------------------------------------------
# Demo 4: Full health assessment — allopathy perspective
# ---------------------------------------------------------------------------


def demo_allopathy_assessment() -> None:
    """Run a complete HealthAssessment under the allopathy medical system."""
    print("\n--- Demo 4: Allopathy Health Assessment ---")

    advisor = HealthAdvisor()

    symptoms = [
        SimpleSymptom(name="fever", body_area="general", severity="moderate"),
        SimpleSymptom(name="body ache", body_area="general", severity="moderate"),
        SimpleSymptom(name="fatigue", body_area="general", severity="moderate"),
        SimpleSymptom(name="headache", body_area="head", severity="mild"),
        SimpleSymptom(name="cough", body_area="chest", severity="mild"),
    ]

    assessment: HealthAssessment = advisor.assess(symptoms, system=MedicalSystem.allopathy)

    print(f"Medical system   : {assessment.system.value}")
    print(f"Urgency level    : {assessment.urgency}")
    print(f"Conditions found : {len(assessment.possible_conditions)}")
    for condition in assessment.possible_conditions[:3]:
        print(
            f"  {condition['name']} ({condition['icd_code']}) "
            f"likelihood={condition['likelihood_pct']}%"
        )

    print(f"\nRecommended actions ({len(assessment.recommended_actions)}):")
    # Skip the trailing disclaimer line for brevity
    for action in assessment.recommended_actions[:-1]:
        print(f"  - {action}")

    print(f"\nDisclaimer present: {bool(assessment.disclaimer)}")


# ---------------------------------------------------------------------------
# Demo 5: Multi-system comparison — Ayurveda vs Allopathy
# ---------------------------------------------------------------------------


def demo_multi_system_comparison() -> None:
    """Compare recommendations for the same symptoms across two medical systems."""
    print("\n--- Demo 5: Multi-System Comparison ---")

    advisor = HealthAdvisor()

    symptoms = [
        SimpleSymptom(name="joint pain", body_area="musculoskeletal", severity="moderate"),
        SimpleSymptom(name="fatigue", body_area="general", severity="mild"),
        SimpleSymptom(name="weakness", body_area="general", severity="mild"),
    ]

    systems_to_compare = [MedicalSystem.allopathy, MedicalSystem.ayurveda]

    for system in systems_to_compare:
        assessment = advisor.assess(symptoms, system=system)
        print(f"\nSystem: {system.value.upper()}")
        print(f"  Urgency  : {assessment.urgency}")
        print(f"  Conditions: {[c['name'] for c in assessment.possible_conditions[:2]]}")
        # Show first two system-specific actions (before the disclaimer)
        for action in assessment.recommended_actions[:2]:
            print(f"  Action   : {action}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run all aumai-vaidyaai quickstart demos."""
    print("=== aumai-vaidyaai Quickstart ===")
    print()
    print(MEDICAL_DISCLAIMER)

    demo_symptom_normalisation()
    demo_condition_matching()
    demo_ayush_advisor()
    demo_allopathy_assessment()
    demo_multi_system_comparison()

    print("\nAll demos completed successfully.")
    print()
    print(MEDICAL_DISCLAIMER)


if __name__ == "__main__":
    main()
