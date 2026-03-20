from __future__ import annotations

from pathlib import Path

import streamlit as st

from ui.artifact_panel import render_artifact_panel
from ui.guidance_panel import render_guidance_panel
from ui.step_nav import render_step_nav
from workflow.contracts import (
    AnalysisExplanation,
    ArtifactType,
    CoverLetterDraft,
    CoverLetterStrategy,
    GapAnalysis,
    GeneratedArtifact,
    MatchAnalysis,
    ResumeRevisionArtifact,
    RevisionPriority,
    RevisionSuggestion,
)
from workflow.session_manager import SessionManager
from workflow.step_registry import StepRegistry
from workflow.validators import ValidationRuleSet, ValidatorEngine


BASE = Path(__file__).resolve().parent
STEP_REGISTRY_PATH = BASE / "step_registry.json"
VALIDATION_RULES_PATH = BASE / "validation_rules.json"

DEFAULT_VERBOSITY_MODE = "standard"
VERBOSITY_OPTIONS = ["concise", "standard", "deep"]


@st.cache_resource
def load_workflow_components():
    registry = StepRegistry.from_json(STEP_REGISTRY_PATH)
    rule_set = ValidationRuleSet.from_json(VALIDATION_RULES_PATH)
    validator = ValidatorEngine(rule_set)
    from workflow.router import WorkflowRouter

    router = WorkflowRouter(registry, validator)
    return registry, validator, router


def ensure_state():
    _, _, router = load_workflow_components()

    if "workflow_state" not in st.session_state:
        workflow_state = router.initialize_workflow(
            workflow_id="streamlit_phase1",
            workflow_name="Guided Job Optimization MVP",
        )
        st.session_state.workflow_state = workflow_state
        st.session_state.user_session = SessionManager.create_session(
            active_workflow_id=workflow_state.workflow_id,
            active_step_id=workflow_state.current_step_id,
        )

        st.session_state.resume_text = ""
        st.session_state.jd_text = ""
        st.session_state.cover_letter_start_text = ""
        st.session_state.cover_letter_working_text = ""
        st.session_state.requested_step_id = None
        st.session_state.focus_output_step = None
        st.session_state.chat_responses_by_step = {}
        st.session_state.selected_seed_prompt_by_step = {}
        st.session_state.chat_history_by_step = {}

        st.session_state.match_analysis = None
        st.session_state.gap_analysis = None
        st.session_state.revisions = []
        st.session_state.cover_letter = None
        st.session_state.cover_letter_strategy = None
        st.session_state.generated_artifacts = []
        st.session_state.analysis_explanations = {}
        st.session_state.resume_revision_artifact = None


def ensure_ui_preferences():
    if "verbosity_mode" not in st.session_state:
        st.session_state.verbosity_mode = DEFAULT_VERBOSITY_MODE


def render_ui_controls():
    st.sidebar.subheader("Display")
    st.session_state.verbosity_mode = st.sidebar.selectbox(
        "Analysis depth",
        VERBOSITY_OPTIONS,
        index=VERBOSITY_OPTIONS.index(st.session_state.verbosity_mode),
        help="Controls how much analysis text is shown by default.",
    )


def sync_session():
    st.session_state.user_session = SessionManager.sync_session_with_workflow(
        st.session_state.user_session,
        st.session_state.workflow_state,
    )


def maybe_handle_requested_navigation():
    requested_step_id = st.session_state.get("requested_step_id")
    if not requested_step_id:
        return

    _, _, router = load_workflow_components()
    st.session_state.workflow_state = router.go_to_step(
        st.session_state.workflow_state,
        requested_step_id,
    )
    st.session_state.requested_step_id = None
    sync_session()


def build_placeholder_match_analysis() -> MatchAnalysis:
    return MatchAnalysis(
        match_analysis_id="match_001",
        overall_score=72.0,
        matched_skills=["project leadership", "stakeholder communication", "program design"],
        missing_skills=["cross-functional scaling", "change management language"],
        matched_keywords=["strategy", "outcomes", "collaboration"],
        missing_keywords=["transformation", "operational excellence", "scalable systems"],
        strengths=[
            "Candidate materials show strong program and instructional design experience.",
            "Evidence of cross-stakeholder work is present.",
        ],
        weaknesses=[
            "Role emphasizes transformation language more explicitly than the current materials do.",
        ],
        language_overlap=["strategy", "collaboration", "outcomes"],
        language_gaps=["transformation", "enterprise scale", "operational excellence"],
        tone_mismatch_notes=[
            "Current materials read as thoughtful and evidence-driven, but less explicitly executive/transformational.",
        ],
        rationale=(
            "Candidate and role align on substance, but candidate materials underuse some "
            "organizational framing and language."
        ),
    )


def build_placeholder_gap_analysis() -> GapAnalysis:
    return GapAnalysis(
        gap_analysis_id="gap_001",
        priority_gaps=[
            "Increase explicit transformation/change language.",
            "Frame prior work in broader organizational terms.",
        ],
        missing_evidence=[
            "Broader scale framing is not consistently foregrounded.",
        ],
        weak_sections=["summary", "experience"],
        recommended_focus_areas=[
            "Leadership framing",
            "Enterprise/program-level impact",
        ],
        revision_priorities=[
            "Revise summary for role-aligned language.",
            "Rewrite top experience bullets to surface transformation and scale.",
        ],
        language_gaps=["transformation", "operational excellence", "scalable systems"],
        framing_gaps=[
            "Resume often frames work as instructional execution rather than organizational leadership.",
        ],
        rationale=(
            "Core evidence is present, but framing and language do not yet fully match "
            "the target organization context."
        ),
    )


def build_placeholder_resume_revision_artifact() -> ResumeRevisionArtifact:
    revised_summary = (
        "Strategic educator and program leader with experience designing AI-enabled initiatives, aligning stakeholders, "
        "and translating innovation into practical implementation across instructional and organizational contexts."
    )

    revised_experience_bullets = [
        "Led cross-stakeholder AI adoption efforts by translating emerging capabilities into practical programs aligned with organizational priorities.",
        "Designed and implemented initiatives that connected innovation strategy to operational execution and long-term program impact.",
        "Developed guidance, workshops, and structured resources that increased organizational legibility and supported broader adoption of new capabilities.",
        "Bridged communication across technical, instructional, and leadership-facing audiences to move projects from concept to execution.",
        "Contributed to program and documentation systems that improved consistency, clarity, and scalability of implementation work.",
    ]

    revised_skills_section = [
        "Strategic program design",
        "Cross-stakeholder alignment",
        "AI adoption and implementation",
        "Organizational communication",
        "Innovation leadership",
        "Documentation and systems thinking",
        "Change-oriented initiative support",
    ]

    section_notes = [
        "Summary revised to foreground leadership and organizational scope.",
        "Experience bullets revised to increase strategic and transformation-oriented framing.",
        "Skills revised to better reflect role language and organizational legibility.",
    ]

    full_revision_text = f"""
REVISED PROFESSIONAL SUMMARY
{revised_summary}

REVISED EXPERIENCE
- {revised_experience_bullets[0]}
- {revised_experience_bullets[1]}
- {revised_experience_bullets[2]}
- {revised_experience_bullets[3]}
- {revised_experience_bullets[4]}

REVISED SKILLS
- {revised_skills_section[0]}
- {revised_skills_section[1]}
- {revised_skills_section[2]}
- {revised_skills_section[3]}
- {revised_skills_section[4]}
- {revised_skills_section[5]}
- {revised_skills_section[6]}
""".strip()

    return ResumeRevisionArtifact(
        resume_revision_id="rra_001",
        revised_summary=revised_summary,
        revised_experience_bullets=revised_experience_bullets,
        revised_skills_section=revised_skills_section,
        section_notes=section_notes,
        full_revision_text=full_revision_text,
    )


def build_placeholder_revisions() -> list[RevisionSuggestion]:
    return [
        RevisionSuggestion(
            revision_id="rev_001",
            target_section="summary",
            original_text="Experienced educator and program builder with strong interest in AI and innovation.",
            revised_text=(
                "Strategic educator and program leader with experience designing AI-enabled "
                "initiatives, aligning stakeholders, and driving innovation across instructional "
                "and organizational contexts."
            ),
            reason_for_change=(
                "Shifts the summary toward leadership, strategic alignment, and "
                "organization-facing language used in the target role."
            ),
            priority=RevisionPriority.HIGH,
            alignment_focus="language",
        ),
        RevisionSuggestion(
            revision_id="rev_002",
            target_section="experience",
            original_text="Designed workshops and supported faculty AI adoption.",
            revised_text=(
                "Led cross-stakeholder AI adoption efforts by designing faculty-facing "
                "initiatives, translating emerging capabilities into practical programs, "
                "and aligning implementation with institutional priorities."
            ),
            reason_for_change="Adds organizational framing and stronger transformation-oriented language.",
            priority=RevisionPriority.HIGH,
            alignment_focus="framing",
        ),
    ]


