import json
from pathlib import Path


BASE = Path(__file__).resolve().parent
WORKFLOW_DEFINITION_PATH = BASE / "workflow_definition.json"
STEP_REGISTRY_PATH = BASE / "step_registry.json"
VALIDATION_RULES_PATH = BASE / "validation_rules.json"


def main():
    workflow_def = json.loads(WORKFLOW_DEFINITION_PATH.read_text(encoding="utf-8"))
    step_registry = json.loads(STEP_REGISTRY_PATH.read_text(encoding="utf-8"))
    validation_rules = json.loads(VALIDATION_RULES_PATH.read_text(encoding="utf-8"))

    workflow_steps = workflow_def["steps"]
    registry_steps = step_registry["steps"]
    registry_step_ids = [s["step_id"] for s in registry_steps]
    registry_orders = [s["step_order"] for s in registry_steps]
    rule_step_ids = [r["step_id"] for r in validation_rules["rules"]]

    assert len(registry_step_ids) == len(set(registry_step_ids)), "Duplicate step_id found."
    assert len(registry_orders) == len(set(registry_orders)), "Duplicate step_order found."
    assert workflow_steps == registry_step_ids, "workflow_definition.json and step_registry.json are out of sync."

    for step_id in rule_step_ids:
        assert step_id in registry_step_ids, f"Validation rule references unknown step_id: {step_id}"

    print("Config consistency check passed.")


if __name__ == "__main__":
    main()