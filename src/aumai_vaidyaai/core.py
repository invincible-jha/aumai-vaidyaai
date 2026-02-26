"""Core logic for aumai-vaidyaai: symptom checker with AYUSH and allopathy perspectives."""

from __future__ import annotations

from .models import (
    MEDICAL_DISCLAIMER,
    HealthAssessment,
    MedicalSystem,
    SimpleSymptom,
)

__all__ = ["SymptomDatabase", "ConditionMatcher", "AYUSHAdvisor", "HealthAdvisor"]

# ---------------------------------------------------------------------------
# Symptom-to-condition mapping (rule-based)
# ---------------------------------------------------------------------------

_CONDITIONS: list[dict[str, object]] = [
    {
        "name": "Common Cold",
        "matching_symptoms": ["runny nose", "sneezing", "sore throat", "mild fever", "cough"],
        "min_match": 2,
        "description": "Viral upper respiratory tract infection, usually self-limiting in 7-10 days.",
        "urgency": "routine",
        "icd_code": "J06.9",
    },
    {
        "name": "Influenza",
        "matching_symptoms": ["fever", "body ache", "fatigue", "headache", "cough", "chills"],
        "min_match": 3,
        "description": "Seasonal flu caused by influenza virus; more severe than common cold.",
        "urgency": "routine",
        "icd_code": "J11",
    },
    {
        "name": "Dengue",
        "matching_symptoms": ["high fever", "severe headache", "eye pain", "joint pain", "rash", "bleeding"],
        "min_match": 3,
        "description": "Mosquito-borne viral infection. Platelet count monitoring is critical.",
        "urgency": "urgent",
        "icd_code": "A90",
    },
    {
        "name": "Malaria",
        "matching_symptoms": ["cyclical fever", "chills", "sweating", "headache", "nausea", "vomiting"],
        "min_match": 3,
        "description": "Parasitic infection transmitted by Anopheles mosquito. Requires blood test confirmation.",
        "urgency": "urgent",
        "icd_code": "B50",
    },
    {
        "name": "Typhoid Fever",
        "matching_symptoms": ["sustained fever", "abdominal pain", "headache", "constipation", "weakness", "rose spots"],
        "min_match": 3,
        "description": "Bacterial enteric fever caused by Salmonella typhi. Widal test recommended.",
        "urgency": "urgent",
        "icd_code": "A01.0",
    },
    {
        "name": "Gastroenteritis",
        "matching_symptoms": ["diarrhoea", "vomiting", "nausea", "abdominal cramps", "stomach pain"],
        "min_match": 2,
        "description": "Inflammation of stomach and intestines. Oral rehydration is the priority.",
        "urgency": "routine",
        "icd_code": "A09",
    },
    {
        "name": "Acute Coronary Syndrome",
        "matching_symptoms": ["chest pain", "left arm pain", "jaw pain", "breathlessness", "sweating", "nausea"],
        "min_match": 2,
        "description": "EMERGENCY: Possible heart attack. Call 108 immediately.",
        "urgency": "emergency",
        "icd_code": "I24",
    },
    {
        "name": "Hypertensive Crisis",
        "matching_symptoms": ["severe headache", "blurred vision", "chest pain", "nose bleed", "shortness of breath"],
        "min_match": 2,
        "description": "EMERGENCY: Severely elevated blood pressure. Seek immediate care.",
        "urgency": "emergency",
        "icd_code": "I10",
    },
    {
        "name": "Stroke",
        "matching_symptoms": ["face drooping", "arm weakness", "speech difficulty", "sudden headache", "confusion"],
        "min_match": 2,
        "description": "EMERGENCY: Brain attack. Act FAST — Face, Arms, Speech, Time.",
        "urgency": "emergency",
        "icd_code": "I63",
    },
    {
        "name": "Pneumonia",
        "matching_symptoms": ["fever", "cough with sputum", "breathlessness", "chest pain", "fatigue"],
        "min_match": 3,
        "description": "Lung infection requiring medical evaluation and possibly antibiotics.",
        "urgency": "urgent",
        "icd_code": "J18",
    },
    {
        "name": "Urinary Tract Infection",
        "matching_symptoms": ["burning urination", "frequent urination", "lower abdominal pain", "cloudy urine", "fever"],
        "min_match": 2,
        "description": "Bacterial infection of the urinary tract. Urine culture recommended.",
        "urgency": "routine",
        "icd_code": "N39.0",
    },
    {
        "name": "Migraine",
        "matching_symptoms": ["severe headache", "nausea", "light sensitivity", "sound sensitivity", "visual aura"],
        "min_match": 2,
        "description": "Neurological condition causing intense headaches, often one-sided.",
        "urgency": "routine",
        "icd_code": "G43",
    },
    {
        "name": "Anaemia",
        "matching_symptoms": ["fatigue", "weakness", "pale skin", "shortness of breath", "dizziness", "cold hands"],
        "min_match": 3,
        "description": "Low haemoglobin. Common in India due to iron or B12 deficiency. CBC recommended.",
        "urgency": "routine",
        "icd_code": "D64.9",
    },
    {
        "name": "Diabetes (Uncontrolled)",
        "matching_symptoms": ["excessive thirst", "frequent urination", "weight loss", "blurred vision", "fatigue", "slow healing"],
        "min_match": 3,
        "description": "Possible uncontrolled blood glucose. Fasting blood sugar test recommended.",
        "urgency": "urgent",
        "icd_code": "E11",
    },
    {
        "name": "Appendicitis",
        "matching_symptoms": ["right lower abdominal pain", "nausea", "vomiting", "fever", "loss of appetite"],
        "min_match": 3,
        "description": "URGENT: Possible appendix inflammation. Seek surgical evaluation immediately.",
        "urgency": "emergency",
        "icd_code": "K35",
    },
    {
        "name": "Allergic Reaction",
        "matching_symptoms": ["hives", "itching", "swelling", "sneezing", "runny nose", "watery eyes"],
        "min_match": 2,
        "description": "Allergic response. If throat swelling or difficulty breathing, seek emergency care.",
        "urgency": "routine",
        "icd_code": "T78.4",
    },
    {
        "name": "Anaphylaxis",
        "matching_symptoms": ["throat swelling", "difficulty breathing", "hives", "rapid heartbeat", "dizziness", "collapse"],
        "min_match": 2,
        "description": "EMERGENCY: Severe allergic reaction. Administer epinephrine and call 108.",
        "urgency": "emergency",
        "icd_code": "T78.2",
    },
    {
        "name": "Tuberculosis",
        "matching_symptoms": ["persistent cough", "blood in sputum", "weight loss", "night sweats", "fever", "fatigue"],
        "min_match": 3,
        "description": "Bacterial lung infection. Sputum test and chest X-ray required. Report to RNTCP.",
        "urgency": "urgent",
        "icd_code": "A15",
    },
    {
        "name": "Jaundice",
        "matching_symptoms": ["yellow skin", "yellow eyes", "dark urine", "pale stools", "fatigue", "abdominal pain"],
        "min_match": 2,
        "description": "Elevated bilirubin. Liver function tests needed to determine cause.",
        "urgency": "urgent",
        "icd_code": "R17",
    },
    {
        "name": "Dehydration",
        "matching_symptoms": ["excessive thirst", "dry mouth", "dark urine", "dizziness", "fatigue", "reduced urination"],
        "min_match": 3,
        "description": "Fluid deficit. Oral rehydration solution (ORS) is first-line treatment.",
        "urgency": "routine",
        "icd_code": "E86",
    },
]