def build_placeholder_cover_letter_strategy() -> CoverLetterStrategy:
    return CoverLetterStrategy(
        strategy_id="cls_001",
        target_role_language=[
            "transformation",
            "cross-functional leadership",
            "organizational impact",
        ],
        candidate_strengths_to_foreground=[
            "program design",
            "stakeholder alignment",
            "AI-enabled initiative leadership",
        ],
        priority_gaps_to_address=[
            "Increase transformation-oriented language",
            "Frame experience at broader organizational scale",
        ],
        tone_guidance=[
            "Sound strategic rather than purely tactical",
            "Use confident but grounded language",
        ],
        framing_moves=[
            "Connect candidate experience to organizational priorities",
            "Translate program work into broader leadership impact",
        ],
        key_messages=[
            "Candidate has relevant strategic and implementation experience",
            "Candidate can bridge innovation, adoption, and execution",
        ],
        rationale=(
            "The letter should foreground candidate strengths using language closer to the target "
            "organization’s framing, while addressing the current gap in transformation and scale-oriented language."
        ),
    )


def build_placeholder_cover_letter() -> CoverLetterDraft:
    full_text = (
        "Dear Hiring Team,\n\n"
        "I am excited to submit my application for this role. My background combines program design, "
        "stakeholder collaboration, and AI-enabled innovation work that aligns strongly with your mission.\n\n"
        "Across my work, I have translated emerging capabilities into practical initiatives, supported adoption, "
        "and connected strategy to implementation. I am particularly drawn to your emphasis on transformation, "
        "cross-functional alignment, and sustained organizational impact.\n\n"
        "I would welcome the opportunity to contribute that combination of evidence, language alignment, and "
        "program leadership to your team.\n\n"
        "Sincerely,\nCandidate Name"
    )
    return CoverLetterDraft(
        cover_letter_id="cl_001",
        job_title="Target Role",
        company_name="Target Organization",
        opening="Dear Hiring Team,",
        body_paragraphs=[
            "I am excited to submit my application for this role.",
            "My background combines program design, stakeholder collaboration, and AI-enabled innovation work.",
        ],
        closing="Sincerely,\nCandidate Name",
        tone="professional",
        full_text=full_text,
    )


def build_placeholder_generated_artifacts() -> list[GeneratedArtifact]:
    return [
        GeneratedArtifact(
            artifact_id="artifact_001",
            artifact_type=ArtifactType.ANALYSIS_SUMMARY,
            title="Alignment Summary",
            content=(
                "Overall match is promising, but the candidate materials underuse transformation-oriented "
                "language and broader organizational framing."
            ),
            source_step_id="match_analysis",
            format_hint="markdown",
        )
    ]


def build_placeholder_analysis_explanations() -> dict[str, AnalysisExplanation]:
    return {
        "match_analysis": AnalysisExplanation(
            explanation_id="exp_match_001",
            analysis_type="match_analysis",
            summary_text=(
                "The candidate is substantively aligned with the role, but the materials understate "
                "transformation and organizational-scale framing."
            ),
            explain_text=(
                "The resume and role align on program design, stakeholder work, and innovation, "
                "but the role language emphasizes transformation and cross-functional scale more explicitly."
            ),
            expand_text=(
                "The issue is not just missing keywords. The materials communicate competence, but often in "
                "a way that reads as execution-aware rather than explicitly strategic and organizational. "
                "The revision process should therefore reframe valid evidence, not just swap vocabulary."
            ),
        ),
        "gap_analysis": AnalysisExplanation(
            explanation_id="exp_gap_001",
            analysis_type="gap_analysis",
            summary_text=(
                "The main gaps are in language emphasis, organizational framing, and narration of impact."
            ),
            explain_text=(
                "The strongest opportunities are to revise the summary and top experience bullets so they "
                "communicate broader strategic scope and more explicit organizational impact."
            ),
            expand_text=(
                "This is primarily a representational gap rather than a raw experience gap. The candidate’s "
                "experience appears relevant, but the current materials do not consistently frame it in the "
                "same rhetorical and organizational terms used by the role."
            ),
        ),
        "cover_letter_strategy": AnalysisExplanation(
            explanation_id="exp_cls_001",
            analysis_type="cover_letter_strategy",
            summary_text=(
                "The cover letter should foreground strategic fit, organizational relevance, and "
                "transformation-oriented framing."
            ),
            explain_text=(
                "The letter should select candidate evidence that demonstrates leadership, alignment, and "
                "innovation, while using language closer to the role’s priorities."
            ),
            expand_text=(
                "A strong letter should act as an interpretive bridge between candidate evidence and "
                "organizational need, emphasizing why the candidate’s experience matters in this context "
                "and using language that is more legible to the organization."
            ),
        ),
    }


def build_deep_analysis_memo(step_id: str) -> dict:
    if step_id == "summary_revision":
        return {
            "executive_summary": (
                "The summary is doing more than introducing the candidate; it is defining how the rest of the resume will be interpreted. "
                "At present, the candidate appears to have relevant substance, but the summary does not yet fully direct the reader to interpret that substance as strategic, organization-facing, and transformation-capable."
            ),
            "what_is_strong": (
                "What is already promising is that the candidate seems to have real substance to foreground: initiative-building, collaboration across stakeholders, and work that connects ideas to implementation. "
                "Those are not minor traits. They are often the raw material from which a stronger leadership narrative can be built."
            ),
            "how_the_role_reads_this": (
                "A hiring reader in this role is likely to look for immediate signals of scope, relevance, and fit. "
                "If the summary sounds thoughtful but generic, the rest of the resume may be interpreted too narrowly—even if the experience itself is stronger than that reading suggests."
            ),
            "what_is_under_signaled": (
                "The summary currently under-signals transformation, organizational scale, and explicit contribution to broader institutional or business goals. "
                "The problem is not necessarily lack of evidence; it is that the framing does not yet help the reader classify the candidate in the right category."
            ),
            "revision_strategy": (
                "The revision should move beyond a descriptive summary of experience and become an interpretive summary of value. "
                "It should name leadership, alignment, innovation, and organization-level contribution in a way that still feels grounded in the candidate’s actual record."
            ),
            "context": (
                "This matters because summaries are often read first and remembered disproportionately. "
                "They shape the lens through which later bullets are processed. A stronger summary can therefore improve the perceived strength of the whole resume without changing the underlying facts."
            ),
            "example_reframe": (
                "For example, a weaker summary might say the candidate has experience in program development and AI innovation. "
                "A stronger summary would reinterpret that same evidence as leadership in designing AI-enabled initiatives, aligning stakeholders, and translating innovation into organizationally relevant action."
            ),
            "reader_takeaway": (
                "The goal is for the reader to finish the summary already primed to see the candidate as strategically relevant, not merely competent."
            ),
        }

    if step_id == "experience_revision":
        return {
            "executive_summary": (
                "The experience section is where claimed fit becomes believable. Right now, the likely issue is not absence of meaningful work, but that the existing bullets may read too locally or too operationally."
            ),
            "what_is_strong": (
                "The candidate appears to have experience that can support a stronger case: initiative design, coordination, implementation support, and practical delivery. "
                "These can all become persuasive if framed as evidence of broader value rather than isolated tasks."
            ),
            "how_the_role_reads_this": (
                "A reader will often scan bullets for signals of scale, leadership, and organizational contribution. "
                "If the bullets focus only on what was done, rather than why it mattered, the organization may miss the broader relevance."
            ),
            "what_is_under_signaled": (
                "Under-signaled elements include scope, translation across groups, leadership in moving work forward, and visible connection between activity and impact."
            ),
            "revision_strategy": (
                "The revision should shift bullets from task-reporting toward evidence-framing. "
                "That means emphasizing coordination, influence, design decisions, adoption, outcomes, and organizational relevance."
            ),
            "context": (
                "This is especially important because many candidates have good experience that reads as smaller than it really is. "
                "The difference often comes down to whether the bullet presents work as activity or as contribution."
            ),
            "example_reframe": (
                "For example, instead of saying the candidate designed workshops and supported adoption, a stronger bullet would show that they led or coordinated adoption efforts, translated emerging tools into practical use, and aligned implementation with institutional priorities."
            ),
            "reader_takeaway": (
                "The reader should come away feeling that the candidate has already done work that resembles the kind of contribution this role needs."
            ),
        }

    if step_id == "skills_revision":
        return {
            "executive_summary": (
                "The skills section is a compressed interpretive signal. It will not carry the whole application, but it strongly shapes first impressions."
            ),
            "what_is_strong": (
                "The candidate likely already has several relevant skills at the substance level, especially around design, collaboration, implementation, and innovation."
            ),
            "how_the_role_reads_this": (
                "A hiring reader may use the skills section as a fast proxy for alignment. "
                "If the language is too generic, the candidate may appear weaker in fit than they actually are."
            ),
            "what_is_under_signaled": (
                "Role-relevant language such as transformation, cross-functional alignment, organizational communication, and strategic implementation may still be muted."
            ),
            "revision_strategy": (
                "The skills section should be revised to reinforce the same narrative built elsewhere. "
                "It should not feel like a disconnected keyword bank; it should confirm the leadership and impact framing already established in the summary and experience sections."
            ),
            "context": (
                "This matters because recruiters and hiring managers often scan this section quickly. "
                "That makes it one of the highest-leverage places to improve legibility without overstating anything."
            ),
            "example_reframe": (
                "For example, instead of generic labels like communication or program support, stronger phrasing might foreground organizational communication, stakeholder alignment, strategic program design, or AI adoption and implementation."
            ),
            "reader_takeaway": (
                "The reader should be able to skim the skills section and see language that feels native to the role."
            ),
        }

    if step_id == "cover_letter_generation":
        return {
            "executive_summary": (
                "The cover letter should not merely repeat the resume. Its job is to interpret the candidate for this specific organizational context."
            ),
            "what_is_strong": (
                "The candidate appears to have substance that can support a strong letter, especially where experience suggests initiative-building, translation of innovation into action, and collaboration across groups."
            ),
            "how_the_role_reads_this": (
                "The organization will likely read the letter less as a catalogue of facts and more as a framing statement: why this candidate, why this role, why now."
            ),
            "what_is_under_signaled": (
                "The current application may still under-connect candidate evidence to organizational need. "
                "That bridge is exactly what the letter must strengthen."
            ),
            "revision_strategy": (
                "The letter should foreground the strongest candidate themes, name the most relevant priorities of the role, and explicitly connect the two. "
                "It should sound interpretive, not repetitive."
            ),
            "context": (
                "A strong letter adds value when it helps the organization understand how to read the resume. "
                "It becomes weak when it simply restates accomplishments without contextualizing them."
            ),
            "example_reframe": (
                "For example, rather than repeating that the candidate worked on AI-related initiatives, the letter should explain that the candidate has experience translating emerging capabilities into usable programs and aligning innovation with organizational priorities."
            ),
            "reader_takeaway": (
                "The reader should finish the letter understanding not just what the candidate has done, but why that experience matters in this exact setting."
            ),
        }

    return {
        "executive_summary": "This step should clarify what is strong, what is weak, and what the next artifact should accomplish.",
        "what_is_strong": "Relevant substance appears present.",
        "how_the_role_reads_this": "Interpretation depends on framing.",
        "what_is_under_signaled": "Some signals are not yet fully legible.",
        "revision_strategy": "Revise toward stronger alignment.",
        "context": "The point is to guide how the reader classifies the candidate.",
        "example_reframe": "A stronger version should reinterpret real evidence rather than invent new evidence.",
        "reader_takeaway": "The next artifact should make the candidate easier to read as relevant.",
    }


