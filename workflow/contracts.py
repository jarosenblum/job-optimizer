from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import model_validator
from pydantic import BaseModel, Field, field_validator


class WorkflowStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    BLOCKED = "blocked"


class StepStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED_VALIDATION = "failed_validation"


class RuleType(str, Enum):
    REQUIRED_FIELD = "required_field"
    NON_EMPTY = "non_empty"
    MIN_LENGTH = "min_length"
    CONTRACT_PRESENCE = "contract_presence"
    CROSS_STEP_DEPENDENCY = "cross_step_dependency"


class RevisionPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TargetSection(str, Enum):
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    SKILLS = "skills"
    EDUCATION = "education"
    OTHER = "other"


class ArtifactType(str, Enum):
    RESUME_REVISION = "resume_revision"
    COVER_LETTER = "cover_letter"
    ANALYSIS_SUMMARY = "analysis_summary"
    COPY_BLOCK = "copy_block"
    COVER_LETTER_STRATEGY = "cover_letter_strategy"
    ANALYSIS_EXPLANATION = "analysis_explanation"


class SourceType(str, Enum):
    PASTED_TEXT = "pasted_text"
    UPLOADED_FILE = "uploaded_file"
    UPLOADED_TEXT = "uploaded_text"


class UIState(BaseModel):
    show_guidance_panel: bool = True
    show_artifact_panel: bool = True


class ResumeExperienceItem(BaseModel):
    title: Optional[str] = None
    organization: Optional[str] = None
    date_range: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)


class ResumeEducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None


class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None


class UserSession(BaseModel):
    session_id: str
    created_at: datetime
    updated_at: datetime
    active_workflow_id: str
    active_step_id: str
    completed_step_ids: List[str] = Field(default_factory=list)
    ui_state: UIState = Field(default_factory=UIState)


class ValidationResult(BaseModel):
    step_id: str
    is_valid: bool
    passed_rule_ids: List[str] = Field(default_factory=list)
    failed_rule_ids: List[str] = Field(default_factory=list)
    messages: List[str] = Field(default_factory=list)

    @field_validator("is_valid")
    @classmethod
    def validate_consistency(cls, v, info):
        failed = info.data.get("failed_rule_ids", [])
        if v and failed:
            raise ValueError("is_valid cannot be true when failed_rule_ids is not empty.")
        return v


