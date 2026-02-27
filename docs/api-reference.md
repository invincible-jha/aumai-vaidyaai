# API Reference — aumai-vaidyaai

Complete reference for all public classes, functions, and Pydantic models.

> **Medical Disclaimer:** This tool does NOT provide medical advice, diagnosis, or
> treatment. Symptom analysis is based on keyword matching only. Always consult
> a qualified healthcare professional for medical concerns.

---

## Module: `aumai_vaidyaai.core`

Core symptom-assessment logic. Contains the symptom database, condition matcher,
AYUSH advisor, and the orchestrating health advisor.

---

### `class SymptomDatabase`

Database of 100+ common symptoms with body area mappings. Used to normalise raw
symptom strings into structured `SimpleSymptom` objects.

#### `SymptomDatabase.get_body_area(symptom_name: str) -> str`

Return the body area for a given symptom name.

**Parameters:**

| Parameter      | Type  | Description                              |
|----------------|-------|------------------------------------------|
| `symptom_name` | `str` | Symptom name, looked up after lowercasing. |

**Returns:** `str` — one of `"head"`, `"general"`, `"chest"`, `"abdomen"`,
`"urinary"`, `"skin"`, `"musculoskeletal"`. Returns `"general"` if the symptom
is not in the body area mapping.

**Example:**

```python
from aumai_vaidyaai.core import SymptomDatabase

db = SymptomDatabase()
print(db.get_body_area("chest pain"))              # chest
print(db.get_body_area("right lower abdominal pain"))  # abdomen
print(db.get_body_area("unknown symptom"))         # general
```

---

#### `SymptomDatabase.normalise(symptom_name: str) -> SimpleSymptom`

Create a `SimpleSymptom` object from a plain symptom name string. Strips whitespace,
lowercases, and looks up the body area.

**Parameters:**

| Parameter      | Type  | Description                          |
|----------------|-------|--------------------------------------|
| `symptom_name` | `str` | Raw symptom name from user input.    |

**Returns:** `SimpleSymptom` with `severity` defaulting to `"mild"`.

**Example:**

```python
db = SymptomDatabase()
s = db.normalise("  Chest Pain  ")
print(s.name)        # "chest pain"
print(s.body_area)   # "chest"
print(s.severity)    # "mild"
```

---

#### `SymptomDatabase.all_symptom_names() -> list[str]`

Return all known symptom names from the body area mapping.

**Returns:** `list[str]` — all 100+ symptom names. Order is dict-insertion order
(Python 3.7+).

**Example:**

```python
db = SymptomDatabase()
symptoms = db.all_symptom_names()
print(len(symptoms))          # 100+
print(sorted(symptoms)[:5])   # ['abdominal cramps', 'abdominal pain', ...]
```

---

### `class ConditionMatcher`

Rule-based symptom-to-condition matcher. Operates entirely on `SimpleSymptom`
objects. Does not use machine learning.

#### `ConditionMatcher.match(symptoms: list[SimpleSymptom]) -> list[dict[str, object]]`

Return conditions matching the provided symptoms, ranked by overlap score.

**Parameters:**

| Parameter  | Type                    | Description                         |
|------------|-------------------------|-------------------------------------|
| `symptoms` | `list[SimpleSymptom]`   | List of reported symptoms.          |

**Returns:** `list[dict[str, object]]` — list of condition dicts, sorted descending
by `likelihood_pct`. Each dict contains:

| Key                | Type        | Description                                                      |
|--------------------|-------------|------------------------------------------------------------------|
| `name`             | `str`       | Condition name (e.g. `"Dengue"`)                                 |
| `icd_code`         | `str`       | ICD-10 code                                                      |
| `description`      | `str`       | Short clinical description, includes urgency note for emergencies |
| `likelihood_pct`   | `int`       | Overlap score as percentage, capped at 95                        |
| `likelihood_note`  | `str`       | Always `"Estimated by keyword matching only — not a clinical probability."` |
| `urgency`          | `str`       | `"routine"`, `"urgent"`, or `"emergency"`                        |
| `matched_symptoms` | `list[str]` | Symptom names from the condition's list that appeared in input   |

**Algorithm:**

1. Build a set of input symptom names (lowercased).
2. For each condition in `_CONDITIONS`, count the overlap with `matching_symptoms`.
3. If `overlap >= condition['min_match']`, include the condition.
4. `likelihood_pct = min(round(overlap / len(matching_symptoms) * 100), 95)`.
5. Sort descending by `likelihood_pct`.