def build_final_review_memo() -> dict:
    return {
        "application_read": (
            "The application now reads as substantially more aligned, especially where the resume and letter have been revised to foreground strategic and organizationally relevant language."
        ),
        "strongest_differentiators": [
            "Evidence of program design and initiative-building",
            "Cross-stakeholder collaboration",
            "Ability to connect innovation to practical implementation",
        ],
        "remaining_risks": [
            "Some language may still under-signal scale",
            "Certain bullets may still read more execution-level than transformation-level",
        ],
        "final_edit_priorities": [
            "Tighten top resume bullets for strongest organizational framing",
            "Ensure letter opening explicitly names role-relevant fit",
            "Confirm the strongest evidence appears early in both resume and letter",
        ],
        "submission_readiness": (
            "The materials appear much stronger than the original state, but a final pass should still focus on clarity, framing consistency, and emphasis."
        ),
    }


def build_export_bundle_text() -> str:
    artifact = st.session_state.resume_revision_artifact
    cover_letter = st.session_state.cover_letter
    final_review = build_final_review_memo()

    parts: list[str] = []

    if artifact:
        parts.append("FULL REVISED SUMMARY")
        parts.append(artifact.revised_summary or "")
        parts.append("")

        parts.append("REVISED EXPERIENCE BULLETS")
        parts.extend(f"- {b}" for b in artifact.revised_experience_bullets)
        parts.append("")

        parts.append("REVISED SKILLS SECTION")
        parts.extend(f"- {s}" for s in artifact.revised_skills_section)
        parts.append("")

    if cover_letter:
        parts.append("COVER LETTER DRAFT")
        parts.append(cover_letter.full_text)
        parts.append("")

    parts.append("FINAL REVIEW MEMO")
    parts.append(final_review["application_read"])
    parts.append("")
    parts.append("FINAL EDIT PRIORITIES")
    parts.extend(f"- {item}" for item in final_review["final_edit_priorities"])

    return "\n".join(parts)


def maybe_seed_placeholder_outputs():
    workflow_state = st.session_state.workflow_state
    completed_ids = {s.step_id for s in workflow_state.step_states if s.status.value == "complete"}

    if "job_description_intake" in completed_ids and st.session_state.match_analysis is None:
        st.session_state.match_analysis = build_placeholder_match_analysis()

    if "match_analysis" in completed_ids and st.session_state.gap_analysis is None:
        st.session_state.gap_analysis = build_placeholder_gap_analysis()

    if "gap_analysis" in completed_ids and not st.session_state.revisions:
        st.session_state.revisions = build_placeholder_revisions()

    if "skills_revision" in completed_ids and st.session_state.cover_letter_strategy is None:
        st.session_state.cover_letter_strategy = build_placeholder_cover_letter_strategy()

    if "cover_letter_generation" in completed_ids and st.session_state.cover_letter is None:
        st.session_state.cover_letter = build_placeholder_cover_letter()

    if "final_review" in completed_ids and not st.session_state.generated_artifacts:
        st.session_state.generated_artifacts = build_placeholder_generated_artifacts()

    if "match_analysis" in completed_ids and not st.session_state.analysis_explanations:
        st.session_state.analysis_explanations = build_placeholder_analysis_explanations()

    if "summary_revision" in completed_ids and st.session_state.resume_revision_artifact is None:
        st.session_state.resume_revision_artifact = build_placeholder_resume_revision_artifact()


def render_section_break(title: str):
    st.markdown("---")
    st.markdown(f"## {title}")


def get_step_index(step_id: str) -> tuple[int, int]:
    step_ids = [s.step_id for s in st.session_state.workflow_state.step_states]
    if step_id not in step_ids:
        return 1, max(1, len(step_ids))
    return step_ids.index(step_id) + 1, len(step_ids)


def get_next_step_id(step_id: str) -> str | None:
    step_ids = [s.step_id for s in st.session_state.workflow_state.step_states]
    if step_id not in step_ids:
        return None
    idx = step_ids.index(step_id)
    return step_ids[idx + 1] if idx + 1 < len(step_ids) else None


def get_previous_step_id(step_id: str) -> str | None:
    step_ids = [s.step_id for s in st.session_state.workflow_state.step_states]
    if step_id not in step_ids:
        return None
    idx = step_ids.index(step_id)
    return step_ids[idx - 1] if idx - 1 >= 0 else None


def render_step_action_bar(
    step_id: str,
    primary_label: str | None = None,
    primary_key: str | None = None,
    primary_disabled: bool = False,
) -> bool:
    step_num, total_steps = get_step_index(step_id)
    prev_step_id = get_previous_step_id(step_id)
    next_step_id = get_next_step_id(step_id)

    st.markdown("### What to do next")
    st.progress(step_num / total_steps)
    st.caption(f"Step {step_num} of {total_steps}")

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button(
            "⬅ Back",
            key=f"back_nav_{step_id}",
            disabled=prev_step_id is None,
            use_container_width=True,
        ):
            st.session_state.requested_step_id = prev_step_id
            st.rerun()

    with col2:
        if st.button(
            "Open next ➡",
            key=f"next_nav_{step_id}",
            disabled=next_step_id is None,
            use_container_width=True,
        ):
            st.session_state.requested_step_id = next_step_id
            st.rerun()

    with col3:
        if primary_label:
            return st.button(
                primary_label,
                key=primary_key or f"primary_action_{step_id}",
                disabled=primary_disabled,
                use_container_width=True,
            )

    return False


