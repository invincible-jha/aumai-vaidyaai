# Getting Started with aumai-vaidyaai

AYUSH and allopathy symptom checker for rural health workers in India.

> **Medical Disclaimer:** This tool does NOT provide medical advice, diagnosis, or
> treatment. Always consult a qualified healthcare professional. In emergencies,
> call 108 immediately.

---

## Prerequisites

- Python 3.11 or newer
- pip or uv package manager
- No external APIs, no model weights, no cloud credentials required
- Works fully offline — suitable for low-connectivity rural deployments
- Optional: `uvicorn` if you want to run the API server (not yet implemented in v0.1.0)

---

## Installation

### From PyPI

```bash
pip install aumai-vaidyaai
```

### From source

```bash
git clone https://github.com/aumai/aumai-vaidyaai.git
cd aumai-vaidyaai
pip install -e ".[dev]"
```

### Verify

```bash
vaidyaai --version
# aumai-vaidyaai, version 0.1.0

python -c "import aumai_vaidyaai; print(aumai_vaidyaai.__version__)"
# 0.1.0
```

---

## Step-by-Step Tutorial

### Step 1 — Understand what symptoms the system knows

Before assessing a patient, it helps to know what symptoms are in the database.

```bash
vaidyaai symptoms
```

This prints all 100+ recognised symptoms with their index numbers. You can then
use exact symptom names (case is handled automatically) in your assessments.

Programmatically:

```python
from aumai_vaidyaai.core import SymptomDatabase

db = SymptomDatabase()
all_symptoms = db.all_symptom_names()
print(f"Total known symptoms: {len(all_symptoms)}")
print(sorted(all_symptoms)[:10])
# ['abdominal cramps', 'abdominal pain', 'arm weakness', 'back pain', ...]
```

### Step 2 — Normalise your first symptom

The `SymptomDatabase.normalise` method converts a plain text symptom name into
a `SimpleSymptom` object with a `body_area` classification and default severity.

```python
from aumai_vaidyaai.core import SymptomDatabase

db = SymptomDatabase()

symptom = db.normalise("fever")
print(symptom.name)        # "fever"
print(symptom.body_area)   # "general"
print(symptom.severity)    # "mild"

symptom = db.normalise("chest pain")
print(symptom.body_area)   # "chest"

symptom = db.normalise("right lower abdominal pain")
print(symptom.body_area)   # "abdomen"
```

### Step 3 — Run your first assessment

```python
from aumai_vaidyaai.core import HealthAdvisor, SymptomDatabase
from aumai_vaidyaai.models import MedicalSystem

db = SymptomDatabase()
advisor = HealthAdvisor()

# Common cold symptom pattern
symptoms = [
    db.normalise("runny nose"),
    db.normalise("sneezing"),
    db.normalise("sore throat"),
    db.normalise("mild fever"),
]

assessment = advisor.assess(symptoms, MedicalSystem.allopathy)

print(f"Urgency: {assessment.urgency}")       # routine
print(f"Disclaimer: {assessment.disclaimer}")

for condition in assessment.possible_conditions:
    print(f"  - {condition['name']}: {condition['likelihood_pct']}%")

for action in assessment.recommended_actions:
    print(f"  * {action}")
```

Or from the CLI using the same symptoms:

```bash
vaidyaai assess \
  --symptoms "runny nose,sneezing,sore throat,mild fever" \
  --system allopathy
```

### Step 4 — Try a different medical system

The same symptoms yield different recommended actions depending on the selected
`MedicalSystem`. The condition matching is system-agnostic — only the action
recommendations change.

```python
from aumai_vaidyaai.core import HealthAdvisor, SymptomDatabase
from aumai_vaidyaai.models import MedicalSystem

db = SymptomDatabase()
advisor = HealthAdvisor()
symptoms = [db.normalise(s) for s in ["fever", "cough", "headache", "body ache"]]

# Compare perspectives
for system in [MedicalSystem.allopathy, MedicalSystem.ayurveda, MedicalSystem.homeopathy]:
    assessment = advisor.assess(symptoms, system)
    print(f"\n=== {system.value.upper()} ===")
    for action in assessment.recommended_actions[:3]:
        print(f"  {action}")
```

