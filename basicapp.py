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
        st.session_state.requested_step_id = None
        st.session_state.chat_input = ""
        st.session_state.focus_output_step = None

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
    )

    if st.button("Submit Resume", key="submit_resume"):
        workflow_state = router.start_step(workflow_state, "resume_intake")
        workflow_state = router.complete_step(
            workflow_state,
            "resume_intake",
            payload={"raw_text": st.session_state.resume_text},
            output_ref="resume_001" if st.session_state.resume_text.strip() else None,
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
            "How would the organization interpret this candidate?",
            "What is strong but under-communicated?",
        ],
        "gap_analysis": [
            "What gaps matter most and why?",
            "What should be prioritized first?",
        ],
        "summary_revision": [
            "How should the summary be reframed for this role?",
            "What should the summary signal immediately?",
        ],
        "experience_revision": [
            "Why do the current bullets read as too execution-level?",
            "How should the bullets show broader impact?",
        ],
        "cover_letter_generation": [
            "How should the letter differ from the resume?",
            "What is the strongest opening strategy here?",
        ],
    }

    for prompt in prompts.get(step_id, []):
        if st.button(prompt, key=f"seeded_prompt_{step_id}_{prompt}"):
            st.session_state.chat_input = prompt


def render_chat(step_id: str):
    st.markdown("### Ask / Explore")
    user_input = st.text_input("Ask a question", key="chat_input")

    if user_input:
        st.write("**Response:**")

        if step_id == "match_analysis":
            st.write(
                "At this stage, the strongest interpretation is that the candidate already has relevant substance, "
                "but the current materials do not yet make that substance fully legible in the organization’s preferred language. "
                "What is present is meaningful: program design, stakeholder collaboration, and innovation work all point toward genuine fit. "
                "The issue is not that the candidate lacks relevant experience, but that the current materials communicate that experience in a way "
                "that reads as thoughtful and execution-aware rather than explicitly strategic, organizational, and transformation-oriented. "
                "In practical terms, that means the next step is less about inventing stronger claims and more about reframing valid evidence so it is "
                "recognized as relevant by this audience. The role appears to reward not only competence, but visible alignment with organizational scale, "
                "cross-functional leadership, and transformation language."
            )

        elif step_id == "gap_analysis":
            st.write(
                "The most important thing to understand here is that the leading gaps are interpretive, not merely semantic. "
                "The candidate’s materials appear to contain meaningful evidence of fit, but the way that evidence is currently framed does not consistently "
                "match how the target role describes value. That distinction matters. A weaker candidate would need new evidence; this candidate more likely needs "
                "clearer signaling. The priority gaps therefore matter because they affect how the organization is likely to read the candidate’s relevance. "
                "Language like transformation, organizational impact, and scale should not be treated as decorative keywords. They are cues for how the institution "
                "classifies leadership and fit. The revisions should therefore focus on making real strengths easier to recognize in the role’s own terms."
            )

        elif step_id == "summary_revision":
            st.write(
                "The summary is not just a short introduction; it is the framing device through which the rest of the resume is read. "
                "If it reads as competent but too general, then even strong downstream evidence can be interpreted too narrowly. "
                "In this case, the summary needs to do more than state experience. It needs to signal how that experience should be understood: "
                "as strategic, organizationally relevant, and capable of supporting transformation-oriented work. The revision therefore should foreground "
                "leadership, stakeholder alignment, and innovation in a way that feels grounded rather than inflated. A strong summary here helps the reader "
                "interpret later experience bullets through the right lens from the start."
            )

        elif step_id == "experience_revision":
            st.write(
                "Experience bullets are where abstract fit becomes evidence. Right now, the likely problem is not that the bullets are empty, "
                "but that they may read as task-level, local, or instructional in ways that understate broader organizational relevance. "
                "This is why the revision work needs to focus on framing as much as wording. The goal is to show the reader how to interpret the candidate’s work: "
                "not simply as execution, but as coordination, translation, alignment, adoption, and institutional contribution. "
                "When the bullets are revised well, they do not become exaggerated; instead, they become more legible to the organization’s priorities."
            )

        elif step_id == "skills_revision":
            st.write(
                "The skills section functions as a compressed interpretive signal. A hiring reader may not treat it as the most nuanced part of the document, "
                "but it strongly shapes first impressions of fit. That is why language issues should be resolved here explicitly. If the role repeatedly emphasizes "
                "transformation, organizational impact, cross-functional alignment, or similar concepts, the skills section should reinforce that signal rather than "
                "remain generic. The purpose is not keyword stuffing. The purpose is to ensure that the reader’s quick scan confirms the broader narrative already built "
                "by the summary and experience sections."
            )

        elif step_id == "cover_letter_generation":
            st.write(
                "The cover letter should function as an interpretive bridge between the candidate’s evidence and the organization’s priorities. "
                "It should not merely restate the resume, and it should not try to compensate for weak materials by becoming generic or overly broad. "
                "Instead, it should help the organization understand why the candidate’s experience matters in this context. That means selecting the right dimensions "
                "of the candidate’s background, adopting the role’s language where appropriate, and framing the candidate as someone whose work already points toward the "
                "kind of contribution the organization values. A strong letter clarifies fit; it does not simply assert it."
            )

        else:
            st.write(
                "This step should help the user understand not only what was generated, but why it matters, how it fits into the larger workflow, "
                "and how the generated output should be interpreted in light of the organization’s priorities."
            )


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

    st.markdown("### Revise Resume Summary")
    st.write("Generate a revised professional summary using the alignment and gap analysis.")

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

    render_resume_revision_output(step_id)
    render_seeded_prompts(step_id)
    render_chat(step_id)