def get_step_output_summary(step_id: str) -> dict:
    summary = {
        "has_output": False,
        "output_type": "No output yet",
        "summary_lines": [],
    }

    if step_id == "match_analysis" and st.session_state.match_analysis:
        match = st.session_state.match_analysis
        summary["has_output"] = True
        summary["output_type"] = "Match Analysis"
        summary["summary_lines"] = [
            f"Match score: {match.overall_score:.1f}",
            f"Shared language items: {len(match.language_overlap)}",
            f"Language gaps identified: {len(match.language_gaps)}",
        ]

    elif step_id == "gap_analysis" and st.session_state.gap_analysis:
        gap = st.session_state.gap_analysis
        summary["has_output"] = True
        summary["output_type"] = "Gap Analysis"
        summary["summary_lines"] = [
            f"Priority gaps: {len(gap.priority_gaps)}",
            f"Language gaps: {len(gap.language_gaps)}",
            f"Framing gaps: {len(gap.framing_gaps)}",
        ]

    elif step_id == "summary_revision" and st.session_state.revisions:
        summary["has_output"] = True
        summary["output_type"] = "Resume Summary Revision"
        summary["summary_lines"] = [
            "Revised summary generated",
            f"Revision objects available: {len(st.session_state.revisions)}",
        ]

    elif step_id == "experience_revision" and st.session_state.revisions:
        summary["has_output"] = True
        summary["output_type"] = "Experience Revisions"
        summary["summary_lines"] = [
            "Revised experience language available",
            f"Revision objects available: {len(st.session_state.revisions)}",
        ]

    elif step_id == "skills_revision" and st.session_state.resume_revision_artifact:
        summary["has_output"] = True
        summary["output_type"] = "Compiled Resume Redesign"
        summary["summary_lines"] = [
            "Revised summary available",
            "Revised experience bullets available",
            "Revised skills section available",
        ]

    elif step_id == "cover_letter_generation" and st.session_state.cover_letter:
        summary["has_output"] = True
        summary["output_type"] = "Cover Letter Draft"
        summary["summary_lines"] = [
            "Targeted cover letter generated",
            "Ready for review in artifacts panel",
        ]

    elif step_id == "final_review" and st.session_state.generated_artifacts:
        summary["has_output"] = True
        summary["output_type"] = "Generated Artifacts"
        summary["summary_lines"] = [
            f"Artifacts available: {len(st.session_state.generated_artifacts)}",
            "Ready for final review",
        ]

    elif step_id == "export_bundle":
        completed = {
            s.step_id for s in st.session_state.workflow_state.step_states if s.status.value == "complete"
        }
        if "final_review" in completed:
            summary["has_output"] = True
            summary["output_type"] = "Export Bundle Ready"
            summary["summary_lines"] = [
                "Workflow outputs assembled for export step",
            ]

    return summary


def render_step_context(step_id: str):
    step_state = next(s for s in st.session_state.workflow_state.step_states if s.step_id == step_id)
    output_summary = get_step_output_summary(step_id)

    st.markdown(f"## {step_id.replace('_', ' ').title()}")
    st.write(f"**Status:** {step_state.status.value.replace('_', ' ').title()}")

    if output_summary["has_output"]:
        st.success(f"Output generated: {output_summary['output_type']}")
    else:
        st.info("No output generated yet.")


def render_step_output_card(step_id: str):
    output_summary = get_step_output_summary(step_id)

    st.markdown("### Latest Output from this Step")
    st.write(f"**Type:** {output_summary['output_type']}")

    if output_summary["has_output"]:
        st.success("Generated")
        for line in output_summary["summary_lines"]:
            st.write(f"- {line}")

        if st.button("Open latest output", key=f"open_output_{step_id}"):
            st.session_state.focus_output_step = step_id
    else:
        st.info("No output generated yet for this step.")


def render_analysis_summary():
    match_analysis = st.session_state.match_analysis
    gap_analysis = st.session_state.gap_analysis
    explanations = st.session_state.analysis_explanations
    mode = st.session_state.get("verbosity_mode", DEFAULT_VERBOSITY_MODE)

    if match_analysis:
        st.markdown("### Baseline alignment")
        st.metric("Match score", f"{match_analysis.overall_score:.1f}")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Shared language**")
            for item in match_analysis.language_overlap:
                st.write(f"- {item}")

        with col2:
            st.write("**Missing / underused language**")
            for item in match_analysis.language_gaps:
                st.write(f"- {item}")

        if match_analysis.tone_mismatch_notes:
            st.write("**Tone mismatch notes**")
            for item in match_analysis.tone_mismatch_notes:
                st.write(f"- {item}")

        explanation = explanations.get("match_analysis")
        if explanation:
            st.markdown("### Match analysis explanation")
            st.write(explanation.summary_text)

            if mode in {"standard", "deep"}:
                st.markdown("**Explanation**")
                st.write(explanation.explain_text)
            else:
                with st.expander("Explain", expanded=False):
                    st.write(explanation.explain_text)

            if mode == "deep":
                st.markdown("**Expanded analysis**")
                st.write(explanation.expand_text)
            else:
                with st.expander("Expand", expanded=False):
                    st.write(explanation.expand_text)

    if gap_analysis:
        st.markdown("### Revision focus")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Language gaps**")
            for item in gap_analysis.language_gaps:
                st.write(f"- {item}")

        with col2:
            st.write("**Framing gaps**")
            for item in gap_analysis.framing_gaps:
                st.write(f"- {item}")

        explanation = explanations.get("gap_analysis")
        if explanation:
            st.markdown("### Gap analysis explanation")
            st.write(explanation.summary_text)

            if mode in {"standard", "deep"}:
                st.markdown("**Explanation**")
                st.write(explanation.explain_text)
            else:
                with st.expander("Explain", expanded=False):
                    st.write(explanation.explain_text)

            if mode == "deep":
                st.markdown("**Expanded analysis**")
                st.write(explanation.expand_text)
            else:
                with st.expander("Expand", expanded=False):
                    st.write(explanation.expand_text)

    if st.session_state.cover_letter_strategy:
        explanation = explanations.get("cover_letter_strategy")
        if explanation:
            st.markdown("### Cover letter strategy explanation")
            st.write(explanation.summary_text)

            if mode in {"standard", "deep"}:
                st.markdown("**Explanation**")
                st.write(explanation.explain_text)
            else:
                with st.expander("Explain", expanded=False):
                    st.write(explanation.explain_text)

            if mode == "deep":
                st.markdown("**Expanded analysis**")
                st.write(explanation.expand_text)
            else:
                with st.expander("Expand", expanded=False):
                    st.write(explanation.expand_text)


def render_deep_analysis_memo(step_id: str):
    mode = st.session_state.get("verbosity_mode", DEFAULT_VERBOSITY_MODE)
    if mode != "deep":
        return

    memo = build_deep_analysis_memo(step_id)

    render_section_break("Deep Analysis Memo")
    st.markdown("### Executive Summary")
    st.write(memo["executive_summary"])

    st.markdown("### What Is Strong")
    st.write(memo["what_is_strong"])

    st.markdown("### How the Organization Is Likely to Read This")
    st.write(memo["how_the_role_reads_this"])

    st.markdown("### What Is Under-Signaled or Misframed")
    st.write(memo["what_is_under_signaled"])

    st.markdown("### Revision Strategy")
    st.write(memo["revision_strategy"])

    st.markdown("### Context")
    st.write(memo["context"])

    st.markdown("### Example Reframe")
    st.write(memo["example_reframe"])

    st.markdown("### Reader Takeaway")
    st.write(memo["reader_takeaway"])