_SYMPTOM_BODY_AREAS: dict[str, str] = {
    "headache": "head", "severe headache": "head", "dizziness": "head",
    "confusion": "head", "facial drooping": "head", "visual aura": "head",
    "blurred vision": "head", "eye pain": "head", "watery eyes": "head",
    "runny nose": "head", "sneezing": "head", "nasal congestion": "head",
    "sore throat": "head", "jaw pain": "head", "nose bleed": "head",
    "ear pain": "head", "yellow eyes": "head", "speech difficulty": "head",
    "fever": "general", "high fever": "general", "mild fever": "general",
    "sustained fever": "general", "cyclical fever": "general", "chills": "general",
    "sweating": "general", "night sweats": "general", "fatigue": "general",
    "weakness": "general", "weight loss": "general", "body ache": "general",
    "loss of appetite": "general",
    "cough": "chest", "cough with sputum": "chest", "blood in sputum": "chest",
    "persistent cough": "chest", "chest pain": "chest",
    "shortness of breath": "chest", "breathlessness": "chest",
    "difficulty breathing": "chest", "wheezing": "chest",
    "rapid heartbeat": "chest", "left arm pain": "chest",
    "nausea": "abdomen", "vomiting": "abdomen", "diarrhoea": "abdomen",
    "constipation": "abdomen", "abdominal pain": "abdomen",
    "abdominal cramps": "abdomen", "stomach pain": "abdomen",
    "right lower abdominal pain": "abdomen", "lower abdominal pain": "abdomen",
    "pale stools": "abdomen", "bloating": "abdomen",
    "burning urination": "urinary", "frequent urination": "urinary",
    "cloudy urine": "urinary", "dark urine": "urinary",
    "excessive thirst": "urinary", "reduced urination": "urinary",
    "rash": "skin", "hives": "skin", "itching": "skin", "swelling": "skin",
    "yellow skin": "skin", "pale skin": "skin", "rose spots": "skin",
    "slow healing": "skin", "cold hands": "general", "dry mouth": "general",
    "joint pain": "musculoskeletal", "muscle pain": "musculoskeletal",
    "arm weakness": "musculoskeletal", "back pain": "musculoskeletal",
    "neck stiffness": "musculoskeletal",
    "collapse": "general", "bleeding": "general",
    "light sensitivity": "head", "sound sensitivity": "head",
    "throat swelling": "head", "face drooping": "head",
}


