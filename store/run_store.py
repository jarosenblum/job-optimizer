from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class RunPaths:
    run_dir: Path
    artifacts_dir: Path
    prompts_dir: Path


def make_run_id(prefix: str = "run") -> str:
    return f"{prefix}_{time.strftime('%Y%m%d_%H%M%S')}"


def init_run(repo_root: Path, run_id: str) -> RunPaths:
    run_dir = repo_root / "runs" / run_id
    artifacts_dir = run_dir / "artifacts"
    prompts_dir = run_dir / "prompts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir.mkdir(parents=True, exist_ok=True)

    # minimal meta
    meta = {
        "run_id": run_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return RunPaths(run_dir=run_dir, artifacts_dir=artifacts_dir, prompts_dir=prompts_dir)


def save_json(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_artifact(run_paths: RunPaths, artifact_type: str, obj: Dict[str, Any]) -> Path:
    out_path = run_paths.artifacts_dir / f"{artifact_type}.json"
    save_json(out_path, obj)
    return out_path


def save_prompt(run_paths: RunPaths, step_id: str, prompt_text: str) -> Path:
    out_path = run_paths.prompts_dir / f"prompt_{step_id}.txt"
    out_path.write_text(prompt_text, encoding="utf-8")
    return out_path


def save_state(run_paths: RunPaths, state: Dict[str, Any]) -> Path:
    out_path = run_paths.run_dir / "state.json"
    save_json(out_path, state)
    return out_path