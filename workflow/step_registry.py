from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from workflow.contracts import StepDefinition


class StepRegistry:
    """
    Loads and serves canonical workflow step definitions from JSON config.
    """

    def __init__(self, steps: List[StepDefinition]) -> None:
        self._steps = sorted(steps, key=lambda s: s.step_order)
        self._by_id: Dict[str, StepDefinition] = {step.step_id: step for step in self._steps}
        self._validate_unique_ids()
        self._validate_unique_order()

    @classmethod
    def from_json(cls, filepath: str | Path) -> "StepRegistry":
        path = Path(filepath)
        data = json.loads(path.read_text(encoding="utf-8"))
        steps = [StepDefinition(**item) for item in data.get("steps", [])]
        return cls(steps)

    def _validate_unique_ids(self) -> None:
        if len(self._by_id) != len(self._steps):
            raise ValueError("Duplicate step_id values found in step registry.")

    def _validate_unique_order(self) -> None:
        orders = [step.step_order for step in self._steps]
        if len(orders) != len(set(orders)):
            raise ValueError("Duplicate step_order values found in step registry.")

    def all_steps(self) -> List[StepDefinition]:
        return list(self._steps)

    def get_step(self, step_id: str) -> Optional[StepDefinition]:
        return self._by_id.get(step_id)

    def require_step(self, step_id: str) -> StepDefinition:
        step = self.get_step(step_id)
        if step is None:
            raise KeyError(f"Unknown step_id: {step_id}")
        return step

    def first_step(self) -> StepDefinition:
        if not self._steps:
            raise ValueError("Step registry is empty.")
        return self._steps[0]

    def next_step(self, step_id: str) -> Optional[StepDefinition]:
        current = self.require_step(step_id)
        for step in self._steps:
            if step.step_order == current.step_order + 1:
                return step
        return None

    def previous_step(self, step_id: str) -> Optional[StepDefinition]:
        current = self.require_step(step_id)
        for step in self._steps:
            if step.step_order == current.step_order - 1:
                return step
        return None