From the CLI:

```bash
vaidyaai assess --symptoms "fever,cough,headache,body ache" --system ayurveda
vaidyaai assess --symptoms "fever,cough,headache,body ache" --system unani
vaidyaai assess --symptoms "fever,cough,headache,body ache" --system siddha
```

### Step 5 — Handle emergency symptoms

When any matched condition has `urgency="emergency"`, the assessment always
includes "Call 108 immediately" as the first recommended action, regardless
of which medical system is selected.

```python
from aumai_vaidyaai.core import HealthAdvisor, SymptomDatabase
from aumai_vaidyaai.models import MedicalSystem

db = SymptomDatabase()
advisor = HealthAdvisor()

# FAST stroke assessment
symptoms = [
    db.normalise("face drooping"),
    db.normalise("arm weakness"),
    db.normalise("speech difficulty"),
    db.normalise("sudden headache"),
]

assessment = advisor.assess(symptoms, MedicalSystem.allopathy)

print(f"URGENCY: {assessment.urgency}")    # emergency

if assessment.urgency == "emergency":
    print("\nEMERGENCY PROTOCOL:")
    for action in assessment.recommended_actions:
        print(f"  [!] {action}")
```

---

## Common Patterns and Recipes

### Pattern 1 — Batch assessment for a health camp

```python
from aumai_vaidyaai.core import HealthAdvisor, SymptomDatabase
from aumai_vaidyaai.models import MedicalSystem

db = SymptomDatabase()
advisor = HealthAdvisor()

# Patient data from a rural health camp
patients = [
    ("P001", ["fever", "joint pain", "rash"]),
    ("P002", ["chest pain", "breathlessness", "sweating"]),
    ("P003", ["persistent cough", "weight loss", "night sweats"]),
    ("P004", ["diarrhoea", "vomiting", "abdominal cramps"]),
]

emergency_cases = []
urgent_cases = []

for patient_id, symptom_names in patients:
    symptoms = [db.normalise(s) for s in symptom_names]
    assessment = advisor.assess(symptoms, MedicalSystem.allopathy)

    if assessment.urgency == "emergency":
        emergency_cases.append(patient_id)
    elif assessment.urgency == "urgent":
        urgent_cases.append(patient_id)

print(f"Emergency referrals : {emergency_cases}")
print(f"Urgent referrals    : {urgent_cases}")
```

### Pattern 2 — Dengue/Malaria differential for a field worker

```python
from aumai_vaidyaai.core import ConditionMatcher, SymptomDatabase

db = SymptomDatabase()
matcher = ConditionMatcher()

# High fever + joint pain pattern — dengue or chikungunya?
symptoms = [
    db.normalise("high fever"),
    db.normalise("severe headache"),
    db.normalise("joint pain"),
    db.normalise("rash"),
    db.normalise("eye pain"),
]

conditions = matcher.match(symptoms)
print("Differential diagnosis (keyword-based — not clinical):")
for c in conditions:
    print(f"  {c['name']:<30} {c['likelihood_pct']:3}%  [{c['urgency']}]  ICD: {c['icd_code']}")
    print(f"    Matched: {', '.join(c['matched_symptoms'])}")
```

### Pattern 3 — Ayurvedic wellness for a community program

```python
from aumai_vaidyaai.core import AYUSHAdvisor, SymptomDatabase

db = SymptomDatabase()
ayush = AYUSHAdvisor()

# Stress and joint-related symptoms
symptoms = [db.normalise(s) for s in ["joint pain", "fatigue", "headache"]]
suggestions = ayush.ayurvedic_perspective(symptoms)

print("Ayurvedic wellness context:")
for s in suggestions:
    print(f"  - {s}")
```

### Pattern 4 — Direct use of SimpleSymptom with custom severity

