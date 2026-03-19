from __future__ import annotations

from typing import Iterable, Optional

import streamlit as st

from workflow.contracts import CoverLetterDraft, GeneratedArtifact, RevisionSuggestion


def render_artifact_panel(
    *,
    revisions: Optional[Iterable[RevisionSuggestion]] = None,
    cover_letter: Optional[CoverLetterDraft] = None,
    generated_artifacts: Optional[Iterable[GeneratedArtifact]] = None,
) -> None:
    st.subheader("Artifacts")

    revisions = list(revisions or [])
    generated_artifacts = list(generated_artifacts or [])

    if revisions:
        st.markdown("### Revision suggestions")
        for idx, rev in enumerate(revisions, start=1):
            with st.expander(f"{idx}. {rev.target_section.value.title()} revision — {rev.alignment_focus}", expanded=False):
                if rev.original_text:
                    st.markdown("**Original**")
                    st.code(rev.original_text)

                st.markdown("**Revised**")
                st.code(rev.revised_text)

                st.markdown("**Why this change matters**")
                st.write(rev.reason_for_change)

                st.markdown(f"**Priority:** {rev.priority.value}")

    if cover_letter:
        st.markdown("### Cover letter draft")
        st.text_area(
            "Draft",
            value=cover_letter.full_text,
            height=280,
            key="artifact_cover_letter_text",
        )

    if generated_artifacts:
        st.markdown("### Generated output blocks")
        for artifact in generated_artifacts:
            with st.expander(f"{artifact.title} ({artifact.artifact_type.value})", expanded=False):
                st.text_area(
                    artifact.title,
                    value=artifact.content,
                    height=180,
                    key=f"artifact_{artifact.artifact_id}",
                )

    if not revisions and not cover_letter and not generated_artifacts:
        st.info("No artifacts yet. Revisions and outputs will appear here as the workflow advances.")