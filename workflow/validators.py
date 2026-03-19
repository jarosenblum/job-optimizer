from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from workflow.contracts import ValidationResult, ValidationRule


class ValidationRuleSet:
    def __init__(self, rules: List[ValidationRule]) -> None:
        self._rules = rules
        self._rules_by_step: Dict[str, List[ValidationRule]] = {}
        for rule in rules:
            self._rules_by_step.setdefault(rule.step_id, []).append(rule)

    @classmethod
    def from_json(cls, filepath: str | Path) -> "ValidationRuleSet":
        path = Path(filepath)
        data = json.loads(path.read_text(encoding="utf-8"))
        rules = [ValidationRule(**item) for item in data.get("rules", [])]
        return cls(rules)

    def get_rules_for_step(self, step_id: str) -> List[ValidationRule]:
        return self._rules_by_step.get(step_id, [])


class ValidatorEngine:
    """
    Simple Phase 1 validator. Can be extended later with richer field mapping
    and contract-aware object validation.
    """

    def __init__(self, rule_set: ValidationRuleSet) -> None:
        self.rule_set = rule_set

    def validate_step(self, step_id: str, payload: Dict[str, Any]) -> ValidationResult:
        rules = self.rule_set.get_rules_for_step(step_id)

        passed_rule_ids: List[str] = []
        failed_rule_ids: List[str] = []
        messages: List[str] = []

        for rule in rules:
            is_valid = self._evaluate_rule(rule, payload)
            if is_valid:
                passed_rule_ids.append(rule.rule_id)
            else:
                failed_rule_ids.append(rule.rule_id)
                messages.append(rule.error_message)

        return ValidationResult(
            step_id=step_id,
            is_valid=len(failed_rule_ids) == 0,
            passed_rule_ids=passed_rule_ids,
            failed_rule_ids=failed_rule_ids,
            messages=messages,
        )

    def _evaluate_rule(self, rule: ValidationRule, payload: Dict[str, Any]) -> bool:
        target_value = payload.get(rule.target_field) if rule.target_field else None

        if rule.condition == "non_empty":
            return target_value is not None and str(target_value).strip() != ""

        if rule.rule_type.value == "min_length":
            try:
                min_len = int(rule.condition)
            except ValueError:
                return False
            return target_value is not None and len(str(target_value).strip()) >= min_len

        if rule.rule_type.value == "contract_presence":
            return target_value is not None

        # Extend this block later for cross-step / richer expressions.
        return True