def build_chat_response(step_id: str, user_input: str) -> str:
    q = user_input.strip().lower()

    if step_id == "gap_analysis":
        if "main gaps" in q:
            return (
                "The main gaps are not simply missing words; they are gaps in how the candidate’s value is being represented. "
                "First, the materials underuse language associated with transformation and scale. Second, the framing does not always help "
                "the reader see broader organizational contribution. Third, some evidence that may actually be relevant is still presented in "
                "a way that feels narrower than the role likely expects. In other words, the issue is less that the candidate lacks substance "
                "and more that the current materials do not yet help the organization recognize that substance clearly.\n\n"
                "For example, a line about designing workshops may sound helpful but local. Reframed properly, that same work might signal "
                "leadership in capability-building, alignment across stakeholder groups, and movement from innovation to implementation."
            )
        elif "improvement first" in q or "needs improvement first" in q:
            return (
                "The first improvement should be the one that changes overall interpretation most quickly: the summary. "
                "That is because the summary sets the lens for everything that follows. After that, the top experience bullets should be revised "
                "so they reinforce the same strategic framing. Only then should the skills section be tightened to confirm the language of fit.\n\n"
                "A useful way to think about the order is: framing first, evidence second, reinforcement third."
            )
        elif "framing issues" in q:
            return (
                "A framing issue is different from an evidence issue. An evidence issue would mean the candidate has not done the relevant work. "
                "A framing issue means the relevant work may already be present, but it is not being presented in a way that the organization will classify correctly.\n\n"
                "For example, work that demonstrates coordination, translation, and institutional contribution might still be described as task execution unless the bullet is rewritten "
                "to highlight scope, leadership, and value."
            )
        elif "example" in q:
            return (
                "Here is the kind of contrast that matters. A thin version might say: 'Supported faculty AI adoption.' "
                "A stronger version would say: 'Led cross-stakeholder AI adoption efforts by translating emerging capabilities into practical programs aligned with organizational priorities.'\n\n"
                "Both refer to related underlying work, but only the second one helps the reader classify the candidate as strategically relevant."
            )
        return (
            "The leading gaps are interpretive, not merely semantic. The candidate’s materials appear to contain meaningful evidence of fit, "
            "but the way that evidence is currently framed does not consistently match how the target role describes value.\n\n"
            "That means the revision process should prioritize stronger signaling, stronger narrative framing, and clearer connections between experience and organizational need."
        )

    if step_id == "summary_revision":
        if "already good" in q:
            return (
                "What is already good about the summary direction is that it begins moving the candidate out of a narrow practitioner frame and into a broader strategic frame. "
                "That matters because the role likely expects the candidate to look organization-aware, not merely competent.\n\n"
                "The revised direction is therefore stronger because it starts foregrounding leadership, stakeholder alignment, and innovation in a more role-legible way."
            )
        elif "still needs improvement" in q:
            return (
                "What still needs improvement in the summary is explicit signaling of scale, transformation, and organizational contribution. "
                "Right now, the revised direction is better, but it could still go further in helping the reader understand not just what the candidate has done, but why that work "
                "should count as strategically relevant in this setting.\n\n"
                "A stronger summary should make the reader think: this person has already operated in ways that matter to our priorities."
            )
        elif "reframed" in q:
            return (
                "The summary should be reframed as a statement of value, not merely a statement of background. "
                "That means leading with the kind of contribution the candidate brings—strategic design, stakeholder alignment, innovation translated into action—rather than only naming domains of experience.\n\n"
                "For example, instead of reading as 'experienced educator with AI interests,' it should read more like 'strategic program leader who has designed AI-enabled initiatives, "
                "aligned stakeholders, and connected innovation to implementation.'"
            )
        elif "example" in q:
            return (
                "A weaker summary might say the candidate has experience in education, technology, and innovation. "
                "A stronger version would say the candidate has led or designed initiatives that connect innovation to organizational goals, align stakeholders, and create scalable program impact.\n\n"
                "The difference is not exaggeration. It is interpretive clarity."
            )
        return (
            "The summary is not just a short introduction; it is the framing device through which the rest of the resume is read. "
            "A strong summary helps the reader interpret later bullets through the right lens from the start.\n\n"
            "In practice, that means the summary should do early narrative work: define the candidate as strategically relevant before the reader gets into the details."
        )

    if step_id == "match_analysis":
        if "strongest parts" in q:
            return (
                "The strongest parts of the resume appear to be the evidence of meaningful work already present: program design, collaboration across stakeholders, and innovation-oriented implementation. "
                "Those are strong because they suggest real fit potential. The problem is not that these elements are absent, but that they are not yet being interpreted at the highest-value level the role seems to reward.\n\n"
                "For a typical hiring reader, this means the resume has substance, but some of its best evidence is currently under-leveraged."
            )
        elif "under-communicated" in q:
            return (
                "What is under-communicated is the organizational meaning of the candidate’s experience. "
                "The current materials may show thoughtful and relevant work, but they do not yet foreground scale, transformation, or broader institutional relevance strongly enough.\n\n"
                "That means the application risks being read as capable but narrower than it should be."
            )
        elif "interpret" in q:
            return (
                "The organization would likely interpret the candidate as credible and relevant in substance, but not yet optimally framed. "
                "The reader may see someone with real experience, but may not immediately classify that experience as strategic, transformation-oriented, or broad enough in scope unless the framing is strengthened.\n\n"
                "This is exactly the kind of situation where good revision can change the reading without changing the underlying facts."
            )
        elif "example" in q:
            return (
                "For example, if a bullet says the candidate designed workshops and supported adoption, a reader may interpret that as useful but local. "
                "If the same evidence is reframed as leading adoption efforts, translating emerging capabilities into practical programs, and aligning implementation with organizational priorities, "
                "the reader is far more likely to see strategic fit."
            )
        return (
            "At this stage, the strongest interpretation is that the candidate already has relevant substance, but the current materials do not yet make that substance fully legible in the organization’s preferred language.\n\n"
            "The next step is less about inventing stronger claims and more about reframing valid evidence so it is recognized as relevant by this audience."
        )

    if step_id == "experience_revision":
        if "good" in q:
            return (
                "What is already good about the experience evidence is that it likely contains meaningful work: coordination, initiative design, adoption support, and practical implementation. "
                "Those are useful signals because they can be reframed as broader contribution.\n\n"
                "The key is to make sure the bullets show not only activity, but scope, influence, and why the work mattered."
            )
        elif "under-signal" in q or "improve" in q:
            return (
                "The bullets currently risk under-signaling scope and significance. When experience reads as task-level or purely local, the organization may miss broader relevance.\n\n"
                "The revision should therefore emphasize translation, coordination, leadership, adoption, and institutional value, not just execution. "
                "For example, a bullet should show what changed, who was aligned, or what larger objective the work served."
            )
        elif "example" in q:
            return (
                "A thin bullet might say: 'Created documentation and workshops for AI adoption.' "
                "A stronger bullet might say: 'Developed guidance and adoption resources that aligned faculty-facing implementation with broader organizational priorities and improved consistency across rollout efforts.'\n\n"
                "The second version gives the reader a reason to treat the work as strategically relevant."
            )
        return (
            "Experience bullets are where abstract fit becomes evidence. The revision work here needs to focus on framing as much as wording so the candidate’s work becomes more legible to the organization’s priorities."
        )

    if step_id == "skills_revision":
        if "align" in q or "good" in q:
            return (
                "Some skills already align well, especially where they suggest program design, collaboration, practical implementation, and innovation support. "
                "Those provide a strong foundation because they can be translated into the organization’s own language.\n\n"
                "The goal is not to replace the real skills. It is to relabel them so the fit becomes easier to see."
            )
        elif "missing" in q or "improve" in q:
            return (
                "What is missing is not simply more content, but more targeted framing. If the role emphasizes transformation, organizational impact, or cross-functional alignment, "
                "the skills section should reinforce those ideas directly so the resume’s quick-scan layer matches the deeper narrative.\n\n"
                "For example, 'communication' is weaker than 'organizational communication' if the latter better reflects the kind of value the role expects."
            )
        elif "example" in q:
            return (
                "A generic skills list might include items like communication, program support, and technical fluency. "
                "A more role-legible version would foreground strategic program design, stakeholder alignment, AI adoption and implementation, and organizational communication.\n\n"
                "The difference is subtle, but it changes the way the reader classifies the candidate."
            )
        return (
            "The skills section functions as a compressed interpretive signal. It should confirm the broader story told by the summary and experience sections."
        )

    if step_id == "cover_letter_generation":
        if "good" in q:
            return (
                "What is promising about the current letter direction is that it already points toward strategic fit and organizational relevance. "
                "That gives you a foundation. The next step is to make that fit feel more specifically grounded in the candidate’s evidence and the organization’s priorities."
            )
        elif "gap" in q or "differ" in q or "improve" in q:
            return (
                "The cover letter should not merely restate the resume. Its main job is interpretive: it should explain why this candidate’s experience matters in this context. "
                "What still needs improvement is the bridge between evidence and organizational need.\n\n"
                "The letter should foreground the strongest parts of the candidate’s background, name the most relevant themes in the role, and connect those two with more deliberate framing."
            )
        elif "example" in q:
            return (
                "For example, instead of simply saying the candidate has worked on AI initiatives, the letter should explain that the candidate has experience translating emerging capabilities into practical programs, "
                "aligning stakeholders, and connecting innovation to implementation in ways that matter to organizational goals."
            )
        return (
            "The cover letter should function as an interpretive bridge between the candidate’s evidence and the organization’s priorities."
        )

    return (
        "This area should explain what is already strong, what is currently weak or under-signaled, and how the next revision should change the reader’s interpretation.\n\n"
        "The eventual goal is not just to answer questions, but to walk the user through why the revision matters and what a stronger version would look like in practice."
    )