def render_experience_revision_step():
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state
    step_id = "experience_revision"

    render_step_context(step_id)
    render_step_output_card(step_id)

    st.markdown("### Revise Experience Bullets")
    st.write(
        "Generate stronger experience bullet language that better matches the target role’s organizational framing."
    )

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

    render_resume_revision_output(step_id)
    render_seeded_prompts(step_id)
    render_chat(step_id)

def render_skills_revision_step():
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state
    step_id = "skills_revision"

    render_step_context(step_id)
    render_step_output_card(step_id)

    st.markdown("### Revise Skills and Compile Resume Redesign")
    st.write(
        "Generate the final resume redesign package, including revised skills language and compiled revised content."
    )

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

    render_resume_revision_output(step_id)
    render_seeded_prompts(step_id)
    render_chat(step_id)

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

def render_cover_letter_generation_step():
    _, _, router = load_workflow_components()
    workflow_state = st.session_state.workflow_state
    step_id = "cover_letter_generation"

    render_step_context(step_id)
    render_step_output_card(step_id)

    st.markdown("### Generate Cover Letter")
    st.write(
        "Generate a targeted cover letter using the prior analysis, revision decisions, and strategy."
    )

    if st.button("Generate Cover Letter", key="run_cover_letter_generation"):
        workflow_state = router.start_step(workflow_state, step_id)
        workflow_state = router.complete_step(
            workflow_state,
            step_id,
            payload={"placeholder": "ok"},
            output_ref="cover_letter_generation_001",
        )
        st.session_state.workflow_state = workflow_state
        st.session_state.cover_letter = build_placeholder_cover_letter()
        sync_session()
        st.rerun()

    render_analysis_summary()
    render_seeded_prompts(step_id)
    render_chat(step_id)

def render_revision_issue_resolution(step_id: str):
    gap = st.session_state.gap_analysis
    if not gap:
        return

    st.markdown("### Issues to Resolve in This Revision")

    if step_id == "summary_revision":
        st.write("**Language issues to resolve here**")
        for item in gap.language_gaps[:3]:
            st.write(f"- {item}")

        st.write("**Framing issues that matter here**")
        for item in gap.framing_gaps[:1]:
            st.write(f"- {item}")

        st.markdown("**Why this matters in the summary**")
        st.write(
            "The summary is the first place the organization forms an impression of scale, leadership, and relevance. "
            "If the summary reads as competent but not explicitly strategic, the rest of the materials can be interpreted "
            "through a narrower lens than the role requires."
        )

    elif step_id == "experience_revision":
        st.write("**Language issues to resolve in experience bullets**")
        for item in gap.language_gaps[:3]:
            st.write(f"- {item}")

        st.write("**Framing issues to resolve in bullets**")
        for item in gap.framing_gaps[:2]:
            st.write(f"- {item}")

        st.markdown("**Why this matters in experience bullets**")
        st.write(
            "Experience bullets are where the candidate’s work is translated into evidence. If they read as task-level "
            "or instructional-only, the organization may miss the broader scope, leadership, and transformation relevance "
            "that the candidate actually brings."
        )

    elif step_id == "skills_revision":
        st.write("**Language that should be more visible in the skills section**")
        for item in gap.language_gaps[:4]:
            st.write(f"- {item}")

        st.markdown("**Why this matters in the skills section**")
        st.write(
            "The skills section acts as a fast interpretive cue. It should reinforce the organizational language already "
            "surfaced in the analysis so the candidate appears legible and aligned at a glance."
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