class StepState(BaseModel):
    step_id: str
    status: StepStatus
    is_unlocked: bool
    is_required: bool = True
    input_refs: List[str] = Field(default_factory=list)
    output_refs: List[str] = Field(default_factory=list)
    validation_status: Optional[str] = None
    validation_messages: List[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CandidateAssetSet(BaseModel):
    asset_set_id: str

    resume_text: Optional[str] = None
    job_description_text: Optional[str] = None
    cover_letter_text: Optional[str] = None
    candidate_notes: Optional[str] = None

    # Derived fields (should NOT be user-controlled)
    has_resume: bool = False
    has_job_description: bool = False
    has_cover_letter: bool = False
    is_intake_complete: bool = False

    @model_validator(mode="after")
    def compute_derived_fields(self):
        """
        Enforce contract consistency:
        - has_* fields reflect actual text presence
        - intake completeness is computed, not set manually
        """

        # Normalize text presence
        self.has_resume = bool(self.resume_text and self.resume_text.strip())
        self.has_job_description = bool(self.job_description_text and self.job_description_text.strip())
        self.has_cover_letter = bool(self.cover_letter_text and self.cover_letter_text.strip())

        # Phase 1 rule: resume + job description required
        self.is_intake_complete = self.has_resume and self.has_job_description

        return self


class WorkflowState(BaseModel):
    workflow_id: str
    workflow_name: str
    current_step_id: str
    status: WorkflowStatus
    step_states: List[StepState] = Field(default_factory=list)

    candidate_asset_set_id: Optional[str] = None
    resume_artifact_id: Optional[str] = None
    job_description_artifact_id: Optional[str] = None
    latest_match_analysis_id: Optional[str] = None
    latest_gap_analysis_id: Optional[str] = None
    latest_cover_letter_strategy_id: Optional[str] = None
    latest_resume_revision_artifact_id: Optional[str] = None

    generated_artifact_ids: List[str] = Field(default_factory=list)


class StepDefinition(BaseModel):
    step_id: str
    step_name: str
    step_order: int
    description: Optional[str] = None
    inputs_required: List[str] = Field(default_factory=list)
    outputs_produced: List[str] = Field(default_factory=list)
    validation_rule_ids: List[str] = Field(default_factory=list)
    unlock_condition: str
    is_required: bool = True


class ValidationRule(BaseModel):
    rule_id: str
    rule_name: str
    step_id: str
    rule_type: RuleType
    target_field: Optional[str] = None
    condition: str
    error_message: str


class ResumeArtifact(BaseModel):
    resume_id: str
    raw_text: str
    candidate_name: Optional[str] = None
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = None
    experience: List[ResumeExperienceItem] = Field(default_factory=list)
    education: List[ResumeEducationItem] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    source_type: SourceType


class JobDescriptionArtifact(BaseModel):
    job_description_id: str
    raw_text: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    source_type: SourceType


class MatchAnalysis(BaseModel):
    match_analysis_id: str
    overall_score: float
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    language_overlap: List[str] = Field(default_factory=list)
    language_gaps: List[str] = Field(default_factory=list)
    tone_mismatch_notes: List[str] = Field(default_factory=list)
    rationale: str

    @field_validator("overall_score")
    @classmethod
    def score_range(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("overall_score must be between 0 and 100.")
        return v


class GapAnalysis(BaseModel):
    gap_analysis_id: str
    priority_gaps: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    weak_sections: List[str] = Field(default_factory=list)
    recommended_focus_areas: List[str] = Field(default_factory=list)
    revision_priorities: List[str] = Field(default_factory=list)
    language_gaps: List[str] = Field(default_factory=list)
    framing_gaps: List[str] = Field(default_factory=list)
    rationale: str


class RevisionSuggestion(BaseModel):
    revision_id: str
    target_section: TargetSection
    original_text: Optional[str] = None
    revised_text: str
    reason_for_change: str
    priority: RevisionPriority
    alignment_focus: str = "evidence"


class ResumeRevisionArtifact(BaseModel):
    resume_revision_id: str
    revised_summary: Optional[str] = None
    revised_experience_bullets: List[str] = Field(default_factory=list)
    revised_skills_section: List[str] = Field(default_factory=list)
    section_notes: List[str] = Field(default_factory=list)
    full_revision_text: str


class CoverLetterStrategy(BaseModel):
    strategy_id: str
    target_role_language: List[str] = Field(default_factory=list)
    candidate_strengths_to_foreground: List[str] = Field(default_factory=list)
    priority_gaps_to_address: List[str] = Field(default_factory=list)
    tone_guidance: List[str] = Field(default_factory=list)
    framing_moves: List[str] = Field(default_factory=list)
    key_messages: List[str] = Field(default_factory=list)
    rationale: str


class AnalysisExplanation(BaseModel):
    explanation_id: str
    analysis_type: str
    summary_text: str
    explain_text: str
    expand_text: str


class CoverLetterDraft(BaseModel):
    cover_letter_id: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    opening: str
    body_paragraphs: List[str] = Field(default_factory=list)
    closing: str
    tone: str
    full_text: str


class GeneratedArtifact(BaseModel):
    artifact_id: str
    artifact_type: ArtifactType
    title: str
    content: str
    source_step_id: str
    format_hint: str


class ExportBundle(BaseModel):
    export_bundle_id: str
    bundle_name: str
    artifact_ids: List[str] = Field(default_factory=list)
    includes_resume_revision: bool = False
    includes_cover_letter: bool = False
    includes_analysis_summary: bool = False
    created_at: datetime