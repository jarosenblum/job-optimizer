from __future__ import annotations
from uuid import uuid4

from workflow.contracts import UIState, UserSession, WorkflowState
from datetime import datetime, timezone

class SessionManager:
    """
    Phase 1 in-memory session bootstrapper.
    """

    @staticmethod
    def create_session(active_workflow_id: str, active_step_id: str) -> UserSession:
        now = datetime.now(timezone.utc)
        return UserSession(
            session_id=str(uuid4()),
            created_at=now,
            updated_at=now,
            active_workflow_id=active_workflow_id,
            active_step_id=active_step_id,
            completed_step_ids=[],
            ui_state=UIState(),
        )

    @staticmethod
    def sync_session_with_workflow(session: UserSession, workflow_state: WorkflowState) -> UserSession:
        session.active_workflow_id = workflow_state.workflow_id
        session.active_step_id = workflow_state.current_step_id
        session.completed_step_ids = [
            step.step_id for step in workflow_state.step_states if step.status.value == "complete"
        ]
        session.updated_at = datetime.now(timezone.utc)
        return session