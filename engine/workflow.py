from __future__ import annotations

import json
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, Tuple

from llm.client import get_client, load_llm_config, chat_json
from llm.prompts import (
    system_json_only,
    build_profile_blueprint_prompt,
    build_job_blueprint_prompt,
    build_match_report_prompt,
)
from store.run_store import RunPaths, save_artifact, save_prompt, save_state
from validators.validate import validate_artifact


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def run_step(repo_root: Path, run_paths: RunPaths, step_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    The ONLY business entrypoint.
    UI and CLI both call this.

    It:
    - reads inputs from state
    - produces one artifact
    - validates it
    - saves it
    - updates state with artifact path
    """
    client = get_client()
    cfg = load_llm_config()

    if "approved_steps" not in state:
        state["approved_steps"] = []
    if "artifacts" not in state:
        state["artifacts"] = {}

    # ---------- STEP 1: candidate_profile (minimal chunking) ----------
    if step_id == "1":
        resume_text = (state.get("inputs", {}).get("resume_text") or "").strip()
        if not resume_text:
            raise ValueError("Step 1 requires inputs.resume_text")

        # Minimal chunking MVP: single chunk + (optional) later improvements
        chunks = [{
            "chunk_id": "r_001",
            "chunk_type": "resume_full",
            "text": resume_text,
            "tags": []
        }]

        artifact = {
            "schema_version": "1.0",
            "artifact_type": "candidate_profile",
            "created_at": _now_iso(),
            "run_id": state["run_id"],
            "candidate_id": state.get("candidate_id", "janet"),
            "source_refs": state.get("inputs", {}).get("source_refs", {}),
            "raw_text": {
                "resume_text": resume_text,
                "cover_letter_texts": state.get("inputs", {}).get("cover_letter_texts", []),
                "notes_texts": state.get("inputs", {}).get("notes_texts", []),
            },
            "chunks": chunks,
            "redaction": {"pii_removed": False, "notes": ""}
        }

        err = validate_artifact(repo_root, artifact)
        if err:
            raise ValueError(err)

        p = save_artifact(run_paths, "candidate_profile", artifact)
        state["artifacts"]["candidate_profile"] = str(p)
        save_state(run_paths, state)
        return state

    # ---------- STEP 2: profile_blueprint ----------
    if step_id == "2":
        # gate: step 1 must exist (approval optional; you can tighten later)
        cand_path = state["artifacts"].get("candidate_profile")
        if not cand_path:
            raise ValueError("Step 2 requires candidate_profile artifact (run Step 1 first).")

        candidate_profile = json.loads(Path(cand_path).read_text(encoding="utf-8"))
        resume_text = candidate_profile["raw_text"]["resume_text"]
        cover_letters = candidate_profile["raw_text"].get("cover_letter_texts", [])
        notes = candidate_profile["raw_text"].get("notes_texts", [])

        user_prompt = build_profile_blueprint_prompt(resume_text, cover_letters, notes)
        save_prompt(run_paths, "2", user_prompt)

        raw = chat_json(client, cfg, system_json_only(), user_prompt)
        artifact = json.loads(raw)

        # inject required meta fields if prompt forgets (minimal patch)
        artifact.setdefault("schema_version", "1.0")
        artifact["artifact_type"] = "profile_blueprint"
        artifact.setdefault("created_at", _now_iso())
        artifact["run_id"] = state["run_id"]
        artifact["candidate_id"] = state.get("candidate_id", "janet")

        err = validate_artifact(repo_root, artifact)
        if err:
            raise ValueError(err)

        p = save_artifact(run_paths, "profile_blueprint", artifact)
        state["artifacts"]["profile_blueprint"] = str(p)
        save_state(run_paths, state)
        return state

    # ---------- STEP 3: job_blueprint ----------
    if step_id == "3":
        job_text = (state.get("inputs", {}).get("job_text") or "").strip()
        if not job_text:
            raise ValueError("Step 3 requires inputs.job_text (paste JD).")

        meta = state.get("inputs", {}).get("job_meta", {})
        title = meta.get("title", "")
        company = meta.get("company", "")
        location = meta.get("location", "")
        source = meta.get("source", "manual")

        user_prompt = build_job_blueprint_prompt(job_text, title=title, company=company, location=location, source=source)
        save_prompt(run_paths, "3", user_prompt)

        artifact = chat_json(client, cfg, system_json_only(), user_prompt)

        artifact.setdefault("schema_version", "1.0")
        artifact["artifact_type"] = "job_blueprint"
        artifact.setdefault("created_at", _now_iso())
        artifact["run_id"] = state["run_id"]
        artifact.setdefault("job_id", f"job_{_fingerprint(job_text)}")

        # enforce minimal job_meta if missing
        artifact.setdefault("job_meta", {})
        artifact["job_meta"].setdefault("title", title)
        artifact["job_meta"].setdefault("company", company)
        artifact["job_meta"].setdefault("location", location)
        artifact["job_meta"].setdefault("url", None)
        artifact["job_meta"].setdefault("source", source)
        artifact["job_meta"].setdefault("retrieved_at", _now_iso())

        err = validate_artifact(repo_root, artifact)
        if err:
            raise ValueError(err)

        p = save_artifact(run_paths, "job_blueprint", artifact)
        state["artifacts"]["job_blueprint"] = str(p)
        save_state(run_paths, state)
        return state

    # ---------- STEP 4: match_report ----------
    if step_id == "4":
        pb_path = state["artifacts"].get("profile_blueprint")
        jb_path = state["artifacts"].get("job_blueprint")
        if not pb_path or not jb_path:
            raise ValueError("Step 4 requires profile_blueprint (Step 2) and job_blueprint (Step 3).")

        profile_blueprint_json = Path(pb_path).read_text(encoding="utf-8")
        job_blueprint_json = Path(jb_path).read_text(encoding="utf-8")

        user_prompt = build_match_report_prompt(profile_blueprint_json, job_blueprint_json)
        save_prompt(run_paths, "4", user_prompt)

        raw = chat_json(client, cfg, system_json_only(), user_prompt)
        artifact = json.loads(raw)

        artifact.setdefault("schema_version", "1.0")
        artifact["artifact_type"] = "match_report"
        artifact.setdefault("created_at", _now_iso())
        artifact["run_id"] = state["run_id"]
        artifact["candidate_id"] = state.get("candidate_id", "janet")

        # propagate job_id if missing
        job_bp = json.loads(job_blueprint_json)
        artifact["job_id"] = artifact.get("job_id") or job_bp.get("job_id")

        err = validate_artifact(repo_root, artifact)
        if err:
            raise ValueError(err)

        p = save_artifact(run_paths, "match_report", artifact)
        state["artifacts"]["match_report"] = str(p)
        save_state(run_paths, state)
        return state

    raise ValueError(f"Unknown step_id: {step_id}")