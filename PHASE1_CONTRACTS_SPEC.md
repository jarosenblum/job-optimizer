# PHASE1_CONTRACTS_SPEC.md

## Purpose

This document defines the canonical Phase 1 contracts for the Guided Workflow MVP of the job optimization app.

In this architecture:

- a **schema** defines structural fields and types
- a **contract** includes schema + constraints + lifecycle + usage + guarantees

This document is the semantic and behavioral source of truth for Phase 1 objects.

Runtime enforcement occurs in Python.
Workflow configuration occurs in JSON.

---

# Contract Template

Each contract includes:

1. Purpose
2. Schema
3. Constraints
4. Lifecycle
5. Produced By
6. Consumed By
7. Guarantees
8. Disallowed Behavior

---

# 1. UserSession

## Purpose
Tracks the current in-app working session for a user during a guided optimization run.

## Schema
- session_id: string
- created_at: datetime
- updated_at: datetime
- active_workflow_id: string
- active_step_id: string
- completed_step_ids: list[string]
- ui_state: object
  - show_guidance_panel: boolean
  - show_artifact_panel: boolean

## Constraints
- session_id is required
- active_step_id must correspond to a valid StepDefinition
- completed_step_ids may only include valid step IDs
- updated_at must refresh on any workflow-relevant change
- ui_state affects presentation only and must not determine workflow truth

## Lifecycle
- created at session start
- updated throughout user navigation
- ends when session expires or is persisted into longer-term run state

## Produced By
- session initialization logic

## Consumed By
- workflow router
- step navigation UI
- guidance panel
- artifact panel

## Guarantees
- always exposes current workflow location
- always exposes session-level UI state

## Disallowed Behavior
- may not be treated as the canonical historical record of a run

---

# 2. WorkflowState

## Purpose
Represents the overall state of a guided optimization workflow.

## Schema
- workflow_id: string
- workflow_name: string
- current_step_id: string
- status: enum[not_started, in_progress, complete, blocked]
- step_states: list[StepState]
- resume_artifact_id: string|null
- job_description_artifact_id: string|null
- latest_match_analysis_id: string|null
- latest_gap_analysis_id: string|null
- generated_artifact_ids: list[string]
- candidate_asset_set_id: string|null
- latest_cover_letter_strategy_id: string|null
- latest_resume_revision_artifact_id: string|null

## Constraints
- current_step_id is required
- status must be one of the allowed enum values
- step_states must correspond to defined workflow steps
- artifact references must remain null until produced
- new object references must remain null until the corresponding object is produced
- only one step may be current at a time

## Lifecycle
- initialized at workflow start
- updated whenever progression occurs
- may later be persisted as OptimizationRun in Phase 2

## Produced By
- workflow initializer
- workflow router

## Consumed By
- step renderer
- validator layer
- export logic
- navigation logic

## Guarantees
- always exposes authoritative current workflow progress for the active run

## Disallowed Behavior
- may not reference undefined steps or phantom artifacts

---

# 3. StepState

## Purpose
Represents the runtime state of an individual workflow step.

## Schema
- step_id: string
- status: enum[locked, available, in_progress, complete, failed_validation]
- is_unlocked: boolean
- is_required: boolean
- input_refs: list[string]
- output_refs: list[string]
- validation_status: string
- validation_messages: list[string]
- started_at: datetime|null
- completed_at: datetime|null

## Constraints
- step_id is required
- completed_at may only exist when status = complete
- output_refs may only reference outputs valid for that step
- a required step cannot be skipped without explicit system support
- status must align with validation outcome

## Lifecycle
- begins locked or available
- progresses to in_progress
- resolves to complete or failed_validation

## Produced By
- router
- validator layer

## Consumed By
- navigation UI
- guidance panel
- workflow progression logic

## Guarantees
- exposes step-level readiness and completion state

## Disallowed Behavior
- may not show complete if validation failed

---
# CandidateAssetSet

## Purpose
Represents the full set of candidate-provided intake assets for the workflow.

## Schema
- asset_set_id: string
- resume_text: string|null
- job_description_text: string|null
- cover_letter_text: string|null
- candidate_notes: string|null
- has_resume: boolean
- has_job_description: boolean
- has_cover_letter: boolean
- is_intake_complete: boolean