```python
from aumai_vaidyaai.core import ConditionMatcher
from aumai_vaidyaai.models import SimpleSymptom

# Create symptoms directly with custom severity
symptoms = [
    SimpleSymptom(name="fever", body_area="general", severity="severe"),
    SimpleSymptom(name="breathlessness", body_area="chest", severity="severe"),
    SimpleSymptom(name="cough with sputum", body_area="chest", severity="moderate"),
    SimpleSymptom(name="chest pain", body_area="chest", severity="severe"),
    SimpleSymptom(name="fatigue", body_area="general", severity="moderate"),
]

matcher = ConditionMatcher()
conditions = matcher.match(symptoms)

for c in conditions[:3]:
    print(f"{c['name']}: {c['likelihood_pct']}% — {c['urgency']}")
```

### Pattern 5 — Multi-language wrapper integration

```python
# aumai-vaidyaai outputs English text. For Hindi integration, wrap the
# assessment output in your own i18n layer.

from aumai_vaidyaai.core import HealthAdvisor, SymptomDatabase
from aumai_vaidyaai.models import MedicalSystem

db = SymptomDatabase()
advisor = HealthAdvisor()

# Hindi symptom names are not directly supported — normalise from a
# translated list before passing to the engine
hindi_to_english_symptoms = {
    "बुखार": "fever",
    "सिरदर्द": "headache",
    "खांसी": "cough",
}

hindi_input = ["बुखार", "सिरदर्द", "खांसी"]
english_symptoms = [
    db.normalise(hindi_to_english_symptoms.get(s, s)) for s in hindi_input
]

assessment = advisor.assess(english_symptoms, MedicalSystem.allopathy)
print(f"Urgency: {assessment.urgency}")
```

---

## Troubleshooting FAQ

**Q: `assess` returns no conditions. Why?**

A: The condition matching requires a minimum number of symptoms to overlap with
a condition's known symptom list (`min_match`). For most conditions this is 2-3
symptoms. Check that you are using exact symptom names from the database (run
`vaidyaai symptoms` to see the list). Underscores in CLI are auto-converted to
spaces; in Python use `db.normalise()`.

---

**Q: "Acute Coronary Syndrome" keeps appearing even for mild symptoms. Why?**

A: Conditions like ACS have `min_match=2` because missing it is far more dangerous
than a false positive. If even 2 of its symptoms (e.g. "chest pain" + "sweating")
are present, it is returned as a match. This is intentional safety design. The
likelihood percentage will be low, and the note clearly states this is
keyword-based, not a clinical probability.

---

**Q: Can I add new conditions to the catalogue?**

A: Yes. Add an entry to `_CONDITIONS` in `core.py` with all required fields:
`name`, `matching_symptoms`, `min_match`, `description`, `urgency`, `icd_code`.
Then add a test. Open a pull request.

---

**Q: Can I run this offline on a device with no internet?**

A: Yes. The entire library is self-contained. No external HTTP calls are made.
Install once with pip while online, then use fully offline.

---

**Q: The Ayurvedic suggestions seem generic. How does the mapping work?**

A: `AYUSHAdvisor` uses substring matching on symptom names against keys in
`_AYURVEDIC_MAPPINGS` (keys: `fever`, `cough`, `headache`, `joint pain`,
`digestive`, `stress`, `general`). If a symptom name contains one of these keys,
the corresponding suggestions are included. If nothing matches, the `"general"`
key's suggestions are used as a fallback. This is intentionally conservative.

---

**Q: How do I distinguish between Dengue and Malaria using this tool?**

A: Both will appear as matched conditions when the relevant symptom overlap exists.
The `matched_symptoms` field on each matched condition shows you exactly which
reported symptoms matched. The `likelihood_pct` score (capped at 95%) can be used
to rank them. However, this is keyword matching only — a blood smear (for malaria)
or NS1 antigen test (for dengue) is required for clinical confirmation.

---

**Q: The `serve` command fails with an import error.**

A: The REST API module requires `uvicorn`. Install it:
```bash
pip install uvicorn
```
Note that the `aumai_vaidyaai.api` module itself is not yet implemented in v0.1.0.

---

## Next Steps

- [API Reference](api-reference.md) — full class and method documentation
- [Examples](../examples/quickstart.py) — runnable Python demos
- [CONTRIBUTING.md](../CONTRIBUTING.md) — contribution guidelines
- [NHP India](https://www.nhp.gov.in) — National Health Portal resources
- [AYUSH Ministry](https://main.ayush.gov.in) — AYUSH system guidelines
