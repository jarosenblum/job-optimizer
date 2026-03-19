from __future__ import annotations

from typing import Optional

import streamlit as st

from workflow.contracts import GapAnalysis, MatchAnalysis, RevisionSuggestion, WorkflowState
from workflow.step_registry import StepRegistry


def render_guidance_panel(
    workflow_state: WorkflowState,
    registry: StepRegistry,
    *,
    match_analysis: Optional[MatchAnalysis] = None,
    gap_analysis: Optional[GapAnalysis] = None,
    latest_revision: Optional[RevisionSuggestion] = None,
) -> None:
    st.subheader("Guidance")

    current_step = registry.require_step(workflow_state.current_step_id)
    current_state = next(s for s in workflow_state.step_states if s.step_id == current_step.step_id)

    st.markdown(f"**Current step:** {current_step.step_name}")
    if current_step.description:
        st.write(current_step.description)

    if current_state.validation_messages:
        for msg in current_state.validation_messages:
            st.error(msg)
    else:
        st.info("Complete this step to unlock the next stage.")

    st.markdown("### What happened")
    if match_analysis:
        st.write(f"**Alignment score:** {match_analysis.overall_score:.1f}/100")

        if match_analysis.strengths:
            st.write("**Strengths**")
            for item in match_analysis.strengths[:3]:
                st.write(f"- {item}")

        if match_analysis.language_overlap:
            st.write("**Shared language with the role**")
            for item in match_analysis.language_overlap[:5]:
                st.write(f"- {item}")

        if match_analysis.language_gaps:
            st.write("**Language the role uses that is underrepresented**")
            for item in match_analysis.language_gaps[:5]:
                st.write(f"- {item}")

        if match_analysis.tone_mismatch_notes:
            st.write("**Tone / framing notes**")
            for item in match_analysis.tone_mismatch_notes[:3]:
                st.write(f"- {item}")

    elif gap_analysis:
        st.write("Gap analysis is available for this run.")

    else:
        st.write("No analysis output yet. Start with the intake steps.")

    st.markdown("### What to do next")
    if gap_analysis:
        if gap_analysis.revision_priorities:
            for item in gap_analysis.revision_priorities[:4]:
                st.write(f"- {item}")

        if gap_analysis.language_gaps:
            st.write("**Language gaps to address**")
            for item in gap_analysis.language_gaps[:4]:
                st.write(f"- {item}")

        if gap_analysis.framing_gaps:
            st.write("**Framing gaps to address**")
            for item in gap_analysis.framing_gaps[:4]:
                st.write(f"- {item}")
    else:
        st.write("- Complete intake and baseline analysis.")
        st.write("- Review where candidate evidence and role language diverge.")
        st.write("- Use revisions to tighten alignment before generating the letter.")

    if latest_revision:
        st.markdown("### Latest revision note")
        st.write(f"**Focus:** {latest_revision.alignment_focus}")
        st.write(latest_revision.reason_for_change)