## Constraints
- resume_text and job_description_text are required for baseline intake completeness
- cover_letter_text is optional for MVP, but should be tracked explicitly if present
- has_* fields must reflect actual presence/absence of the corresponding text fields
- is_intake_complete should be true only when the minimum required Phase 1 inputs are present

## Lifecycle
- created during intake
- updated as user provides or edits inputs
- reused by downstream analysis and revision steps

## Produced By
- intake UI
- session/app state logic

## Consumed By
- intake validation
- resume parser
- job parser
- cover-letter strategy generation
- guidance UI

## Guarantees
- provides a single coherent view of intake completeness
- makes missing assets visible to the workflow and UI

## Disallowed Behavior
- may not mark intake complete when required assets are absent

---

# 4. StepDefinition

## Purpose
Defines a workflow step declaratively.

## Schema
- step_id: string
- step_name: string
- step_order: integer
- description: string
- inputs_required: list[string]
- outputs_produced: list[string]
- validation_rule_ids: list[string]
- unlock_condition: string
- is_required: boolean

## Constraints
- step_id must be unique
- step_order must be unique within the workflow
- inputs_required must refer to valid object names or prior outputs
- outputs_produced must correspond to valid contracts
- unlock_condition must be interpretable by the router/validator layer

## Lifecycle
- defined statically in workflow config
- loaded at app start

## Produced By
- workflow config

## Consumed By
- step registry
- router
- navigation UI
- validators

## Guarantees
- provides canonical step metadata for Phase 1 workflow behavior

## Disallowed Behavior
- may not define duplicate step IDs or ambiguous order values

---

# 5. ValidationRule

## Purpose
Defines a validation condition for a step or object.

## Schema
- rule_id: string
- rule_name: string
- step_id: string
- rule_type: enum[required_field, non_empty, min_length, contract_presence, cross_step_dependency]
- target_field: string|null
- condition: string
- error_message: string

## Constraints
- rule_id must be unique
- step_id must refer to a valid step
- condition must map to code-supported logic
- error_message must be displayable to the user

## Lifecycle
- defined statically
- applied at validation time

## Produced By
- validation config

## Consumed By
- validator engine
- guidance panel

## Guarantees
- yields explainable failure conditions

## Disallowed Behavior
- may not reference nonexistent steps or fields

---

# 6. ValidationResult

## Purpose
Stores the result of applying validation rules.

## Schema
- step_id: string
- is_valid: boolean
- passed_rule_ids: list[string]
- failed_rule_ids: list[string]
- messages: list[string]

## Constraints
- is_valid = true only if failed_rule_ids is empty
- messages must be safe for UI display

## Lifecycle
- produced on step validation
- may be regenerated as user input changes

## Produced By
- validator engine

## Consumed By
- router
- step UI
- guidance panel

## Guarantees
- provides a structured explanation of validation status

## Disallowed Behavior
- may not mark valid when failed rules exist

---

# 7. ResumeArtifact

## Purpose
Normalized representation of the user's resume.

## Schema
- resume_id: string
- raw_text: string
- candidate_name: string|null
- contact_info: object
  - email: string|null
  - phone: string|null
  - location: string|null
- summary: string|null
- experience: list[ResumeExperienceItem]
- education: list[ResumeEducationItem]
- skills: list[string]
- source_type: enum[pasted_text, uploaded_file]

## Constraints
- resume_id is required
- raw_text must always be preserved
- parsed sections may be partial but object must remain valid
- arrays should be normalized even if empty

## Lifecycle
- created when user submits resume
- reused throughout all downstream steps

## Produced By
- resume parser

## Consumed By
- match engine
- gap engine
- revision engines
- cover letter generator

## Guarantees
- preserves original resume text and normalized sections

## Disallowed Behavior
- must not silently discard raw input

---
# ResumeRevisionArtifact

## Purpose
Represents a compiled resume-revision output for user review and copying.

## Schema
- resume_revision_id: string
- revised_summary: string|null
- revised_experience_bullets: list[string]
- revised_skills_section: list[string]
- section_notes: list[string]
- full_revision_text: string

## Constraints
- full_revision_text is required
- revised content must remain grounded in candidate evidence
- revised_summary may be null if not yet produced, but full artifact should still remain renderable

## Lifecycle
- produced after revision steps
- updated as revision outputs accumulate
- consumed by artifact display and export

## Produced By
- revision engines
- artifact builder

## Consumed By
- artifact panel
- final review
- export logic

