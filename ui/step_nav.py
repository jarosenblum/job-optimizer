from __future__ import annotations

import streamlit as st

from workflow.contracts import StepStatus, WorkflowState
from workflow.step_registry import StepRegistry


def _status_icon(status: StepStatus) -> str:
    if status == StepStatus.COMPLETE:
        return "✅"
    if status == StepStatus.IN_PROGRESS:
        return "🟦"
    if status == StepStatus.FAILED_VALIDATION:
        return "⚠️"
    if status == StepStatus.AVAILABLE:
        return "🟢"
    return "🔒"


def render_step_nav(
    workflow_state: WorkflowState,
    registry: StepRegistry,
    *,
    session_key_prefix: str = "nav",
) -> None:
    st.subheader("Workflow")

    for step_def in registry.all_steps():
        step_state = next(s for s in workflow_state.step_states if s.step_id == step_def.step_id)
        is_current = workflow_state.current_step_id == step_def.step_id
        icon = _status_icon(step_state.status)

        label = f"{icon} {step_def.step_order}. {step_def.step_name}"
        if is_current:
            st.markdown(f"**{label}**")
        else:
            st.markdown(label)

        if step_def.description:
            st.caption(step_def.description)

        if step_state.is_unlocked:
            button_label = "Open" if not is_current else "Current step"
            if is_current:
                st.button(button_label, key=f"{session_key_prefix}_{step_def.step_id}", disabled=True)
            else:
                if st.button(button_label, key=f"{session_key_prefix}_{step_def.step_id}"):
                    st.session_state.requested_step_id = step_def.step_id
        else:
            st.button(
                "Locked",
                key=f"{session_key_prefix}_{step_def.step_id}",
                disabled=True,
            )

        st.markdown("---")