**Example:**

```python
from aumai_vaidyaai.core import ConditionMatcher, SymptomDatabase

db = SymptomDatabase()
matcher = ConditionMatcher()

symptoms = [db.normalise(s) for s in ["high fever", "joint pain", "rash", "eye pain"]]
conditions = matcher.match(symptoms)

for c in conditions:
    print(f"{c['name']:30} {c['likelihood_pct']:3}%  urgency={c['urgency']}")
    print(f"  matched: {c['matched_symptoms']}")
```

---

#### `ConditionMatcher.assess_urgency(conditions: list[dict[str, object]]) -> str`

Determine the highest urgency level across all matched conditions.

**Parameters:**

| Parameter    | Type                         | Description                           |
|--------------|------------------------------|---------------------------------------|
| `conditions` | `list[dict[str, object]]`    | Output of `match()`.                  |

**Returns:** `str` — `"emergency"` if any condition has `urgency="emergency"`;
otherwise `"urgent"` if any has `urgency="urgent"`; otherwise `"routine"`.

**Example:**

```python
matcher = ConditionMatcher()
urgency = matcher.assess_urgency([
    {"urgency": "routine"},
    {"urgency": "urgent"},
])
print(urgency)   # "urgent"

urgency = matcher.assess_urgency([
    {"urgency": "routine"},
    {"urgency": "emergency"},
])
print(urgency)   # "emergency"
```

---

### `class AYUSHAdvisor`

Provides traditional Ayurvedic general wellness perspectives. This is NOT medical
advice. All suggestions are general wellness context only.

#### `AYUSHAdvisor.ayurvedic_perspective(symptoms: list[SimpleSymptom]) -> list[str]`

Return Ayurvedic general wellness suggestions for the given symptom set.

**Parameters:**

| Parameter  | Type                  | Description                |
|------------|-----------------------|----------------------------|
| `symptoms` | `list[SimpleSymptom]` | Reported symptoms.         |

**Returns:** `list[str]` — a deduplicated list of Ayurvedic wellness suggestion
strings. Always ends with a reminder to consult a registered BAMS physician and the
mandatory medical disclaimer string.

**Mapping keys:** `"fever"`, `"cough"`, `"headache"`, `"joint pain"`,
`"digestive"`, `"stress"`, `"general"` (fallback if no match found).

**Example:**

```python
from aumai_vaidyaai.core import AYUSHAdvisor, SymptomDatabase

db = SymptomDatabase()
ayush = AYUSHAdvisor()

symptoms = [db.normalise(s) for s in ["fever", "cough"]]
suggestions = ayush.ayurvedic_perspective(symptoms)
for s in suggestions:
    print(f"  - {s}")
# - Giloy (Tinospora cordifolia) kadha is traditionally used for immune support.
# - Stay hydrated with warm water and ginger tea.
# - Tulsi (Holy Basil) honey ginger tea is a traditional respiratory support.
# - Consult a registered Ayurvedic physician (BAMS) for personalised treatment.
# - IMPORTANT MEDICAL DISCLAIMER: ...
```

---

### `class HealthAdvisor`

Orchestrates symptom assessment across multiple medical systems. This is the
primary entry point for end-to-end assessments.

#### `HealthAdvisor.__init__()`

No arguments. Instantiates a `ConditionMatcher` and an `AYUSHAdvisor` internally.

```python
from aumai_vaidyaai.core import HealthAdvisor
advisor = HealthAdvisor()
```

---

#### `HealthAdvisor.assess(symptoms: list[SimpleSymptom], system: MedicalSystem) -> HealthAssessment`

Generate a `HealthAssessment` for the given symptoms and medical system.

**Parameters:**

| Parameter  | Type                  | Description                                                  |
|------------|-----------------------|--------------------------------------------------------------|
| `symptoms` | `list[SimpleSymptom]` | List of normalised symptom objects.                          |
| `system`   | `MedicalSystem`       | Medical system for which to generate recommended actions.    |

**Returns:** `HealthAssessment`

**Behaviour:**

1. Calls `ConditionMatcher.match(symptoms)` to get scored conditions.
2. Calls `ConditionMatcher.assess_urgency(conditions)` to get overall urgency.
3. If urgency is `"emergency"`: `recommended_actions = _EMERGENCY_ACTIONS + _SYSTEM_ACTIONS[system]`.
4. Otherwise: `recommended_actions = _SYSTEM_ACTIONS[system]`.
5. If system is `MedicalSystem.ayurveda`: Ayurvedic suggestions are prepended.
6. The mandatory `MEDICAL_DISCLAIMER` is appended to all action lists.
7. Actions are deduplicated while preserving order.
8. Returns a `HealthAssessment` with all fields populated.

