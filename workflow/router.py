from __future__ import annotations

from typing import Optional

from workflow.contracts import StepState, StepStatus, WorkflowState, WorkflowStatus
from workflow.step_registry import StepRegistry
from workflow.validators import ValidatorEngine
from datetime import datetime, timezone


class WorkflowRouter:
    """
    Controls active-step progression and unlock behavior for Phase 1.
    """

    def __init__(self, registry: StepRegistry, validator: ValidatorEngine) -> None:
        self.registry = registry
        self.validator = validator

    def initialize_workflow(self, workflow_id: str, workflow_name: str) -> WorkflowState:
        first_step = self.registry.first_step()
        step_states = []

        for step in self.registry.all_steps():
            if step.step_id == first_step.step_id:
                status = StepStatus.AVAILABLE
                is_unlocked = True
            else:
                status = StepStatus.LOCKED
                is_unlocked = False

            step_states.append(
                StepState(
                    step_id=step.step_id,
                    status=status,
                    is_unlocked=is_unlocked,
                    is_required=step.is_required,
                )
            )

        return WorkflowState(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            current_step_id=first_step.step_id,
            status=WorkflowStatus.NOT_STARTED,
            step_states=step_states,
        )

    def start_step(self, workflow_state: WorkflowState, step_id: str) -> WorkflowState:
        step_state = self._get_step_state(workflow_state, step_id)
        if not step_state.is_unlocked:
            raise ValueError(f"Step '{step_id}' is locked.")

        step_state.status = StepStatus.IN_PROGRESS
        step_state.started_at = datetime.now(timezone.utc)
        workflow_state.current_step_id = step_id
        workflow_state.status = WorkflowStatus.IN_PROGRESS
        return workflow_state

    def complete_step(
        self,
        workflow_state: WorkflowState,
        step_id: str,
        payload: dict,
        output_ref: Optional[str] = None,
    ) -> WorkflowState:
        validation = self.validator.validate_step(step_id, payload)
        step_state = self._get_step_state(workflow_state, step_id)

        step_state.validation_status = "valid" if validation.is_valid else "invalid"
        step_state.validation_messages = validation.messages

        if not validation.is_valid:
            step_state.status = StepStatus.FAILED_VALIDATION
            workflow_state.status = WorkflowStatus.BLOCKED
            return workflow_state

        step_state.status = StepStatus.COMPLETE
        step_state.completed_at = datetime.now(timezone.utc)

        if output_ref:
            step_state.output_refs.append(output_ref)

        next_step = self.registry.next_step(step_id)
        if next_step:
            next_step_state = self._get_step_state(workflow_state, next_step.step_id)
            next_step_state.is_unlocked = True
            if next_step_state.status == StepStatus.LOCKED:
                next_step_state.status = StepStatus.AVAILABLE
            workflow_state.current_step_id = next_step.step_id
            workflow_state.status = WorkflowStatus.IN_PROGRESS
        else:
            workflow_state.status = WorkflowStatus.COMPLETE

        return workflow_state

    def go_to_step(self, workflow_state: WorkflowState, step_id: str) -> WorkflowState:
        step_state = self._get_step_state(workflow_state, step_id)
        if not step_state.is_unlocked:
            raise ValueError(f"Cannot navigate to locked step '{step_id}'.")
        workflow_state.current_step_id = step_id
        return workflow_state

    def _get_step_state(self, workflow_state: WorkflowState, step_id: str) -> StepState:
        for step_state in workflow_state.step_states:
            if step_state.step_id == step_id:
                return step_state
        raise KeyError(f"StepState not found for step_id='{step_id}'")