def render_seeded_prompts(step_id: str):
    st.markdown("### Explore")

    prompts = {
        "match_analysis": [
            "What are the strongest parts of this resume?",
            "What is strong but under-communicated?",
            "How would the organization interpret this candidate?",
        ],
        "gap_analysis": [
            "What are the main gaps?",
            "What needs improvement first?",
            "Which issues are framing issues rather than evidence issues?",
        ],
        "summary_revision": [
            "What is already good about the summary direction?",
            "What still needs improvement in the summary?",
            "How should the summary be reframed for this role?",
        ],
        "experience_revision": [
            "What is already good about the experience evidence?",
            "What do the bullets currently under-signal?",
            "How should the bullets show broader impact?",
        ],
        "skills_revision": [
            "What skills already align well?",
            "What language is missing from the skills section?",
            "What should be improved in the skills framing?",
        ],
        "cover_letter_generation": [
            "What is good about the current letter direction?",
            "What gaps remain in the letter?",
            "How should the letter differ from the resume?",
        ],
    }

    for prompt in prompts.get(step_id, []):
        if st.button(prompt, key=f"seeded_prompt_{step_id}_{prompt}"):
            st.session_state.selected_seed_prompt_by_step[step_id] = prompt
            st.session_state[f"chat_input_{step_id}"] = prompt


def append_chat_turn(step_id: str, role: str, content: str):
    history = st.session_state.chat_history_by_step.setdefault(step_id, [])
    history.append({"role": role, "content": content})


def render_chat_history(step_id: str):
    history = st.session_state.chat_history_by_step.get(step_id, [])
    if not history:
        return

    st.markdown("### Conversation")
    for msg in history:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Assistant:** {msg['content']}")


