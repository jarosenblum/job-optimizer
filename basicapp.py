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
        "Strategic educator and program leader with experience designing AI-enabled initiatives, "
        "aligning stakeholders, and driving innovation across instructional and organizational contexts."
    )

    revised_experience_bullets = [
        "Led cross-stakeholder AI adoption efforts by translating emerging capabilities into practical programs aligned with organizational priorities.",
        "Designed and implemented initiatives that connected innovation strategy to operational execution and long-term program impact.",
    ]

    revised_skills_section = [
        "Strategic program design",
        "Cross-stakeholder alignment",
        "AI adoption and implementation",
        "Organizational communication",
        "Innovation leadership",
    ]

    section_notes = [
        "Summary revised to foreground leadership and organizational scope.",
        "Experience bullets revised to increase strategic and transformation-oriented framing.",
        "Skills revised to better reflect role language and organizational legibility.",
    ]

    full_revision_text = (
        "REVISED SUMMARY\n"
        f"{revised_summary}\n\n"
        "REVISED EXPERIENCE BULLETS\n"
        + "\n".join(f"- {b}" for b in revised_experience_bullets)
        + "\n\nREVISED SKILLS SECTION\n"
        + "\n".join(f"- {s}" for s in revised_skills_section)
    )

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

    if st.button("Submit Resume + Letter Inputs", key="submit_resume"):
        workflow_state = router.start_step(workflow_state, "resume_intake")
        workflow_state = router.complete_step(
            workflow_state,
            "resume_intake",
            payload={
                "resume_raw_text": st.session_state.resume_text,
                "cover_letter_start_text": st.session_state.cover_letter_start_text,
                "cover_letter_working_text": st.session_state.cover_letter_working_text,
            },
            output_ref="resume_001" if has_resume else None,
        )
        st.session_state.workflow_state = workflow_state
        sync_session()
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

    if st.button("Submit Job Description", key="submit_jd"):
        workflow_state = router.start_step(workflow_state, "job_description_intake")
        workflow_state = router.complete_step(
            workflow_state,
            "job_description_intake",
            payload={"raw_text": st.session_state.jd_text},
            output_ref="jd_001" if st.session_state.jd_text.strip() else None,
        )
        st.session_state.workflow_state = workflow_state
        sync_session()
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


def render_section_break(title: str):
    st.markdown("---")
    st.markdown(f"## {title}")


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


