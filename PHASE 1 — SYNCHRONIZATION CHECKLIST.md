# PHASE 1 — SYNCHRONIZATION CHECKLIST + NAMING / REFERENCE CONVENTIONS

---

# 1. Synchronization checklist

Use this whenever you add, rename, remove, or revise a contract, step, or validation rule.

## A. Contract change checklist

Use this when changing an object like `ResumeArtifact`, `MatchAnalysis`, `GapAnalysis`, etc.

| Check | Question | Required action |
|---|---|---|
| Semantic check | Did the meaning of the object change? | Update `PHASE1_CONTRACTS_SPEC.md` |
| Structural check | Did fields/types/enums change? | Update `contracts.py` |
| Config check | Is the object referenced in workflow config? | Update `.json` references if needed |
| Producer check | Which module creates it? | Update producer code |
| Consumer check | Which modules read it? | Update downstream code |
| Validation check | Are new constraints enforced? | Add/update validators |
| UI check | Is it displayed anywhere? | Update rendering logic |

---

## B. Step change checklist

Use this when changing workflow sequence or a specific step.

| Check | Question | Required action |
|---|---|---|
| Identity check | Did `step_id` change? | Update all `.json`, router consumers, UI references |
| Order check | Did step order change? | Update `step_registry.json` |
| Input check | Did required inputs change? | Update step metadata and producers |
| Output check | Did outputs change? | Update step metadata and contracts if needed |
| Unlock check | Did transition logic change? | Update `step_registry.json` and router logic if necessary |
| Validation check | Did completion requirements change? | Update `validation_rules.json` and validators |
| UX check | Does guidance text or step label change? | Update config/UI text |

---

## C. Validation rule checklist

Use this when adding or editing rules.

| Check | Question | Required action |
|---|---|---|
| Rule ID check | Is the rule ID unique? | Verify naming convention |
| Step linkage | Does the rule point to a real `step_id`? | Validate against registry |
| Field linkage | Does `target_field` exist in expected payload/contract? | Verify against `contracts.py` |
| Condition check | Can `validators.py` interpret the condition? | Add logic if needed |
| UX check | Is the error message user-safe and clear? | Revise message text |

---

# 2. Naming conventions

## A. Contract class names (PascalCase)

Examples:
- `UserSession`
- `WorkflowState`
- `StepState`
- `ResumeArtifact`
- `JobDescriptionArtifact`
- `MatchAnalysis`
- `GapAnalysis`
- `RevisionSuggestion`
- `CoverLetterDraft`
- `GeneratedArtifact`
- `ExportBundle`

Rule:
Contract names in `.md`, `contracts.py`, and `.json` must match exactly.

---

## B. Step IDs (snake_case)

Examples:
- `resume_intake`
- `job_description_intake`
- `match_analysis`
- `gap_analysis`
- `summary_revision`
- `experience_revision`
- `skills_revision`
- `cover_letter_generation`
- `final_review`
- `export_bundle`

Rules:
- no spaces
- IDs remain stable
- labels can change, IDs cannot

---

## C. Validation rule IDs

Pattern:
`<step_id>__<field_or_target>__<rule_purpose>`

Examples:
- `resume_intake__raw_text__required`
- `job_description_intake__raw_text__required`
- `resume_intake__raw_text__min_length`

---

## D. Enum values (snake_case strings)

Examples:
- `not_started`
- `in_progress`
- `failed_validation`
- `pasted_text`
- `uploaded_file`

---

## E. Artifact IDs vs types

### artifact_type (classification)
- `resume_revision`
- `cover_letter`
- `analysis_summary`

### artifact_id (instance)
- UUID or generated ID

Rule:
Type = category  
ID = instance  

---

# 3. Reference conventions

## A. JSON references contracts (does not define them)

Good:
```json
{
  "outputs_produced": ["MatchAnalysis"]
}
```

Bad:
```json
{
  "outputs_produced": [
    {
      "name": "MatchAnalysis",
      "fields": ["overall_score"]
    }
  ]
}
```

---

## B. Logic uses IDs, not labels

Good:
- `step_id = "gap_analysis"`

Bad:
- `"Gap Analysis"` used in logic

---

## C. UI displays labels, logic uses IDs

---

## D. Validation rules must target real fields

Target fields must exist in payload or contract.

---

# 4. Source-of-truth policy

| Concern | Source of truth |
|---|---|
| Semantics | `.md` |
| Structure | `contracts.py` |
| Workflow behavior | `.json` |
| Execution | runtime `.py` |

---

# 5. Change policy

## If you change meaning
1. `.md`
2. `contracts.py`
3. runtime / `.json`

## If you change structure
1. `.md`
2. `contracts.py`
3. all consumers

## If you change workflow
1. `.json`
2. router/UI if needed

## If you change UI only
1. `.json` or UI code

---

# 6. Minimal lint rules

## Contract lint
- every contract in `.json` exists in `contracts.py`

## Step lint
- unique `step_id`
- unique `step_order`

## Validation lint
- valid `rule_id`
- valid `step_id`
- valid `target_field`

## Runtime lint
- no undocumented fields
- no arbitrary dict structures (post-MVP)

---

# 7. Recommended conventions file

Create:
`PHASE1_NAMING_AND_SYNC_RULES.md`

Include:
- naming rules
- sync rules
- change policy
- checklist

---

# 8. Example change flow

Rename field:
`revision_priorities` → `recommended_revisions`

Steps:
1. update `.md`
2. update `contracts.py`
3. update producers
4. update consumers
5. update UI
6. verify `.json`

---

# 9. Final doctrine

Contracts are:
- defined in `.md`
- implemented in `contracts.py`
- referenced in `.json`
- enforced in runtime code

Rules:
- no structure only in `.json`
- no semantics only in runtime code
- no logic using labels

---

# FINAL SUMMARY

`.md` → defines  
`contracts.py` → formalizes  
`.json` → configures  
runtime `.py` → executes