class SymptomDatabase:
    """Database of 100+ common symptoms with body area mappings."""

    def get_body_area(self, symptom_name: str) -> str:
        """Return the body area for a given symptom name."""
        return _SYMPTOM_BODY_AREAS.get(symptom_name.lower(), "general")

    def normalise(self, symptom_name: str) -> SimpleSymptom:
        """Create a SimpleSymptom object from a plain symptom name string."""
        return SimpleSymptom(
            name=symptom_name.strip().lower(),
            body_area=self.get_body_area(symptom_name),
            severity="mild",
        )

    def all_symptom_names(self) -> list[str]:
        """Return all known symptom names."""
        return list(_SYMPTOM_BODY_AREAS.keys())


class ConditionMatcher:
    """Rule-based symptom-to-condition matcher."""

    def match(self, symptoms: list[SimpleSymptom]) -> list[dict[str, object]]:
        """Return conditions matching the provided symptoms, ranked by overlap score."""
        symptom_names = {s.name.lower() for s in symptoms}
        scored: list[tuple[float, dict[str, object]]] = []

        for condition in _CONDITIONS:
            matching_syms = condition["matching_symptoms"]
            min_match = int(condition["min_match"])  # type: ignore[arg-type]

            if not isinstance(matching_syms, list):
                continue

            overlap = sum(1 for ms in matching_syms if ms in symptom_names)
            if overlap >= min_match:
                likelihood = min(round(overlap / len(matching_syms) * 100), 95)
                result: dict[str, object] = {
                    "name": condition["name"],
                    "icd_code": condition["icd_code"],
                    "description": condition["description"],
                    "likelihood_pct": likelihood,
                    "urgency": condition["urgency"],
                    "matched_symptoms": [ms for ms in matching_syms if ms in symptom_names],
                }
                scored.append((float(likelihood), result))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored]

    def assess_urgency(self, conditions: list[dict[str, object]]) -> str:
        """Determine the highest urgency level across matched conditions."""
        for condition in conditions:
            if condition.get("urgency") == "emergency":
                return "emergency"
        for condition in conditions:
            if condition.get("urgency") == "urgent":
                return "urgent"
        return "routine"


_AYURVEDIC_MAPPINGS: dict[str, list[str]] = {
    "fever": [
        "Giloy (Tinospora cordifolia) kadha is traditionally used for immune support.",
        "Stay hydrated with warm water and ginger tea.",
        "Light diet (khichdi) to support digestion during illness.",
    ],
    "cough": [
        "Tulsi (Holy Basil) honey ginger tea is a traditional respiratory support.",
        "Steam inhalation with eucalyptus or camphor.",
        "Avoid cold foods and beverages.",
    ],
    "headache": [
        "Brahmi (Bacopa monnieri) is traditionally associated with cognitive and stress support.",
        "Warm oil self-massage (abhyanga) may provide relaxation.",
    ],
    "joint pain": [
        "Shallaki (Boswellia serrata) and Ashwagandha are traditionally used for joint health.",
        "Anti-inflammatory diet: turmeric (curcumin) in warm milk.",
    ],
    "digestive": [
        "Triphala churna (one teaspoon with warm water before bed) supports digestive health.",
        "Ajwain (carom seeds) with warm water for bloating.",
    ],
    "stress": [
        "Ashwagandha (Withania somnifera) is an adaptogenic herb used in Ayurveda.",
        "Pranayama (Anulom Vilom, Bhramari) for stress management.",
    ],
    "general": [
        "Chyawanprash is a traditional Ayurvedic rasayana for general wellness.",
        "Warm turmeric milk (haldi doodh) as a traditional immunity tonic.",
        "Regular daily routine (dinacharya) for overall wellbeing.",
    ],
}