**Raises:** No exceptions under normal operation. Will raise `ValidationError` if
`system` is not a valid `MedicalSystem` enum value.

**Example:**

```python
from aumai_vaidyaai.core import HealthAdvisor, SymptomDatabase
from aumai_vaidyaai.models import MedicalSystem

db = SymptomDatabase()
advisor = HealthAdvisor()

symptoms = [db.normalise(s) for s in ["persistent cough", "weight loss", "night sweats", "fever"]]
assessment = advisor.assess(symptoms, MedicalSystem.allopathy)

print(f"Urgency   : {assessment.urgency}")     # urgent
print(f"Conditions: {len(assessment.possible_conditions)}")
for c in assessment.possible_conditions:
    print(f"  {c['name']}: {c['likelihood_pct']}%")
for action in assessment.recommended_actions:
    print(f"  -> {action}")
```

---

## Module: `aumai_vaidyaai.models`

Pydantic v2 data models for the health assessment system.

---

### `class SymptomCategory`

Enum for categorising symptoms by body system.

```python
class SymptomCategory(str, Enum):
    general         = "general"
    respiratory     = "respiratory"
    digestive       = "digestive"
    musculoskeletal = "musculoskeletal"
    skin            = "skin"
    neurological    = "neurological"
```

---

### `class MedicalSystem`

Enum representing the six recognised medical systems under AYUSH plus allopathy.

```python
class MedicalSystem(str, Enum):
    allopathy  = "allopathy"
    ayurveda   = "ayurveda"
    yoga       = "yoga"
    unani      = "unani"
    siddha     = "siddha"
    homeopathy = "homeopathy"
```

**Example:**

```python
from aumai_vaidyaai.models import MedicalSystem

system = MedicalSystem.ayurveda
print(system.value)          # "ayurveda"
print(system in MedicalSystem)  # True

# Iterate all systems
for s in MedicalSystem:
    print(s.value)
```

---

### `class SimpleSymptom`

Lightweight symptom model used for CLI and API input.

**Fields:**

| Field       | Type  | Required | Default     | Constraints                          | Description                            |
|-------------|-------|----------|-------------|--------------------------------------|----------------------------------------|
| `name`      | `str` | Yes      | —           | —                                    | Symptom name, lowercased               |
| `body_area` | `str` | No       | `"general"` | —                                    | Body area affected                     |
| `severity`  | `str` | No       | `"mild"`    | `^(mild\|moderate\|severe)$`         | Symptom severity level                 |

**Example:**

```python
from aumai_vaidyaai.models import SimpleSymptom

s = SimpleSymptom(name="chest pain", body_area="chest", severity="severe")
print(s.model_dump())
# {'name': 'chest pain', 'body_area': 'chest', 'severity': 'severe'}

# Default severity
s2 = SimpleSymptom(name="headache")
print(s2.severity)   # "mild"
```

---

### `class Symptom`

Full symptom model for the knowledge base (not used in the main assessment flow;
used for knowledge base representation).

**Fields:**

| Field            | Type              | Required | Default  | Description                          |
|------------------|-------------------|----------|----------|--------------------------------------|
| `code`           | `str`             | Yes      | —        | Unique symptom code                  |
| `name`           | `str`             | Yes      | —        | Human-readable symptom name          |
| `category`       | `SymptomCategory` | Yes      | —        | Body system category                 |
| `severity_range` | `tuple[int, int]` | No       | `(1, 10)` | Min/max severity scores             |

---

### `class Recommendation`

A treatment recommendation from a specific medical system (knowledge base model).

**Fields:**

| Field              | Type          | Required | Constraints                                                | Description                                 |
|--------------------|---------------|----------|------------------------------------------------------------|---------------------------------------------|
| `system`           | `MedicalSystem` | Yes    | —                                                          | Medical system providing the recommendation |
| `condition`        | `str`         | Yes      | —                                                          | Condition being addressed                   |
| `description`      | `str`         | Yes      | —                                                          | Full recommendation text                    |
| `urgency`          | `str`         | Yes      | `^(self_care\|see_doctor\|urgent\|emergency)$`             | Urgency of the recommendation               |
| `seek_professional`| `bool`        | Yes      | —                                                          | Whether professional consultation is needed |

---