def render_chat(step_id: str):
    st.markdown("### Ask / Explore")

    selected_prompt = st.session_state.selected_seed_prompt_by_step.get(step_id)
    if selected_prompt:
        st.caption(f"Selected prompt: {selected_prompt}")

    render_chat_history(step_id)

    with st.form(key=f"chat_form_{step_id}", clear_on_submit=False):
        user_input = st.text_input(
            "Ask a question",
            key=f"chat_input_{step_id}",
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Send")
        with col2:
            cleared = st.form_submit_button("Clear chat")

    if cleared:
        st.session_state.chat_history_by_step[step_id] = []
        st.session_state[f"chat_input_{step_id}"] = ""
        st.rerun()

    if submitted and user_input.strip():
        append_chat_turn(step_id, "user", user_input.strip())
        response = build_chat_response(step_id, user_input.strip())
        append_chat_turn(step_id, "assistant", response)
        st.session_state.chat_responses_by_step[step_id] = response
        st.session_state[f"chat_input_{step_id}"] = ""
        st.rerun()


def render_revision_issue_resolution(step_id: str):
    match = st.session_state.match_analysis
    gap = st.session_state.gap_analysis

    if not match and not gap:
        return

    st.markdown("### Strengths")
    if match:
        strengths = match.strengths[:2] if match.strengths else []
        if strengths:
            for item in strengths:
                st.write(f"- {item}")
        else:
            st.write("- Relevant substance appears present, but may not yet be fully signaled.")
    else:
        st.write("- Core candidate evidence appears present.")

    st.markdown("### Gaps")
    if gap:
        if step_id == "summary_revision":
            for item in gap.language_gaps[:3]:
                st.write(f"- Underused language in summary: {item}")
            for item in gap.framing_gaps[:1]:
                st.write(f"- Framing gap in summary: {item}")

        elif step_id == "experience_revision":
            for item in gap.language_gaps[:3]:
                st.write(f"- Experience language gap: {item}")
            for item in gap.framing_gaps[:2]:
                st.write(f"- Experience framing gap: {item}")

        elif step_id == "skills_revision":
            for item in gap.language_gaps[:4]:
                st.write(f"- Skills language gap: {item}")

        elif step_id == "cover_letter_generation":
            for item in gap.language_gaps[:3]:
                st.write(f"- Letter should better reflect: {item}")
            for item in gap.framing_gaps[:1]:
                st.write(f"- Letter framing issue: {item}")
    else:
        st.write("- No structured gap analysis available yet.")

    st.markdown("### Improve Now")
    if step_id == "summary_revision":
        st.write(
            "Revise the summary so it immediately signals leadership, organizational relevance, and transformation-oriented scope."
        )
    elif step_id == "experience_revision":
        st.write(
            "Rewrite the bullets so they read as broader evidence of coordination, impact, and organizational contribution rather than only task execution."
        )
    elif step_id == "skills_revision":
        st.write(
            "Re-label and surface skills using the role’s own language so the candidate appears more legible at a glance."
        )
    elif step_id == "cover_letter_generation":
        st.write(
            "Use the letter to interpret the candidate’s evidence for this organization, not simply repeat the resume."
        )


def render_resume_revision_output(step_id: str):
    artifact = st.session_state.resume_revision_artifact
    if not artifact:
        return

    st.markdown("### Revised Output")

    if step_id == "summary_revision":
        st.markdown("**Revised Summary**")
        st.text_area(
            "Summary revision",
            value=artifact.revised_summary or "",
            height=180,
            key="summary_revision_output",
        )

    elif step_id == "experience_revision":
        st.markdown("**Revised Experience Bullets**")
        bullets_text = "\n".join(f"- {b}" for b in artifact.revised_experience_bullets)
        st.text_area(
            "Experience bullet revisions",
            value=bullets_text,
            height=260,
            key="experience_revision_output",
        )

    elif step_id == "skills_revision":
        st.markdown("**Compiled Resume Redesign**")
        st.text_area(
            "Compiled full resume redesign",
            value=artifact.full_revision_text,
            height=420,
            key="skills_revision_full_output",
        )

        st.markdown("**Compiled Resume Redesign Notes**")
        for note in artifact.section_notes:
            st.write(f"- {note}")


def render_resume_intake():
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state

    st.markdown("### Resume Intake")
    st.write("Paste the candidate resume text. This becomes the base candidate context for downstream analysis.")

    st.session_state.resume_text = st.text_area(
        "Resume text",
        st.session_state.resume_text,
        height=220,
        key="resume_intake_text_area",
    )

    render_section_break("Cover Letter Intake")
    st.write(
        "Provide the starting and working cover-letter materials. "
        "These are optional for the current scaffold, but should be collected now so later cover-letter revision is grounded in real artifacts."
    )

    st.session_state.cover_letter_start_text = st.text_area(
        "Starting cover letter / original source letter",
        st.session_state.cover_letter_start_text,
        height=180,
        key="cover_letter_start_text_area",
    )

    st.session_state.cover_letter_working_text = st.text_area(
        "Working cover letter / current draft",
        st.session_state.cover_letter_working_text,
        height=180,
        key="cover_letter_working_text_area",
    )

    st.markdown("### Intake status")
    has_resume = bool(st.session_state.resume_text.strip())
    has_cover_start = bool(st.session_state.cover_letter_start_text.strip())
    has_cover_working = bool(st.session_state.cover_letter_working_text.strip())

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Resume", "Present" if has_resume else "Missing")
    with col2:
        st.metric("Starting letter", "Present" if has_cover_start else "Optional")
    with col3:
        st.metric("Working letter", "Present" if has_cover_working else "Optional")

    submit_resume = render_step_action_bar(
        "resume_intake",
        primary_label="Save Intake and Continue",
        primary_key="submit_resume_top",
        primary_disabled=not has_resume,
    )

    if submit_resume:
        workflow_state = router.start_step(workflow_state, "resume_intake")
        workflow_state = router.complete_step(
            workflow_state,
            "resume_intake",
            payload={
                "raw_text": st.session_state.resume_text,
                "resume_raw_text": st.session_state.resume_text,
                "cover_letter_start_text": st.session_state.cover_letter_start_text,
                "cover_letter_working_text": st.session_state.cover_letter_working_text,
            },
            output_ref="resume_001" if has_resume else None,
        )
        st.session_state.workflow_state = workflow_state
        sync_session()
        next_step = get_next_step_id("resume_intake")
        if next_step:
            st.session_state.requested_step_id = next_step
        st.rerun()


def render_job_description_intake():
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state

    st.markdown("### Job Description Intake")
    st.write("Paste the target role and organization text. This becomes the organizational context.")
    st.session_state.jd_text = st.text_area(
        "Job description text",
        st.session_state.jd_text,
        height=220,
        key="jd_text_area",
    )

    submit_jd = render_step_action_bar(
        "job_description_intake",
        primary_label="Save Job Description and Continue",
        primary_key="submit_jd_top",
        primary_disabled=not bool(st.session_state.jd_text.strip()),
    )

    if submit_jd:
        workflow_state = router.start_step(workflow_state, "job_description_intake")
        workflow_state = router.complete_step(
            workflow_state,
            "job_description_intake",
            payload={"raw_text": st.session_state.jd_text},
            output_ref="jd_001" if st.session_state.jd_text.strip() else None,
        )
        st.session_state.workflow_state = workflow_state
        sync_session()
        next_step = get_next_step_id("job_description_intake")
        if next_step:
            st.session_state.requested_step_id = next_step
        st.rerun()


def render_generic_step_stub(step_id: str):
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state

    st.markdown(f"### {step_id.replace('_', ' ').title()}")
    st.write(
        "This step is now part of the guided UX shell. It can be completed with placeholder "
        "behavior while engines are added."
    )

    if st.button(f"Mark {step_id} complete", key=f"complete_{step_id}"):
        workflow_state = router.start_step(workflow_state, step_id)
        workflow_state = router.complete_step(
            workflow_state,
            step_id,
            payload={"placeholder": "ok"},
            output_ref=f"{step_id}_output_001",
        )
        st.session_state.workflow_state = workflow_state
        sync_session()
        st.rerun()


def render_match_analysis_step():
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state
    step_id = "match_analysis"

    render_step_context(step_id)
    render_step_output_card(step_id)

    st.markdown("### Analyze Resume Against Role")
    st.write(
        "Generate a baseline analysis of how the candidate resume aligns with the target role, "
        "including language overlap, missing language, and tone/framing differences."
    )

    run_match = render_step_action_bar(
        step_id,
        primary_label="Run Match Analysis and Continue",
        primary_key="run_match_analysis_top",
    )

    if run_match:
        workflow_state = router.start_step(workflow_state, step_id)
        workflow_state = router.complete_step(
            workflow_state,
            step_id,
            payload={"placeholder": "ok"},
            output_ref="match_analysis_001",
        )
        st.session_state.workflow_state = workflow_state
        st.session_state.match_analysis = build_placeholder_match_analysis()
        st.session_state.analysis_explanations = build_placeholder_analysis_explanations()
        sync_session()
        next_step = get_next_step_id(step_id)
        if next_step:
            st.session_state.requested_step_id = next_step
        st.rerun()

    render_analysis_summary()
    render_deep_analysis_memo(step_id)
    render_seeded_prompts(step_id)
    render_chat(step_id)


def render_gap_analysis_step():
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state
    step_id = "gap_analysis"

    render_step_context(step_id)
    render_step_output_card(step_id)

    st.markdown("### Identify Gaps and Revision Priorities")
    st.write(
        "Translate the baseline alignment analysis into concrete revision priorities, "
        "including evidence gaps, language gaps, and framing gaps."
    )

    run_gap = render_step_action_bar(
        step_id,
        primary_label="Generate Gap Analysis and Continue",
        primary_key="run_gap_analysis_top",
    )

    if run_gap:
        workflow_state = router.start_step(workflow_state, step_id)
        workflow_state = router.complete_step(
            workflow_state,
            step_id,
            payload={"placeholder": "ok"},
            output_ref="gap_analysis_001",
        )
        st.session_state.workflow_state = workflow_state
        st.session_state.gap_analysis = build_placeholder_gap_analysis()
        sync_session()
        next_step = get_next_step_id(step_id)
        if next_step:
            st.session_state.requested_step_id = next_step
        st.rerun()

    render_analysis_summary()
    render_deep_analysis_memo(step_id)
    render_seeded_prompts(step_id)
    render_chat(step_id)


def render_summary_revision_step():
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state
    step_id = "summary_revision"

    render_step_context(step_id)
    render_step_output_card(step_id)

    render_section_break("Summary Revision Workspace")
    st.write("Generate a revised professional summary using the alignment and gap analysis.")

    run_summary = render_step_action_bar(
        step_id,
        primary_label="Generate Summary Revision and Continue",
        primary_key="run_summary_revision_top",
    )

    render_section_break("Strengths / Gaps / Improve Now")
    render_revision_issue_resolution(step_id)
    render_deep_analysis_memo(step_id)

    if run_summary:
        workflow_state = router.start_step(workflow_state, step_id)
        workflow_state = router.complete_step(
            workflow_state,
            step_id,
            payload={"placeholder": "ok"},
            output_ref="summary_revision_001",
        )
        st.session_state.workflow_state = workflow_state
        st.session_state.revisions = build_placeholder_revisions()
        st.session_state.resume_revision_artifact = build_placeholder_resume_revision_artifact()
        sync_session()
        next_step = get_next_step_id(step_id)
        if next_step:
            st.session_state.requested_step_id = next_step
        st.rerun()

    render_section_break("Revised Output")
    render_resume_revision_output(step_id)

    render_section_break("Explore This Revision")
    render_seeded_prompts(step_id)
    render_chat(step_id)


def render_experience_revision_step():
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state
    step_id = "experience_revision"

    render_step_context(step_id)
    render_step_output_card(step_id)

    render_section_break("Experience Revision Workspace")
    st.write(
        "Generate stronger experience bullet language that better matches the target role’s organizational framing."
    )

    run_experience = render_step_action_bar(
        step_id,
        primary_label="Generate Experience Revisions and Continue",
        primary_key="run_experience_revision_top",
    )

    render_section_break("Strengths / Gaps / Improve Now")
    render_revision_issue_resolution(step_id)
    render_deep_analysis_memo(step_id)

    if run_experience:
        workflow_state = router.start_step(workflow_state, step_id)
        workflow_state = router.complete_step(
            workflow_state,
            step_id,
            payload={"placeholder": "ok"},
            output_ref="experience_revision_001",
        )
        st.session_state.workflow_state = workflow_state
        st.session_state.resume_revision_artifact = build_placeholder_resume_revision_artifact()
        sync_session()
        next_step = get_next_step_id(step_id)
        if next_step:
            st.session_state.requested_step_id = next_step
        st.rerun()

    render_section_break("Revised Output")
    render_resume_revision_output(step_id)

    render_section_break("Explore This Revision")
    render_seeded_prompts(step_id)
    render_chat(step_id)


def render_skills_revision_step():
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state
    step_id = "skills_revision"

    render_step_context(step_id)
    render_step_output_card(step_id)

    render_section_break("Skills Revision Workspace")
    st.write(
        "Generate the final resume redesign package, including revised skills language and compiled revised content."
    )

    run_skills = render_step_action_bar(
        step_id,
        primary_label="Generate Resume Redesign and Continue",
        primary_key="run_skills_revision_top",
    )

    render_section_break("Strengths / Gaps / Improve Now")
    render_revision_issue_resolution(step_id)
    render_deep_analysis_memo(step_id)

    if run_skills:
        workflow_state = router.start_step(workflow_state, step_id)
        workflow_state = router.complete_step(
            workflow_state,
            step_id,
            payload={"placeholder": "ok"},
            output_ref="skills_revision_001",
        )
        st.session_state.workflow_state = workflow_state
        st.session_state.resume_revision_artifact = build_placeholder_resume_revision_artifact()
        st.session_state.cover_letter_strategy = build_placeholder_cover_letter_strategy()
        sync_session()
        next_step = get_next_step_id(step_id)
        if next_step:
            st.session_state.requested_step_id = next_step
        st.rerun()

    render_section_break("Revised Output")
    render_resume_revision_output(step_id)

    render_section_break("Explore This Revision")
    render_seeded_prompts(step_id)
    render_chat(step_id)


def render_cover_letter_generation_step():
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state
    step_id = "cover_letter_generation"

    render_step_context(step_id)
    render_step_output_card(step_id)

    render_section_break("Cover Letter Inputs Available")
    start_present = bool(st.session_state.cover_letter_start_text.strip())
    working_present = bool(st.session_state.cover_letter_working_text.strip())

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Starting letter", "Present" if start_present else "Missing")
    with col2:
        st.metric("Working letter", "Present" if working_present else "Missing")

    can_generate_letter = start_present or working_present

    if not can_generate_letter:
        st.info("Provide a starting or working cover letter above to generate a grounded letter revision.")

    run_letter = render_step_action_bar(
        step_id,
        primary_label="Generate Cover Letter and Continue",
        primary_key="run_cover_letter_generation_top",
        primary_disabled=not can_generate_letter,
    )

    render_section_break("Strengths / Gaps / Improve Now")
    render_revision_issue_resolution(step_id)
    render_deep_analysis_memo(step_id)

    render_section_break("Cover Letter Generation Workspace")
    st.write(
        "Generate a targeted cover letter using the prior analysis, revision decisions, strategy, and any available cover-letter source materials."
    )

    if run_letter:
        workflow_state = router.start_step(workflow_state, step_id)
        workflow_state = router.complete_step(
            workflow_state,
            step_id,
            payload={
                "cover_letter_start_text": st.session_state.cover_letter_start_text,
                "cover_letter_working_text": st.session_state.cover_letter_working_text,
            },
            output_ref="cover_letter_generation_001",
        )
        st.session_state.workflow_state = workflow_state
        st.session_state.cover_letter = build_placeholder_cover_letter()
        sync_session()
        next_step = get_next_step_id(step_id)
        if next_step:
            st.session_state.requested_step_id = next_step
        st.rerun()

    render_analysis_summary()

    render_section_break("Explore This Revision")
    render_seeded_prompts(step_id)
    render_chat(step_id)


def render_final_review_step():
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state
    step_id = "final_review"

    render_step_context(step_id)
    render_step_output_card(step_id)

    render_section_break("Final Review")
    st.write("Generate a final integrative review of the revised application materials.")

    run_final_review = render_step_action_bar(
        step_id,
        primary_label="Generate Final Review and Continue",
        primary_key="run_final_review_top",
    )

    if run_final_review:
        workflow_state = router.start_step(workflow_state, step_id)
        workflow_state = router.complete_step(
            workflow_state,
            step_id,
            payload={"placeholder": "ok"},
            output_ref="final_review_001",
        )
        st.session_state.workflow_state = workflow_state
        sync_session()
        next_step = get_next_step_id(step_id)
        if next_step:
            st.session_state.requested_step_id = next_step
        st.rerun()

    render_deep_analysis_memo(step_id)

    memo = build_final_review_memo()
    st.markdown("### How the Application Now Reads")
    st.write(memo["application_read"])

    st.markdown("### Strongest Differentiators")
    for item in memo["strongest_differentiators"]:
        st.write(f"- {item}")

    st.markdown("### Remaining Risks")
    for item in memo["remaining_risks"]:
        st.write(f"- {item}")

    st.markdown("### Final Edit Priorities")
    for item in memo["final_edit_priorities"]:
        st.write(f"- {item}")

    st.markdown("### Submission Readiness")
    st.write(memo["submission_readiness"])


def render_export_bundle_step():
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state
    step_id = "export_bundle"

    render_step_context(step_id)
    render_step_output_card(step_id)

    render_section_break("Export Bundle")
    st.write("Assemble copy-ready outputs for resume revision, cover letter, and final review.")

    run_export = render_step_action_bar(
        step_id,
        primary_label="Assemble Export Bundle",
        primary_key="run_export_bundle_top",
    )

    if run_export:
        workflow_state = router.start_step(workflow_state, step_id)
        workflow_state = router.complete_step(
            workflow_state,
            step_id,
            payload={"placeholder": "ok"},
            output_ref="export_bundle_001",
        )
        st.session_state.workflow_state = workflow_state
        sync_session()
        st.rerun()

    export_text = build_export_bundle_text()
    st.text_area(
        "Copy-ready export bundle",
        value=export_text,
        height=420,
        key="export_bundle_text",
    )


def render_current_step():
    current_step_id = st.session_state.workflow_state.current_step_id

    if current_step_id == "resume_intake":
        render_step_context(current_step_id)
        render_step_output_card(current_step_id)
        render_resume_intake()

    elif current_step_id == "job_description_intake":
        render_step_context(current_step_id)
        render_step_output_card(current_step_id)
        render_job_description_intake()

    elif current_step_id == "match_analysis":
        render_match_analysis_step()

    elif current_step_id == "gap_analysis":
        render_gap_analysis_step()

    elif current_step_id == "summary_revision":
        render_summary_revision_step()

    elif current_step_id == "experience_revision":
        render_experience_revision_step()

    elif current_step_id == "skills_revision":
        render_skills_revision_step()

    elif current_step_id == "cover_letter_generation":
        render_cover_letter_generation_step()

    elif current_step_id == "final_review":
        render_final_review_step()

    elif current_step_id == "export_bundle":
        render_export_bundle_step()

    else:
        render_step_context(current_step_id)
        render_step_output_card(current_step_id)
        render_analysis_summary()
        render_generic_step_stub(current_step_id)


def render_focused_output():
    focus_step = st.session_state.get("focus_output_step")
    if not focus_step:
        return

    st.markdown("---")
    st.subheader("Focused Output")

    if focus_step in {"summary_revision", "experience_revision", "skills_revision"} and st.session_state.resume_revision_artifact:
        artifact = st.session_state.resume_revision_artifact
        st.info(f"Showing latest resume-related output from `{focus_step}`.")

        st.write("**Revised Summary**")
        st.write(artifact.revised_summary)

        st.write("**Revised Experience Bullets**")
        for bullet in artifact.revised_experience_bullets:
            st.write(f"- {bullet}")

        st.write("**Revised Skills Section**")
        for skill in artifact.revised_skills_section:
            st.write(f"- {skill}")

    elif focus_step == "match_analysis" and st.session_state.match_analysis:
        match = st.session_state.match_analysis
        st.info("Showing latest match analysis output.")
        st.write(f"**Match score:** {match.overall_score:.1f}")
        st.write("**Language gaps:**")
        for item in match.language_gaps:
            st.write(f"- {item}")

    elif focus_step == "gap_analysis" and st.session_state.gap_analysis:
        gap = st.session_state.gap_analysis
        st.info("Showing latest gap analysis output.")
        st.write("**Priority gaps:**")
        for item in gap.priority_gaps:
            st.write(f"- {item}")

    elif focus_step == "cover_letter_generation" and st.session_state.cover_letter:
        st.info("Showing latest cover letter output.")
        st.text_area(
            "Latest cover letter",
            value=st.session_state.cover_letter.full_text,
            height=240,
            key="focused_cover_letter",
        )

    elif focus_step == "final_review" and st.session_state.generated_artifacts:
        st.info("Showing latest final-review artifacts.")
        for artifact in st.session_state.generated_artifacts:
            st.write(f"**{artifact.title}**")
            st.write(artifact.content)

    if st.button("Clear focus", key="clear_focus_output"):
        st.session_state.focus_output_step = None
        st.rerun()


def main():
    st.set_page_config(page_title="Guided Job Optimization MVP", layout="wide")
    st.title("Guided Job Optimization MVP")

    ensure_state()
    ensure_ui_preferences()
    maybe_handle_requested_navigation()
    maybe_seed_placeholder_outputs()

    registry, _, _ = load_workflow_components()

    with st.sidebar:
        st.subheader("Workflow")
        render_step_nav(st.session_state.workflow_state, registry)
        st.markdown("---")
        render_ui_controls()

    center, right = st.columns([1.8, 1.2])

    with center:
        render_current_step()

    with right:
        render_guidance_panel(
            st.session_state.workflow_state,
            registry,
            match_analysis=st.session_state.match_analysis,
            gap_analysis=st.session_state.gap_analysis,
            latest_revision=st.session_state.revisions[0] if st.session_state.revisions else None,
        )

        render_focused_output()
        st.markdown("---")

        if st.session_state.resume_revision_artifact:
            st.markdown("---")
            st.subheader("Resume Redesign Artifact")

            artifact = st.session_state.resume_revision_artifact

            st.markdown("**Revised Summary**")
            st.text_area(
                "Resume summary artifact",
                value=artifact.revised_summary or "",
                height=120,
                key="resume_summary_artifact",
            )

            st.markdown("**Revised Experience Bullets**")
            bullets_text = "\n".join(f"- {b}" for b in artifact.revised_experience_bullets)
            st.text_area(
                "Resume experience artifact",
                value=bullets_text,
                height=180,
                key="resume_experience_artifact",
            )

            st.markdown("**Revised Skills Section**")
            skills_text = "\n".join(f"- {s}" for s in artifact.revised_skills_section)
            st.text_area(
                "Resume skills artifact",
                value=skills_text,
                height=160,
                key="resume_skills_artifact",
            )

        render_artifact_panel(
            revisions=st.session_state.revisions,
            cover_letter=st.session_state.cover_letter,
            generated_artifacts=st.session_state.generated_artifacts,
        )


if __name__ == "__main__":
    main()