class AYUSHAdvisor:
    """Provides traditional Ayurvedic general wellness perspectives. NOT medical advice."""

    def ayurvedic_perspective(self, symptoms: list[SimpleSymptom]) -> list[str]:
        """Return Ayurvedic general wellness suggestions for the symptom set."""
        suggestions: list[str] = []
        matched_keys: set[str] = set()

        for symptom in symptoms:
            name_lower = symptom.name.lower()
            for key in _AYURVEDIC_MAPPINGS:
                if key in name_lower or name_lower in key:
                    if key not in matched_keys:
                        suggestions.extend(_AYURVEDIC_MAPPINGS[key])
                        matched_keys.add(key)

        if not suggestions:
            suggestions.extend(_AYURVEDIC_MAPPINGS["general"])

        suggestions.append(
            "Consult a registered Ayurvedic physician (BAMS) for personalised treatment."
        )
        suggestions.append(MEDICAL_DISCLAIMER)
        return suggestions


_SYSTEM_ACTIONS: dict[MedicalSystem, list[str]] = {
    MedicalSystem.allopathy: [
        "Consult a qualified MBBS/MD physician for diagnosis and treatment.",
        "A complete blood count (CBC) and relevant investigations are advised.",
        "Take prescribed medications as directed. Do not self-medicate.",
    ],
    MedicalSystem.ayurveda: [
        "Consult a registered BAMS (Ayurvedic) physician.",
        "Panchakarma evaluation may be recommended for chronic conditions.",
        "Dietary and lifestyle adjustments per Prakriti (constitution) analysis.",
    ],
    MedicalSystem.yoga: [
        "Consult a certified yoga therapist for a personalised yoga prescription.",
        "Pranayama and asana practice may complement conventional treatment.",
        "Yoga is adjunct therapy — do not substitute it for medical care.",
    ],
    MedicalSystem.unani: [
        "Consult a registered BUMS (Unani) physician.",
        "Unani Ilaj-bil-dawa (pharmacotherapy) uses herbo-mineral formulations.",
        "Seek care from a qualified Hakeem for personalised treatment.",
    ],
    MedicalSystem.siddha: [
        "Consult a registered BSMS (Siddha) physician.",
        "Siddha medicine uses plant, animal, and mineral preparations.",
        "Do not self-administer heavy-metal based Siddha formulations without supervision.",
    ],
    MedicalSystem.homeopathy: [
        "Consult a registered BHMS (Homeopathy) physician.",
        "Homeopathic treatment is individualised based on totality of symptoms.",
        "For emergencies, seek conventional medical care first.",
    ],
}

_EMERGENCY_ACTIONS = [
    "CALL 108 (Ambulance) IMMEDIATELY.",
    "Do not drive yourself to hospital if experiencing chest pain or breathing difficulty.",
    "If unconscious or not breathing, start CPR if trained.",
    "Inform nearby people of the emergency.",
]


class HealthAdvisor:
    """Orchestrates symptom assessment across multiple medical systems."""

    def __init__(self) -> None:
        self._matcher = ConditionMatcher()
        self._ayush = AYUSHAdvisor()

    def assess(
        self, symptoms: list[SimpleSymptom], system: MedicalSystem
    ) -> HealthAssessment:
        """Generate a HealthAssessment for the given symptoms and medical system."""
        matched_conditions = self._matcher.match(symptoms)
        urgency = self._matcher.assess_urgency(matched_conditions)

        if urgency == "emergency":
            recommended_actions = list(_EMERGENCY_ACTIONS) + list(
                _SYSTEM_ACTIONS.get(system, [])
            )
        else:
            recommended_actions = list(_SYSTEM_ACTIONS.get(system, []))
            if system == MedicalSystem.ayurveda:
                ayurvedic = self._ayush.ayurvedic_perspective(symptoms)
                # Strip the trailing disclaimer lines added inside ayurvedic_perspective
                ayurvedic_body = [a for a in ayurvedic if a != MEDICAL_DISCLAIMER]
                recommended_actions = ayurvedic_body + recommended_actions

        recommended_actions.append(MEDICAL_DISCLAIMER)
        # Deduplicate while preserving order
        seen: set[str] = set()
        deduped: list[str] = []
        for action in recommended_actions:
            if action not in seen:
                seen.add(action)
                deduped.append(action)

        return HealthAssessment(
            symptoms=symptoms,
            possible_conditions=matched_conditions,
            recommended_actions=deduped,
            urgency=urgency,
            system=system,
            disclaimer=MEDICAL_DISCLAIMER,
        )