### `class SymptomAssessment`

Full assessment result (knowledge base model).

**Fields:**

| Field                | Type                         | Required | Default              | Description                          |
|----------------------|------------------------------|----------|----------------------|--------------------------------------|
| `symptoms`           | `list[str]`                  | Yes      | —                    | Reported symptom codes               |
| `matched_conditions` | `list[dict[str, object]]`    | No       | `[]`                 | Conditions matched with scores       |
| `recommendations`    | `list[Recommendation]`       | No       | `[]`                 | Per-system recommendations           |
| `triage_level`       | `str`                        | Yes      | —                    | `"green"`, `"amber"`, or `"red"`    |
| `disclaimer`         | `str`                        | No       | `MEDICAL_DISCLAIMER` | Mandatory disclaimer                 |

---

### `class Condition`

A medical condition in the knowledge base.

**Fields:**

| Field               | Type                  | Required | Default | Description                              |
|---------------------|-----------------------|----------|---------|------------------------------------------|
| `code`              | `str`                 | Yes      | —       | Unique condition code                    |
| `name`              | `str`                 | Yes      | —       | Condition name                           |
| `symptoms_required` | `list[str]`           | Yes      | —       | Symptom codes that must be present       |
| `symptoms_optional` | `list[str]`           | No       | `[]`    | Symptom codes that may be present        |
| `systems`           | `list[MedicalSystem]` | Yes      | —       | Systems with known management            |

---

### `class HealthAssessment`

Primary output model from `HealthAdvisor.assess()`.

**Fields:**

| Field                  | Type                         | Required | Default              | Constraints                              | Description                              |
|------------------------|------------------------------|----------|----------------------|------------------------------------------|------------------------------------------|
| `symptoms`             | `list[SimpleSymptom]`        | Yes      | —                    | —                                        | Input symptoms, preserved from input     |
| `possible_conditions`  | `list[dict[str, object]]`    | Yes      | —                    | —                                        | Matched conditions with scores           |
| `recommended_actions`  | `list[str]`                  | Yes      | —                    | —                                        | Ordered list of recommended next actions |
| `urgency`              | `str`                        | Yes      | —                    | `^(routine\|urgent\|emergency)$`         | Overall urgency level                    |
| `system`               | `MedicalSystem`              | Yes      | —                    | —                                        | Medical system used for recommendations  |
| `disclaimer`           | `str`                        | No       | `MEDICAL_DISCLAIMER` | —                                        | Mandatory disclaimer                     |

**Example:**

```python
from aumai_vaidyaai.models import HealthAssessment, MedicalSystem, SimpleSymptom

assessment = HealthAssessment(
    symptoms=[SimpleSymptom(name="fever")],
    possible_conditions=[],
    recommended_actions=["Consult a physician."],
    urgency="routine",
    system=MedicalSystem.allopathy,
)
print(assessment.urgency)    # "routine"
print(assessment.disclaimer)  # mandatory disclaimer string
```

---

### `MEDICAL_DISCLAIMER`

Module-level constant in `models.py`:

```
"IMPORTANT MEDICAL DISCLAIMER: This tool does NOT provide medical advice,
diagnosis, or treatment. Symptom analysis is based on keyword matching only
and may be inaccurate. Always consult a qualified healthcare professional for
medical concerns. In emergencies, contact your nearest hospital immediately."
```

Embedded in every `HealthAssessment` and every CLI output.

---

## Module: `aumai_vaidyaai.cli`

CLI entry point built with Click. Accessed via the `vaidyaai` command.

### Commands

| Command             | Description                                                 |
|---------------------|-------------------------------------------------------------|
| `vaidyaai assess`   | Assess symptoms and generate health recommendations         |
| `vaidyaai symptoms` | List all known symptoms in the database                     |
| `vaidyaai serve`    | Start the REST API server (requires uvicorn)                |

---

## Public API Surface (`__all__`)

### `aumai_vaidyaai.core`

```python
__all__ = ["SymptomDatabase", "ConditionMatcher", "AYUSHAdvisor", "HealthAdvisor"]
```

### `aumai_vaidyaai.models`

```python
__all__ = [
    "SymptomCategory", "Symptom", "MedicalSystem", "Recommendation",
    "SymptomAssessment", "Condition", "HealthAssessment", "SimpleSymptom",
    "MEDICAL_DISCLAIMER",
]
```

---

## Version

```python
import aumai_vaidyaai
print(aumai_vaidyaai.__version__)   # 0.1.0
```
