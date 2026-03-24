from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from engine.workflow import run_step

try:
    from store.run_store import RunPaths
except ImportError:
    RunPaths = None  # type: ignore


@dataclass
class KernelResult:
    ok: bool
    task_name: str
    step_id: str
    artifact_type: Optional[str] = None
    artifact: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskRunner:
    """
    Thin orchestration kernel for the job optimizer.

    Responsibilities:
    - map high-level task names to backend step ids
    - pass normalized state into engine.workflow.run_step(...)
    - return normalized results for app_core.py
    """

    TASK_TO_STEP = {
        "candidate_profile": "1",
        "profile_blueprint": "2",
        "job_blueprint": "3",
        "match_report": "4",
    }

    def __init__(self, repo_root: Path, run_paths: Any) -> None:
        self.repo_root = Path(repo_root)
        self.run_paths = run_paths

    def run_task(
        self,
        task_name: str,
        *,
        resume_text: str = "",
        jd_text: str = "",
        cover_letter_text: str = "",
        state: Optional[Dict[str, Any]] = None,
    ) -> KernelResult:
        step_id = self.TASK_TO_STEP.get(task_name)
        if not step_id:
            return KernelResult(
                ok=False,
                task_name=task_name,
                step_id="",
                error=f"Unknown task_name: {task_name}",
            )

        working_state = dict(state or {})
        working_state.setdefault("inputs", {})
        working_state.setdefault("artifacts", {})
        working_state.setdefault("approved_steps", [])

        # Align with engine.workflow.run_step(...) expected input contract
        if resume_text:
            working_state["inputs"]["resume_text"] = resume_text

        if jd_text:
            working_state["inputs"]["job_text"] = jd_text

        if cover_letter_text:
            existing_cls = working_state["inputs"].get("cover_letter_texts", [])
            if not isinstance(existing_cls, list):
                existing_cls = []
            if cover_letter_text not in existing_cls:
                existing_cls.append(cover_letter_text)
            working_state["inputs"]["cover_letter_texts"] = existing_cls

        working_state["inputs"].setdefault("notes_texts", [])
        working_state["inputs"].setdefault("job_meta", {})

        try:
            updated_state = run_step(
                repo_root=self.repo_root,
                run_paths=self.run_paths,
                step_id=step_id,
                state=working_state,
            )
        except Exception as e:
            return KernelResult(
                ok=False,
                task_name=task_name,
                step_id=step_id,
                error=str(e),
                state=working_state,
            )

        artifact = self._extract_latest_artifact(task_name, updated_state)

        return KernelResult(
            ok=True,
            task_name=task_name,
            step_id=step_id,
            artifact_type=(artifact or {}).get("artifact_type"),
            artifact=artifact,
            state=updated_state,
        )

    def run_match_pipeline(
        self,
        *,
        resume_text: str,
        jd_text: str,
        cover_letter_text: str = "",
        state: Optional[Dict[str, Any]] = None,
    ) -> KernelResult:
        """
        Run the minimum high-value chain:
        1 -> candidate_profile
        2 -> profile_blueprint
        3 -> job_blueprint
        4 -> match_report
        """
        working_state = dict(state or {})
        working_state.setdefault("inputs", {})
        working_state.setdefault("artifacts", {})
        working_state.setdefault("approved_steps", [])

        working_state["inputs"]["resume_text"] = resume_text
        working_state["inputs"]["job_text"] = jd_text
        working_state["inputs"]["cover_letter_texts"] = [cover_letter_text] if cover_letter_text else []
        working_state["inputs"].setdefault("notes_texts", [])
        working_state["inputs"].setdefault("job_meta", {})

        for task_name in ("candidate_profile", "profile_blueprint", "job_blueprint", "match_report"):
            result = self.run_task(
                task_name,
                resume_text=resume_text,
                jd_text=jd_text,
                cover_letter_text=cover_letter_text,
                state=working_state,
            )
            if not result.ok:
                return result
            working_state = result.state or working_state

        artifact = self._extract_latest_artifact("match_report", working_state)

        return KernelResult(
            ok=True,
            task_name="match_pipeline",
            step_id="4",
            artifact_type=(artifact or {}).get("artifact_type"),
            artifact=artifact,
            state=working_state,
        )

    def _extract_latest_artifact(self, task_name: str, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Supports both:
        - inline artifact dicts in state["artifacts"]
        - saved artifact file paths in state["artifacts"]
        """
        artifacts = state.get("artifacts", {})

        preferred_keys = {
            "candidate_profile": ["candidate_profile", "step_1", "1"],
            "profile_blueprint": ["profile_blueprint", "step_2", "2"],
            "job_blueprint": ["job_blueprint", "step_3", "3"],
            "match_report": ["match_report", "step_4", "4"],
        }.get(task_name, [])

        for key in preferred_keys:
            value = artifacts.get(key)

            if isinstance(value, dict):
                return value

            if isinstance(value, str):
                path = Path(value)
                if path.exists():
                    try:
                        return json.loads(path.read_text(encoding="utf-8"))
                    except Exception:
                        pass

        expected_type = {
            "candidate_profile": "candidate_profile",
            "profile_blueprint": "profile_blueprint",
            "job_blueprint": "job_blueprint",
            "match_report": "match_report",
        }.get(task_name)

        for value in artifacts.values():
            if isinstance(value, dict) and value.get("artifact_type") == expected_type:
                return value

            if isinstance(value, str):
                path = Path(value)
                if path.exists():
                    try:
                        loaded = json.loads(path.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict) and loaded.get("artifact_type") == expected_type:
                            return loaded
                    except Exception:
                        pass

        return None