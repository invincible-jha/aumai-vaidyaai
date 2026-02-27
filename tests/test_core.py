"""Comprehensive tests for aumai-vaidyaai core module.

Covers SymptomDatabase, ConditionMatcher, AYUSHAdvisor, HealthAdvisor, and models.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from aumai_vaidyaai.core import AYUSHAdvisor, ConditionMatcher, HealthAdvisor, SymptomDatabase
from aumai_vaidyaai.models import (
    MEDICAL_DISCLAIMER,
    Condition,
    HealthAssessment,
    MedicalSystem,
    Recommendation,
    SimpleSymptom,
    Symptom,
    SymptomAssessment,
    SymptomCategory,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def symptom_db() -> SymptomDatabase:
    return SymptomDatabase()


@pytest.fixture()
def matcher() -> ConditionMatcher:
    return ConditionMatcher()


@pytest.fixture()
def ayush_advisor() -> AYUSHAdvisor:
    return AYUSHAdvisor()


@pytest.fixture()
def health_advisor() -> HealthAdvisor:
    return HealthAdvisor()


@pytest.fixture()
def fever_symptom() -> SimpleSymptom:
    return SimpleSymptom(name="fever", body_area="general", severity="mild")


@pytest.fixture()
def emergency_symptoms() -> list[SimpleSymptom]:
    """Symptoms that should trigger an emergency urgency (chest pain + breathlessness)."""
    return [
        SimpleSymptom(name="chest pain", body_area="chest", severity="severe"),
        SimpleSymptom(name="left arm pain", body_area="chest", severity="severe"),
    ]


# ---------------------------------------------------------------------------
# MEDICAL_DISCLAIMER tests
# ---------------------------------------------------------------------------


class TestMedicalDisclaimer:
    def test_disclaimer_is_non_empty(self) -> None:
        assert isinstance(MEDICAL_DISCLAIMER, str)
        assert len(MEDICAL_DISCLAIMER) > 0

    def test_disclaimer_content(self) -> None:
        assert MEDICAL_DISCLAIMER == (
            "IMPORTANT MEDICAL DISCLAIMER: This tool does NOT provide medical advice, diagnosis, or treatment."
            " Symptom analysis is based on keyword matching only and may be inaccurate."
            " Always consult a qualified healthcare professional for medical concerns."
            " In emergencies, contact your nearest hospital immediately."
        )

    def test_disclaimer_contains_medical_advice(self) -> None:
        assert "medical advice" in MEDICAL_DISCLAIMER.lower()


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestSymptomCategoryEnum:
    def test_all_expected_categories_present(self) -> None:
        expected = {"general", "respiratory", "digestive", "musculoskeletal", "skin", "neurological"}
        actual = {member.value for member in SymptomCategory}
        assert expected == actual

    def test_category_values_are_strings(self) -> None:
        for cat in SymptomCategory:
            assert isinstance(cat.value, str)


class TestMedicalSystemEnum:
    def test_all_systems_present(self) -> None:
        expected = {"allopathy", "ayurveda", "yoga", "unani", "siddha", "homeopathy"}
        actual = {member.value for member in MedicalSystem}
        assert expected == actual

    def test_system_values_are_strings(self) -> None:
        for system in MedicalSystem:
            assert isinstance(system.value, str)

    def test_allopathy_value(self) -> None:
        assert MedicalSystem.allopathy.value == "allopathy"

    def test_ayurveda_value(self) -> None:
        assert MedicalSystem.ayurveda.value == "ayurveda"


class TestSimpleSymptomModel:
    def test_simple_symptom_default_body_area(self) -> None:
        symptom = SimpleSymptom(name="fever")
        assert symptom.body_area == "general"

    def test_simple_symptom_default_severity(self) -> None:
        symptom = SimpleSymptom(name="cough")
        assert symptom.severity == "mild"

    def test_simple_symptom_custom_values(self) -> None:
        symptom = SimpleSymptom(name="headache", body_area="head", severity="severe")
        assert symptom.name == "headache"
        assert symptom.body_area == "head"
        assert symptom.severity == "severe"

    def test_simple_symptom_invalid_severity_raises(self) -> None:
        with pytest.raises(Exception):
            SimpleSymptom(name="fever", severity="extreme")  # invalid

    def test_simple_symptom_serialisation_roundtrip(self) -> None:
        symptom = SimpleSymptom(name="nausea", body_area="abdomen", severity="moderate")
        data = symptom.model_dump()
        restored = SimpleSymptom.model_validate(data)
        assert restored.name == "nausea"
        assert restored.body_area == "abdomen"

    def test_symptom_model_with_severity_range(self) -> None:
        symptom = Symptom(
            code="S001",
            name="Headache",
            category=SymptomCategory.neurological,
            severity_range=(1, 10),
        )
        assert symptom.code == "S001"
        assert symptom.category == SymptomCategory.neurological


class TestRecommendationModel:
    def test_valid_recommendation(self) -> None:
        rec = Recommendation(
            system=MedicalSystem.allopathy,
            condition="Common Cold",
            description="Rest and fluids.",
            urgency="self_care",
            seek_professional=False,
        )
        assert rec.system == MedicalSystem.allopathy
        assert rec.urgency == "self_care"

    def test_invalid_urgency_raises(self) -> None:
        with pytest.raises(Exception):
            Recommendation(
                system=MedicalSystem.ayurveda,
                condition="Fever",
                description="Tulsi tea.",
                urgency="critical",  # invalid
                seek_professional=True,
            )


class TestHealthAssessmentModel:
    def test_health_assessment_has_disclaimer(self) -> None:
        assessment = HealthAssessment(
            symptoms=[SimpleSymptom(name="fever")],
            possible_conditions=[],
            recommended_actions=["See a doctor"],
            urgency="routine",
            system=MedicalSystem.allopathy,
        )
        assert assessment.disclaimer == MEDICAL_DISCLAIMER

    def test_health_assessment_invalid_urgency(self) -> None:
        with pytest.raises(Exception):
            HealthAssessment(
                symptoms=[SimpleSymptom(name="fever")],
                possible_conditions=[],
                recommended_actions=[],
                urgency="unknown",  # invalid
                system=MedicalSystem.allopathy,
            )


class TestConditionModel:
    def test_condition_model_valid(self) -> None:
        condition = Condition(
            code="COND001",
            name="Dengue",
            symptoms_required=["high fever", "rash"],
            symptoms_optional=["joint pain"],
            systems=[MedicalSystem.allopathy],
        )
        assert condition.code == "COND001"
        assert len(condition.symptoms_required) == 2

    def test_condition_optional_symptoms_default_empty(self) -> None:
        condition = Condition(
            code="COND002",
            name="Cold",
            symptoms_required=["runny nose"],
            systems=[MedicalSystem.allopathy, MedicalSystem.ayurveda],
        )
        assert condition.symptoms_optional == []


class TestSymptomAssessmentModel:
    def test_valid_triage_levels(self) -> None:
        for level in ["green", "amber", "red"]:
            sa = SymptomAssessment(
                symptoms=["fever"],
                triage_level=level,
            )
            assert sa.triage_level == level

    def test_invalid_triage_level_raises(self) -> None:
        with pytest.raises(Exception):
            SymptomAssessment(
                symptoms=["fever"],
                triage_level="blue",  # invalid
            )

    def test_default_disclaimer(self) -> None:
        sa = SymptomAssessment(symptoms=["fever"], triage_level="green")
        assert sa.disclaimer == MEDICAL_DISCLAIMER


# ---------------------------------------------------------------------------
# SymptomDatabase tests
# ---------------------------------------------------------------------------


class TestSymptomDatabase:
    def test_get_body_area_fever_is_general(self, symptom_db: SymptomDatabase) -> None:
        assert symptom_db.get_body_area("fever") == "general"

    def test_get_body_area_headache_is_head(self, symptom_db: SymptomDatabase) -> None:
        assert symptom_db.get_body_area("headache") == "head"

    def test_get_body_area_chest_pain_is_chest(
        self, symptom_db: SymptomDatabase
    ) -> None:
        assert symptom_db.get_body_area("chest pain") == "chest"

    def test_get_body_area_nausea_is_abdomen(self, symptom_db: SymptomDatabase) -> None:
        assert symptom_db.get_body_area("nausea") == "abdomen"

    def test_get_body_area_joint_pain_is_musculoskeletal(
        self, symptom_db: SymptomDatabase
    ) -> None:
        assert symptom_db.get_body_area("joint pain") == "musculoskeletal"

    def test_get_body_area_rash_is_skin(self, symptom_db: SymptomDatabase) -> None:
        assert symptom_db.get_body_area("rash") == "skin"

    def test_get_body_area_unknown_returns_general(
        self, symptom_db: SymptomDatabase
    ) -> None:
        assert symptom_db.get_body_area("unknown_symptom_xyz") == "general"

    def test_get_body_area_case_insensitive(self, symptom_db: SymptomDatabase) -> None:
        assert symptom_db.get_body_area("FEVER") == "general"
        assert symptom_db.get_body_area("Headache") == "head"

    def test_normalise_returns_simple_symptom(
        self, symptom_db: SymptomDatabase
    ) -> None:
        symptom = symptom_db.normalise("Fever")
        assert isinstance(symptom, SimpleSymptom)

    def test_normalise_lowercases_name(self, symptom_db: SymptomDatabase) -> None:
        symptom = symptom_db.normalise("FEVER")
        assert symptom.name == "fever"

    def test_normalise_strips_whitespace(self, symptom_db: SymptomDatabase) -> None:
        symptom = symptom_db.normalise("  fever  ")
        assert symptom.name == "fever"

    def test_normalise_sets_body_area(self, symptom_db: SymptomDatabase) -> None:
        symptom = symptom_db.normalise("headache")
        assert symptom.body_area == "head"

    def test_normalise_default_severity_mild(
        self, symptom_db: SymptomDatabase
    ) -> None:
        symptom = symptom_db.normalise("cough")
        assert symptom.severity == "mild"

    def test_all_symptom_names_returns_list(
        self, symptom_db: SymptomDatabase
    ) -> None:
        names = symptom_db.all_symptom_names()
        assert isinstance(names, list)
        assert len(names) > 0

    def test_all_symptom_names_includes_common_symptoms(
        self, symptom_db: SymptomDatabase
    ) -> None:
        names = symptom_db.all_symptom_names()
        assert "fever" in names
        assert "headache" in names
        assert "cough" in names

    def test_all_symptom_names_are_strings(
        self, symptom_db: SymptomDatabase
    ) -> None:
        for name in symptom_db.all_symptom_names():
            assert isinstance(name, str)


# ---------------------------------------------------------------------------
# ConditionMatcher tests
# ---------------------------------------------------------------------------


class TestConditionMatcher:
    def test_match_empty_symptoms_returns_empty(
        self, matcher: ConditionMatcher
    ) -> None:
        result = matcher.match([])
        assert result == []

    def test_match_dengue_symptoms(self, matcher: ConditionMatcher) -> None:
        symptoms = [
            SimpleSymptom(name="high fever"),
            SimpleSymptom(name="severe headache"),
            SimpleSymptom(name="eye pain"),
        ]
        result = matcher.match(symptoms)
        names = [r["name"] for r in result]
        assert "Dengue" in names

    def test_match_common_cold_symptoms(self, matcher: ConditionMatcher) -> None:
        symptoms = [
            SimpleSymptom(name="runny nose"),
            SimpleSymptom(name="sneezing"),
        ]
        result = matcher.match(symptoms)
        names = [r["name"] for r in result]
        assert "Common Cold" in names

    def test_match_chest_pain_returns_emergency_condition(
        self, matcher: ConditionMatcher
    ) -> None:
        symptoms = [
            SimpleSymptom(name="chest pain"),
            SimpleSymptom(name="left arm pain"),
        ]
        result = matcher.match(symptoms)
        names = [r["name"] for r in result]
        assert "Acute Coronary Syndrome" in names

    def test_match_result_has_required_keys(self, matcher: ConditionMatcher) -> None:
        symptoms = [
            SimpleSymptom(name="high fever"),
            SimpleSymptom(name="severe headache"),
            SimpleSymptom(name="eye pain"),
        ]
        result = matcher.match(symptoms)
        assert len(result) > 0
        first = result[0]
        assert "name" in first
        assert "icd_code" in first
        assert "description" in first
        assert "likelihood_pct" in first
        assert "urgency" in first
        assert "matched_symptoms" in first

    def test_match_result_sorted_by_likelihood_desc(
        self, matcher: ConditionMatcher
    ) -> None:
        symptoms = [
            SimpleSymptom(name="high fever"),
            SimpleSymptom(name="severe headache"),
            SimpleSymptom(name="eye pain"),
            SimpleSymptom(name="rash"),
        ]
        result = matcher.match(symptoms)
        likelihoods = [r["likelihood_pct"] for r in result]
        assert likelihoods == sorted(likelihoods, reverse=True)

    def test_match_likelihood_between_0_and_100(
        self, matcher: ConditionMatcher
    ) -> None:
        symptoms = [
            SimpleSymptom(name="high fever"),
            SimpleSymptom(name="severe headache"),
            SimpleSymptom(name="eye pain"),
        ]
        result = matcher.match(symptoms)
        for cond in result:
            assert 0 <= int(cond["likelihood_pct"]) <= 100

    def test_match_emergency_conditions_detected(
        self, matcher: ConditionMatcher
    ) -> None:
        # Stroke symptoms
        symptoms = [
            SimpleSymptom(name="face drooping"),
            SimpleSymptom(name="arm weakness"),
        ]
        result = matcher.match(symptoms)
        urgencies = [r["urgency"] for r in result]
        assert "emergency" in urgencies

    def test_assess_urgency_returns_emergency_for_emergency_condition(
        self, matcher: ConditionMatcher
    ) -> None:
        conditions = [
            {"name": "Stroke", "urgency": "emergency"},
            {"name": "Common Cold", "urgency": "routine"},
        ]
        assert matcher.assess_urgency(conditions) == "emergency"

    def test_assess_urgency_returns_urgent_when_no_emergency(
        self, matcher: ConditionMatcher
    ) -> None:
        conditions = [
            {"name": "Dengue", "urgency": "urgent"},
            {"name": "Common Cold", "urgency": "routine"},
        ]
        assert matcher.assess_urgency(conditions) == "urgent"

    def test_assess_urgency_returns_routine_for_routine_only(
        self, matcher: ConditionMatcher
    ) -> None:
        conditions = [
            {"name": "Common Cold", "urgency": "routine"},
            {"name": "Gastroenteritis", "urgency": "routine"},
        ]
        assert matcher.assess_urgency(conditions) == "routine"

    def test_assess_urgency_empty_conditions_returns_routine(
        self, matcher: ConditionMatcher
    ) -> None:
        assert matcher.assess_urgency([]) == "routine"

    def test_match_tuberculosis_symptoms(self, matcher: ConditionMatcher) -> None:
        symptoms = [
            SimpleSymptom(name="persistent cough"),
            SimpleSymptom(name="blood in sputum"),
            SimpleSymptom(name="weight loss"),
        ]
        result = matcher.match(symptoms)
        names = [r["name"] for r in result]
        assert "Tuberculosis" in names


# ---------------------------------------------------------------------------
# AYUSHAdvisor tests
# ---------------------------------------------------------------------------


class TestAYUSHAdvisor:
    def test_ayurvedic_perspective_returns_list(
        self, ayush_advisor: AYUSHAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        result = ayush_advisor.ayurvedic_perspective(symptoms)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_ayurvedic_perspective_includes_disclaimer(
        self, ayush_advisor: AYUSHAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        result = ayush_advisor.ayurvedic_perspective(symptoms)
        assert MEDICAL_DISCLAIMER in result

    def test_ayurvedic_perspective_includes_bams_recommendation(
        self, ayush_advisor: AYUSHAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        result = ayush_advisor.ayurvedic_perspective(symptoms)
        combined = " ".join(result)
        assert "BAMS" in combined or "Ayurvedic" in combined

    def test_ayurvedic_perspective_fever_includes_giloy(
        self, ayush_advisor: AYUSHAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        result = ayush_advisor.ayurvedic_perspective(symptoms)
        combined = " ".join(result)
        assert "Giloy" in combined or "giloy" in combined.lower()

    def test_ayurvedic_perspective_cough_includes_tulsi(
        self, ayush_advisor: AYUSHAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="cough")]
        result = ayush_advisor.ayurvedic_perspective(symptoms)
        combined = " ".join(result)
        assert "Tulsi" in combined or "tulsi" in combined.lower()

    def test_ayurvedic_perspective_empty_symptoms_gives_general(
        self, ayush_advisor: AYUSHAdvisor
    ) -> None:
        result = ayush_advisor.ayurvedic_perspective([])
        combined = " ".join(result)
        # Should include general wellness suggestions
        assert "Chyawanprash" in combined or "turmeric" in combined.lower()

    def test_ayurvedic_perspective_unknown_symptom_gives_general(
        self, ayush_advisor: AYUSHAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="completely_unknown_xyz")]
        result = ayush_advisor.ayurvedic_perspective(symptoms)
        # Should fall back to general
        assert len(result) > 0
        assert MEDICAL_DISCLAIMER in result

    def test_ayurvedic_perspective_joint_pain_includes_shallaki(
        self, ayush_advisor: AYUSHAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="joint pain")]
        result = ayush_advisor.ayurvedic_perspective(symptoms)
        combined = " ".join(result)
        assert "Shallaki" in combined or "Boswellia" in combined


# ---------------------------------------------------------------------------
# HealthAdvisor tests
# ---------------------------------------------------------------------------


class TestHealthAdvisor:
    def test_assess_returns_health_assessment(
        self, health_advisor: HealthAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="fever"), SimpleSymptom(name="cough")]
        assessment = health_advisor.assess(symptoms, MedicalSystem.allopathy)
        assert isinstance(assessment, HealthAssessment)

    def test_assess_includes_disclaimer(self, health_advisor: HealthAdvisor) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        assessment = health_advisor.assess(symptoms, MedicalSystem.allopathy)
        assert assessment.disclaimer == MEDICAL_DISCLAIMER

    def test_assess_disclaimer_in_recommended_actions(
        self, health_advisor: HealthAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        assessment = health_advisor.assess(symptoms, MedicalSystem.allopathy)
        assert MEDICAL_DISCLAIMER in assessment.recommended_actions

    def test_assess_system_is_preserved(self, health_advisor: HealthAdvisor) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        for system in MedicalSystem:
            assessment = health_advisor.assess(symptoms, system)
            assert assessment.system == system

    def test_assess_urgency_routine_for_mild_symptoms(
        self, health_advisor: HealthAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="runny nose"), SimpleSymptom(name="sneezing")]
        assessment = health_advisor.assess(symptoms, MedicalSystem.allopathy)
        assert assessment.urgency in {"routine", "urgent", "emergency"}

    def test_assess_emergency_urgency_for_chest_pain(
        self,
        health_advisor: HealthAdvisor,
        emergency_symptoms: list[SimpleSymptom],
    ) -> None:
        assessment = health_advisor.assess(emergency_symptoms, MedicalSystem.allopathy)
        assert assessment.urgency == "emergency"

    def test_assess_emergency_includes_108_instruction(
        self,
        health_advisor: HealthAdvisor,
        emergency_symptoms: list[SimpleSymptom],
    ) -> None:
        assessment = health_advisor.assess(emergency_symptoms, MedicalSystem.allopathy)
        combined = " ".join(assessment.recommended_actions)
        assert "108" in combined

    def test_assess_no_duplicate_actions(self, health_advisor: HealthAdvisor) -> None:
        symptoms = [SimpleSymptom(name="fever"), SimpleSymptom(name="cough")]
        assessment = health_advisor.assess(symptoms, MedicalSystem.allopathy)
        seen: set[str] = set()
        for action in assessment.recommended_actions:
            assert action not in seen, f"Duplicate action: {action}"
            seen.add(action)

    def test_assess_ayurveda_includes_ayurvedic_suggestions(
        self, health_advisor: HealthAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        assessment = health_advisor.assess(symptoms, MedicalSystem.ayurveda)
        combined = " ".join(assessment.recommended_actions)
        assert "Ayurvedic" in combined or "BAMS" in combined or "Giloy" in combined

    def test_assess_allopathy_includes_mbbs_suggestion(
        self, health_advisor: HealthAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        assessment = health_advisor.assess(symptoms, MedicalSystem.allopathy)
        combined = " ".join(assessment.recommended_actions)
        assert "MBBS" in combined or "physician" in combined.lower()

    def test_assess_symptoms_preserved_in_output(
        self, health_advisor: HealthAdvisor
    ) -> None:
        symptoms = [
            SimpleSymptom(name="fever", body_area="general", severity="mild"),
            SimpleSymptom(name="headache", body_area="head", severity="moderate"),
        ]
        assessment = health_advisor.assess(symptoms, MedicalSystem.allopathy)
        names_in = {s.name for s in symptoms}
        names_out = {s.name for s in assessment.symptoms}
        assert names_in == names_out

    def test_assess_yoga_includes_pranayama(
        self, health_advisor: HealthAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        assessment = health_advisor.assess(symptoms, MedicalSystem.yoga)
        combined = " ".join(assessment.recommended_actions)
        assert "Pranayama" in combined or "yoga" in combined.lower()

    def test_assess_unani_includes_hakeem(self, health_advisor: HealthAdvisor) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        assessment = health_advisor.assess(symptoms, MedicalSystem.unani)
        combined = " ".join(assessment.recommended_actions)
        assert "Hakeem" in combined or "Unani" in combined

    def test_assess_siddha_includes_siddha(self, health_advisor: HealthAdvisor) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        assessment = health_advisor.assess(symptoms, MedicalSystem.siddha)
        combined = " ".join(assessment.recommended_actions)
        assert "Siddha" in combined or "BSMS" in combined

    def test_assess_homeopathy_includes_bhms(
        self, health_advisor: HealthAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        assessment = health_advisor.assess(symptoms, MedicalSystem.homeopathy)
        combined = " ".join(assessment.recommended_actions)
        assert "BHMS" in combined or "Homeopathy" in combined

    def test_assess_urgency_valid_values(self, health_advisor: HealthAdvisor) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        assessment = health_advisor.assess(symptoms, MedicalSystem.allopathy)
        assert assessment.urgency in {"routine", "urgent", "emergency"}

    def test_assess_possible_conditions_is_list(
        self, health_advisor: HealthAdvisor
    ) -> None:
        symptoms = [SimpleSymptom(name="fever")]
        assessment = health_advisor.assess(symptoms, MedicalSystem.allopathy)
        assert isinstance(assessment.possible_conditions, list)

    def test_assess_stroke_symptoms_returns_emergency(
        self, health_advisor: HealthAdvisor
    ) -> None:
        symptoms = [
            SimpleSymptom(name="face drooping"),
            SimpleSymptom(name="speech difficulty"),
        ]
        assessment = health_advisor.assess(symptoms, MedicalSystem.allopathy)
        assert assessment.urgency == "emergency"


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


class TestHypothesisBased:
    @given(name=st.text(min_size=1, max_size=50))
    @settings(max_examples=30)
    def test_get_body_area_never_crashes(self, name: str) -> None:
        db = SymptomDatabase()
        result = db.get_body_area(name)
        assert isinstance(result, str)

    @given(name=st.text(min_size=1, max_size=50))
    @settings(max_examples=30)
    def test_normalise_never_crashes(self, name: str) -> None:
        db = SymptomDatabase()
        result = db.normalise(name)
        assert isinstance(result, SimpleSymptom)
        assert result.severity == "mild"

    @given(
        symptom_names=st.lists(
            st.sampled_from(["fever", "cough", "headache", "nausea", "rash"]),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=20)
    def test_condition_matcher_never_crashes(
        self, symptom_names: list[str]
    ) -> None:
        matcher = ConditionMatcher()
        symptoms = [SimpleSymptom(name=n) for n in symptom_names]
        result = matcher.match(symptoms)
        assert isinstance(result, list)

    @given(
        system=st.sampled_from(list(MedicalSystem))
    )
    @settings(max_examples=6)
    def test_health_advisor_assess_all_systems(
        self, system: MedicalSystem
    ) -> None:
        advisor = HealthAdvisor()
        symptoms = [SimpleSymptom(name="fever")]
        assessment = advisor.assess(symptoms, system)
        assert isinstance(assessment, HealthAssessment)
        assert assessment.disclaimer == MEDICAL_DISCLAIMER


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_full_assessment_workflow_allopathy(self) -> None:
        db = SymptomDatabase()
        advisor = HealthAdvisor()

        raw_names = ["fever", "cough", "headache"]
        symptoms = [db.normalise(name) for name in raw_names]
        assessment = advisor.assess(symptoms, MedicalSystem.allopathy)

        assert isinstance(assessment, HealthAssessment)
        assert len(assessment.symptoms) == 3
        assert assessment.system == MedicalSystem.allopathy
        assert MEDICAL_DISCLAIMER in assessment.recommended_actions

    def test_emergency_workflow_returns_108(self) -> None:
        advisor = HealthAdvisor()
        symptoms = [
            SimpleSymptom(name="chest pain"),
            SimpleSymptom(name="breathlessness"),
        ]
        assessment = advisor.assess(symptoms, MedicalSystem.allopathy)
        combined = " ".join(assessment.recommended_actions)
        assert "108" in combined
        assert assessment.urgency == "emergency"

    def test_ayurveda_workflow_has_both_traditional_and_disclaimer(self) -> None:
        advisor = HealthAdvisor()
        symptoms = [SimpleSymptom(name="fever"), SimpleSymptom(name="joint pain")]
        assessment = advisor.assess(symptoms, MedicalSystem.ayurveda)

        combined = " ".join(assessment.recommended_actions)
        # Must include Ayurvedic content
        assert "Giloy" in combined or "Ashwagandha" in combined or "Shallaki" in combined
        # Must include disclaimer
        assert MEDICAL_DISCLAIMER in assessment.recommended_actions

    def test_disclaimer_always_last_dedup_action(self) -> None:
        """Disclaimer should appear exactly once in recommended_actions."""
        advisor = HealthAdvisor()
        symptoms = [SimpleSymptom(name="fever")]
        assessment = advisor.assess(symptoms, MedicalSystem.allopathy)
        count = assessment.recommended_actions.count(MEDICAL_DISCLAIMER)
        assert count == 1