def render_chat(step_id: str):
    st.markdown("### Ask / Explore")

    selected_prompt = st.session_state.selected_seed_prompt_by_step.get(step_id)
    if selected_prompt:
        st.caption(f"Selected prompt: {selected_prompt}")

    user_input = st.text_input(
        "Ask a question",
        key=f"chat_input_{step_id}",
    )

    if not user_input:
        return

    response = ""

    if step_id == "match_analysis":
        if "strongest parts" in user_input.lower() or "good" in user_input.lower():
            response = (
                "The strongest parts of the resume appear to be the substantive evidence already present: program design, "
                "cross-stakeholder collaboration, and innovation-oriented work. These are not minor strengths; they suggest that the candidate already has a meaningful basis for fit. "
                "What makes them easy to miss is not weakness in the underlying experience, but the way that experience is currently framed. At the moment, the materials seem to communicate "
                "competence and seriousness more than strategic or transformation-oriented identity. So the good news is that the resume appears to have real material to work with."
            )
        elif "gap" in user_input.lower() or "under-communicated" in user_input.lower():
            response = (
                "What is under-communicated is not merely a keyword layer, but an interpretive layer. The candidate’s work may already map to the role, "
                "but the current materials do not yet make that fit obvious in the language the organization appears to value. In particular, transformation, scale, and organizational leadership "
                "are not yet foregrounded strongly enough. That means the revisions should focus on making real strengths more legible, rather than inventing new strengths."
            )
        else:
            response = (
                "At this stage, the strongest interpretation is that the candidate already has relevant substance, but the current materials do not yet make that substance fully legible "
                "in the organization’s preferred language. The next step is less about inventing stronger claims and more about reframing valid evidence so it is recognized as relevant by this audience."
            )

    elif step_id == "gap_analysis":
        if "good" in user_input.lower():
            response = (
                "The encouraging point in the gap analysis is that the leading issues seem to be representational rather than purely experiential. "
                "That means the candidate may already possess much of the right substance. The problem is that the current framing does not consistently surface that substance in a way that matches the role’s own definitions of value."
            )
        elif "improvement" in user_input.lower() or "gap" in user_input.lower():
            response = (
                "The most important improvements are the ones that change how the organization interprets the candidate. "
                "Language such as transformation, organizational impact, and scale should be treated as meaning-bearing signals, not decorative add-ons. "
                "The candidate likely needs clearer strategic framing, stronger narration of impact, and more explicit alignment with the organization’s priorities."
            )
        else:
            response = (
                "The leading gaps are interpretive, not merely semantic. The candidate’s materials appear to contain meaningful evidence of fit, but the way that evidence is currently framed "
                "does not consistently match how the target role describes value."
            )

    elif step_id == "summary_revision":
        if "good" in user_input.lower():
            response = (
                "What is good about the summary direction is that the revision is beginning to reposition the candidate as a strategic and organizationally relevant actor rather than only a capable practitioner. "
                "That is important because the summary functions as the lens for reading the rest of the resume. When it works well, it prepares the reader to interpret downstream evidence as leadership and organizational contribution."
            )
        elif "improve" in user_input.lower() or "reframed" in user_input.lower():
            response = (
                "What still needs improvement in the summary is the explicit signaling of scale, transformation, and organizational relevance. "
                "The summary should not merely state experience; it should guide the reader toward the correct interpretation of that experience. "
                "That means foregrounding leadership, stakeholder alignment, and broader impact in a way that feels credible and grounded."
            )
        else:
            response = (
                "The summary is not just a short introduction; it is the framing device through which the rest of the resume is read. "
                "A strong summary here helps the reader interpret later experience bullets through the right lens from the start."
            )

    elif step_id == "experience_revision":
        if "good" in user_input.lower():
            response = (
                "The strongest thing about the experience evidence is that it likely already contains meaningful work: coordination, initiative design, adoption support, and practical implementation. "
                "Those are valuable. What is needed is a stronger presentation of those same experiences as evidence of broader leadership, alignment, and organizational contribution."
            )
        elif "under-signal" in user_input.lower() or "improve" in user_input.lower():
            response = (
                "The bullets currently risk under-signaling scope and significance. When experience reads as task-level or purely local, the organization may miss broader relevance. "
                "The revision should therefore emphasize translation, coordination, leadership, adoption, and institutional value, not just execution."
            )
        else:
            response = (
                "Experience bullets are where abstract fit becomes evidence. The revision work here needs to focus on framing as much as wording so the candidate’s work becomes more legible to the organization’s priorities."
            )

    elif step_id == "skills_revision":
        if "align" in user_input.lower() or "good" in user_input.lower():
            response = (
                "Some skills already align well, especially where they suggest program design, collaboration, and practical implementation. "
                "The task now is to make the section more legible in the organization’s own language so those strengths are recognized more quickly."
            )
        elif "missing" in user_input.lower() or "improve" in user_input.lower():
            response = (
                "What is missing is not simply more content, but more targeted framing. If the role emphasizes transformation, organizational impact, or cross-functional alignment, "
                "the skills section should reinforce those ideas directly so the resume’s quick-scan layer matches the deeper narrative."
            )
        else:
            response = (
                "The skills section functions as a compressed interpretive signal. It should confirm the broader story told by the summary and experience sections."
            )

    elif step_id == "cover_letter_generation":
        if "good" in user_input.lower():
            response = (
                "What is promising about the current letter direction is that it already points toward strategic fit and organizational relevance. "
                "That gives you a foundation. The next step is to make that fit feel more specifically grounded in the candidate’s evidence and the organization’s priorities."
            )
        elif "gap" in user_input.lower() or "differ" in user_input.lower() or "improve" in user_input.lower():
            response = (
                "The cover letter should not merely restate the resume. Its main job is interpretive: it should explain why this candidate’s experience matters in this context. "
                "What still needs improvement is the bridge between evidence and organizational need. The letter should foreground the strongest parts of the candidate’s background, "
                "name the most relevant themes in the role, and connect those two with more deliberate framing."
            )
        else:
            response = (
                "The cover letter should function as an interpretive bridge between the candidate’s evidence and the organization’s priorities."
            )

    else:
        response = (
            "This step should help the user understand what is already strong, what gaps remain, and what should be improved now."
        )

    st.session_state.chat_responses_by_step[step_id] = response

    st.write("**Response:**")
    st.write(response)


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

    if st.button("Run Match Analysis", key="run_match_analysis"):
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
        st.rerun()

    render_analysis_summary()
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

    if st.button("Generate Gap Analysis", key="run_gap_analysis"):
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
        st.rerun()

    render_analysis_summary()
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

    render_section_break("Strengths / Gaps / Improve Now")
    render_revision_issue_resolution(step_id)

    if st.button("Generate Summary Revision", key="run_summary_revision"):
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

    render_section_break("Strengths / Gaps / Improve Now")
    render_revision_issue_resolution(step_id)

    if st.button("Generate Experience Revisions", key="run_experience_revision"):
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

    render_section_break("Strengths / Gaps / Improve Now")
    render_revision_issue_resolution(step_id)

    if st.button("Generate Resume Redesign", key="run_skills_revision"):
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

    render_section_break("Strengths / Gaps / Improve Now")
    render_revision_issue_resolution(step_id)

    render_section_break("Cover Letter Generation Workspace")
    st.write(
        "Generate a targeted cover letter using the prior analysis, revision decisions, strategy, and any available cover-letter source materials."
    )

    if st.button("Generate Cover Letter", key="run_cover_letter_generation", disabled=not can_generate_letter):
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
        st.rerun()

    render_analysis_summary()

    render_section_break("Explore This Revision")
    render_seeded_prompts(step_id)
    render_chat(step_id)


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
            height=160,
            key="summary_revision_output",
        )

    elif step_id == "experience_revision":
        st.markdown("**Revised Experience Bullets**")
        bullets_text = "\n".join(f"- {b}" for b in artifact.revised_experience_bullets)
        st.text_area(
            "Experience bullet revisions",
            value=bullets_text,
            height=220,
            key="experience_revision_output",
        )

    elif step_id == "skills_revision":
        st.markdown("**Revised Skills Section**")
        skills_text = "\n".join(f"- {s}" for s in artifact.revised_skills_section)
        st.text_area(
            "Skills revision",
            value=skills_text,
            height=200,
            key="skills_revision_output",
        )

        st.markdown("**Compiled Resume Redesign Notes**")
        for note in artifact.section_notes:
            st.write(f"- {note}")


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
    render_ui_controls()
    maybe_handle_requested_navigation()
    maybe_seed_placeholder_outputs()

    registry, _, _ = load_workflow_components()

    left, center, right = st.columns([1.1, 1.6, 1.3])

    with left:
        render_step_nav(st.session_state.workflow_state, registry)

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