## Guarantees
- provides a first-class resume redesign artifact rather than scattered suggestions

## Disallowed Behavior
- may not fabricate unsupported experience or credentials

---

# 8. JobDescriptionArtifact

## Purpose
Normalized representation of the target role.

## Schema
- job_description_id: string
- raw_text: string
- job_title: string|null
- company_name: string|null
- responsibilities: list[string]
- required_skills: list[string]
- preferred_skills: list[string]
- keywords: list[string]
- source_type: enum[pasted_text, uploaded_text]

## Constraints
- raw_text must always be preserved
- extracted skills and responsibilities should be normalized where possible
- parser may infer categories but must not fabricate precise unsupported facts

## Lifecycle
- created when user submits job description
- reused by diagnostic and generation steps

## Produced By
- job parser

## Consumed By
- match engine
- gap engine
- revision engines
- cover letter generator

## Guarantees
- preserves source input and normalized targeting features

## Disallowed Behavior
- must not drop the original source text

---

# 9. MatchAnalysis

## Purpose
Represents baseline alignment between resume and job description.

## Schema
- match_analysis_id: string
- overall_score: number
- matched_skills: list[string]
- missing_skills: list[string]
- matched_keywords: list[string]
- missing_keywords: list[string]
- strengths: list[string]
- weaknesses: list[string]
- language_overlap: list[string]
- language_gaps: list[string]
- tone_mismatch_notes: list[string]
- rationale: string

## Constraints
- overall_score must be normalized to 0–100
- rationale is required
- low score should correspond to at least one weakness or missing signal
- analysis must be grounded in ResumeArtifact and JobDescriptionArtifact
- `language_overlap` should capture meaningful shared vocabulary, framing, or rhetorical patterns between candidate materials and role/organization materials
- `language_gaps` should capture important role/organization language that is absent or underrepresented in candidate materials
- `tone_mismatch_notes` should capture notable differences in register, emphasis, or rhetorical stance, and should not be used to fabricate a personality profile

## Lifecycle
- produced after resume and JD intake
- may be regenerated after revisions in later versions

## Produced By
- match engine

## Consumed By
- gap engine
- guidance panel
- revision engines

## Guarantees
- provides structured diagnostic alignment output
- exposes both evidence alignment and language-alignment signals for downstream use

## Disallowed Behavior
- may not invent evidence absent from the source artifacts
- may not treat keyword overlap alone as a complete measure of language alignment

---

# 10. GapAnalysis

## Purpose
Identifies what needs improvement for stronger alignment.

## Schema
- gap_analysis_id: string
- priority_gaps: list[string]
- missing_evidence: list[string]
- weak_sections: list[string]
- recommended_focus_areas: list[string]
- revision_priorities: list[string]
- language_gaps: list[string]
- framing_gaps: list[string]
- rationale: string

## Constraints
- must be based on source artifacts and MatchAnalysis
- priority_gaps should be ordered by importance
- focus areas must be actionable
- rationale is required
- `language_gaps` should translate language-level mismatches into revision-relevant targets
- `framing_gaps` should identify differences between how the candidate currently presents experience and how the role/organization appears to value, frame, or prioritize that experience

## Lifecycle
- produced after match analysis
- feeds revision and letter-generation stages

## Produced By
- gap engine

## Consumed By
- revision engines
- cover letter generator
- guidance panel

## Guarantees
- exposes prioritized action areas for optimization
- preserves the distinction between evidence gaps, language gaps, and framing gaps

## Disallowed Behavior
- may not remain vague or non-actionable
- may not collapse all mismatch types into a single undifferentiated gap list

---

# 11. RevisionSuggestion

## Purpose
Structured recommendation for revising a resume section.

## Schema
- revision_id: string
- target_section: enum[summary, experience, skills, education, other]
- original_text: string|null
- revised_text: string
- reason_for_change: string
- priority: enum[high, medium, low]
- alignment_focus: string

## Constraints
- revised_text is required
- reason_for_change must tie back to role alignment or gap findings
- suggestions must not invent unsupported experience
- `alignment_focus` identifies the main purpose of the revision, such as `language`, `tone`, `evidence`, or `framing`
- `alignment_focus` should be concise and suitable for UI display

## Lifecycle
- produced by section-specific revision engines
- aggregated into user-facing artifacts

## Produced By
- summary rewriter
- bullet rewriter
- skills rewriter

## Consumed By
- artifact builder
- artifact panel
- export service

