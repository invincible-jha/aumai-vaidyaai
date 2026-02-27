"""Pydantic v2 models for aumai-vaidyaai AYUSH + allopathy symptom checker."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

MEDICAL_DISCLAIMER = (
    "IMPORTANT MEDICAL DISCLAIMER: This tool does NOT provide medical advice, diagnosis, or treatment."
    " Symptom analysis is based on keyword matching only and may be inaccurate."
    " Always consult a qualified healthcare professional for medical concerns."
    " In emergencies, contact your nearest hospital immediately."
)

__all__ = [
    "SymptomCategory",
    "Symptom",
    "MedicalSystem",
    "Recommendation",
    "SymptomAssessment",
    "Condition",
    "HealthAssessment",
    "SimpleSymptom",
    "MEDICAL_DISCLAIMER",
]


class SymptomCategory(str, Enum):
    """Category of symptom by body system."""

    general = "general"
    respiratory = "respiratory"
    digestive = "digestive"
    musculoskeletal = "musculoskeletal"
    skin = "skin"
    neurological = "neurological"


class MedicalSystem(str, Enum):
    """Supported medical systems under AYUSH and allopathy."""

    allopathy = "allopathy"
    ayurveda = "ayurveda"
    yoga = "yoga"
    unani = "unani"
    siddha = "siddha"
    homeopathy = "homeopathy"


class Symptom(BaseModel):
    """A symptom in the knowledge base."""

    code: str = Field(..., description="Unique symptom code")
    name: str = Field(..., description="Human-readable symptom name")
    category: SymptomCategory = Field(..., description="Body system category")
    severity_range: tuple[int, int] = Field(
        default=(1, 10), description="Min and max severity scores (1-10)"
    )


class Recommendation(BaseModel):
    """A treatment recommendation from a specific medical system."""

    system: MedicalSystem = Field(..., description="Medical system providing the recommendation")
    condition: str = Field(..., description="Condition being addressed")
    description: str = Field(..., description="Detailed recommendation text")
    urgency: str = Field(
        ...,
        description="Urgency: self_care / see_doctor / urgent / emergency",
        pattern="^(self_care|see_doctor|urgent|emergency)$",
    )
    seek_professional: bool = Field(
        ..., description="Whether professional consultation is recommended"
    )


class SymptomAssessment(BaseModel):
    """Full assessment result returned to the user."""

    symptoms: list[str] = Field(..., description="Reported symptom codes")
    matched_conditions: list[dict[str, object]] = Field(
        default_factory=list,
        description="Conditions matched with scores",
    )
    recommendations: list[Recommendation] = Field(
        default_factory=list, description="Recommendations per medical system"
    )
    triage_level: str = Field(
        ...,
        description="Triage level: green / amber / red",
        pattern="^(green|amber|red)$",
    )
    disclaimer: str = Field(
        default=MEDICAL_DISCLAIMER,
        description="Mandatory medical disclaimer",
    )


class Condition(BaseModel):
    """A medical condition in the knowledge base."""

    code: str = Field(..., description="Unique condition code")
    name: str = Field(..., description="Condition name")
    symptoms_required: list[str] = Field(
        ..., description="Symptom codes that must be present (required)"
    )
    symptoms_optional: list[str] = Field(
        default_factory=list,
        description="Symptom codes that may be present (optional)",
    )
    systems: list[MedicalSystem] = Field(
        ..., description="Medical systems with known management for this condition"
    )


class SimpleSymptom(BaseModel):
    """Lightweight symptom model used for CLI and API input (name + severity)."""

    name: str = Field(..., description="Name of the symptom (e.g. fever, headache)")
    body_area: str = Field(
        default="general", description="Body area affected (e.g. head, chest, abdomen)"
    )
    severity: str = Field(
        default="mild",
        description="Severity: mild, moderate, or severe",
        pattern="^(mild|moderate|severe)$",
    )


class HealthAssessment(BaseModel):
    """Result of a symptom-based health assessment (spec-required output model)."""

    symptoms: list[SimpleSymptom]
    possible_conditions: list[dict[str, object]] = Field(
        ..., description="Possible conditions with name, likelihood, and description"
    )
    recommended_actions: list[str] = Field(
        ..., description="Recommended next actions"
    )
    urgency: str = Field(
        ...,
        description="Urgency level: routine, urgent, or emergency",
        pattern="^(routine|urgent|emergency)$",
    )
    system: MedicalSystem = Field(
        ..., description="Medical system perspective used for recommendations"
    )
    disclaimer: str = Field(
        default=MEDICAL_DISCLAIMER,
        description="Mandatory medical disclaimer",
    )
