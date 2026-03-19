from pathlib import Path

from workflow.step_registry import StepRegistry
from workflow.validators import ValidationRuleSet, ValidatorEngine
from workflow.router import WorkflowRouter
from workflow.session_manager import SessionManager

BASE = Path(__file__).resolve().parent

STEP_REGISTRY_PATH = BASE / "step_registry.json"
VALIDATION_RULES_PATH = BASE / "validation_rules.json"


def print_workflow_state(workflow_state):
    print(f"\nWorkflow: {workflow_state.workflow_name}")
    print(f"Current step: {workflow_state.current_step_id}")
    print(f"Status: {workflow_state.status.value}")
    for step in workflow_state.step_states:
        print(
            f" - {step.step_id}: status={step.status.value}, "
            f"unlocked={step.is_unlocked}, "
            f"validation={step.validation_status}"
        )


def main():
    registry = StepRegistry.from_json(STEP_REGISTRY_PATH)
    rule_set = ValidationRuleSet.from_json(VALIDATION_RULES_PATH)
    validator = ValidatorEngine(rule_set)
    router = WorkflowRouter(registry, validator)

    workflow_state = router.initialize_workflow(
        workflow_id="local_test_workflow",
        workflow_name="Local Workflow Smoke Test",
    )

    session = SessionManager.create_session(
        active_workflow_id=workflow_state.workflow_id,
        active_step_id=workflow_state.current_step_id,
    )

    print("=== INITIALIZED WORKFLOW ===")
    print_workflow_state(workflow_state)

    # Step 1: resume_intake invalid
    workflow_state = router.start_step(workflow_state, "resume_intake")
    workflow_state = router.complete_step(
        workflow_state,
        "resume_intake",
        payload={"raw_text": ""},
        output_ref=None,
    )
    session = SessionManager.sync_session_with_workflow(session, workflow_state)

    print("\n=== AFTER INVALID resume_intake ===")
    print_workflow_state(workflow_state)
    print("Session completed steps:", session.completed_step_ids)

    # Retry valid
    workflow_state = router.complete_step(
        workflow_state,
        "resume_intake",
        payload={"raw_text": "Sample resume text with experience and skills."},
        output_ref="resume_001",
    )
    session = SessionManager.sync_session_with_workflow(session, workflow_state)

    print("\n=== AFTER VALID resume_intake ===")
    print_workflow_state(workflow_state)
    print("Session completed steps:", session.completed_step_ids)

    # Step 2: job_description_intake valid
    workflow_state = router.start_step(workflow_state, "job_description_intake")
    workflow_state = router.complete_step(
        workflow_state,
        "job_description_intake",
        payload={"raw_text": "Sample job description requiring leadership and analytics."},
        output_ref="jd_001",
    )
    session = SessionManager.sync_session_with_workflow(session, workflow_state)

    print("\n=== AFTER VALID job_description_intake ===")
    print_workflow_state(workflow_state)
    print("Session completed steps:", session.completed_step_ids)

    print("\nSmoke test complete.")


if __name__ == "__main__":
    main()