## Guarantees
- provides actionable revision-ready content
- makes the purpose of a revision explicit for downstream UX and artifact rendering

## Disallowed Behavior
- may not fabricate achievements or credentials
- may not provide a revision without an intelligible alignment rationale

---

# 12. CoverLetterDraft

## Purpose
Structured targeted cover letter draft.

## Schema
- cover_letter_id: string
- job_title: string|null
- company_name: string|null
- opening: string
- body_paragraphs: list[string]
- closing: string
- tone: string
- full_text: string

## Constraints
- full_text must be reconstructible from component parts
- must align with resume evidence and role priorities
- must not claim unsupported experience
- should remain editable and exportable

## Lifecycle
- produced near end of workflow
- bundled into export outputs

## Produced By
- cover letter generator

## Consumed By
- artifact builder
- artifact panel
- export service

## Guarantees
- provides a complete letter object and renderable text

## Disallowed Behavior
- may not introduce fabricated experience or employer-specific facts absent support

---
# CoverLetterStrategy

## Purpose
Represents the strategic reasoning used to generate a targeted cover letter.

## Schema
- strategy_id: string
- target_role_language: list[string]
- candidate_strengths_to_foreground: list[string]
- priority_gaps_to_address: list[string]
- tone_guidance: list[string]
- framing_moves: list[string]
- key_messages: list[string]
- rationale: string

## Constraints
- rationale is required
- strategy must be grounded in candidate evidence, role language, and prior analysis objects
- tone_guidance and framing_moves should be actionable and suitable for downstream generation

## Lifecycle
- produced before final cover-letter draft generation
- consumed by explanation UI and cover-letter generation

## Produced By
- letter strategy engine
- analysis aggregation logic

## Consumed By
- cover-letter generator
- guidance panel
- explanation UI
- artifact panel

## Guarantees
- separates reasoning from final letter output
- makes letter generation more explainable and inspectable

## Disallowed Behavior
- may not rely on unsupported claims about the candidate or organization

---

# AnalysisExplanation

## Purpose
Represents layered explanatory text for a given analysis object or stage.

## Schema
- explanation_id: string
- analysis_type: string
- summary_text: string
- explain_text: string
- expand_text: string

## Constraints
- all three text layers are required
- summary_text should be concise
- explain_text should provide interpretive reasoning
- expand_text should provide deeper project-style analysis suitable for an expanded UI view

## Lifecycle
- produced alongside or after analysis objects
- consumed primarily by the UX layer

## Produced By
- analysis engines
- explanation builders

## Consumed By
- guidance panel
- explain/expand UI panels

## Guarantees
- supports layered explanation without collapsing analysis into bullet-only output

## Disallowed Behavior
- may not contradict the underlying analysis object it explains

---

# 13. GeneratedArtifact

## Purpose
UI-ready output artifact.

## Schema
- artifact_id: string
- artifact_type: enum[resume_revision, cover_letter, analysis_summary, copy_block, cover_letter_strategy, analysis_explanation]
- title: string
- content: string
- source_step_id: string
- format_hint: string

## Constraints
- content must be directly renderable
- source_step_id must refer to a valid step
- artifact_type must be from the allowed set

## Lifecycle
- generated by workflow steps or artifact builder
- shown in UI and optionally included in export bundle

## Produced By
- artifact builder
- step engines

## Consumed By
- artifact panel
- export bundle generator

## Guarantees
- supports immediate copy-ready consumption
- provides a single coherent view of intake completeness
- distinguishes required Phase 1 assets from optional supporting assets
- makes missing assets visible to the workflow and UI

## Disallowed Behavior
- may not reference invalid source steps

---

# 14. ExportBundle

## Purpose
Final package of outputs available for download or copy.

## Schema
- export_bundle_id: string
- bundle_name: string
- artifact_ids: list[string]
- includes_resume_revision: boolean
- includes_cover_letter: boolean
- includes_analysis_summary: boolean
- created_at: datetime

## Constraints
- must include at least one artifact
- artifact_ids must refer to existing GeneratedArtifact objects
- export order should be deterministic

## Lifecycle
- assembled at export time
- emitted to DOCX/TXT exporters

## Produced By
- artifact builder
- export service

## Consumed By
- export UI
- download logic

## Guarantees
- provides a coherent set of user-facing outputs

## Disallowed Behavior
- may not reference nonexistent artifacts