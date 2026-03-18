from __future__ import annotations

import json
from pathlib import Path
import streamlit as st

from store.run_store import make_run_id, init_run, save_state, load_json
from engine.workflow import run_step


REPO_ROOT = Path(__file__).parent.resolve()


def list_input_files() -> list[Path]:
    p = REPO_ROOT / "inputs"
    p.mkdir(exist_ok=True)
    return sorted([x for x in p.glob("*") if x.is_file()])


def main():
    st.set_page_config(page_title="Janet Job MVP", layout="wide")
    st.title("Job Optmizer MVP - Main Dashboard")
    st.header("Improve job decision making by matching professional identity and job contexts.")
    st.subheader("Upload resume, job description and an old cover letter to begin blueprinting.")

    # --- session init ---
    if "run_id" not in st.session_state:
        st.session_state.run_id = make_run_id()
        st.session_state.run_paths = init_run(REPO_ROOT, st.session_state.run_id)
        st.session_state.state = {
            "run_id": st.session_state.run_id,
            "candidate_id": "janet",
            "approved_steps": [],
            "artifacts": {},
            "inputs": {
                "resume_text": "",
                # NEW: explicit cover letter fields
                "starting_cover_letter_text": "",
                "working_cover_letter_text": "",
                # Keep existing list for compatibility with prompts.py
                "cover_letter_texts": [],
                "notes_texts": [],
                "job_text": "",
                "job_meta": {"source": "manual"}
            }
        }
        save_state(st.session_state.run_paths, st.session_state.state)

    state = st.session_state.state
    run_paths = st.session_state.run_paths

    # --- sidebar: preloaded file preview ---
# [START PATCH 2/2 — Sidebar load buttons + main UI fields + harmonize cover_letter_texts]

    # --- sidebar: preloaded file preview ---
    st.sidebar.header("Preloaded Files (/inputs)")
    files = list_input_files()
    selected = st.sidebar.selectbox("Select a file", ["(none)"] + [f.name for f in files])

    if selected != "(none)":
        fpath = next(x for x in files if x.name == selected)
        text = fpath.read_text(encoding="utf-8", errors="ignore")
        st.sidebar.caption(f"{fpath.name} ({len(text)} chars)")
        st.sidebar.text_area("Preview", text[:2000], height=250)

        if st.sidebar.button("Load as Resume Text"):
            state["inputs"]["resume_text"] = text
            save_state(run_paths, state)

        if st.sidebar.button("Load as Job Description"):
            state["inputs"]["job_text"] = text
            save_state(run_paths, state)

        # NEW: cover letter loaders
        if st.sidebar.button("Load as Starting Cover Letter"):
            state["inputs"]["starting_cover_letter_text"] = text
            save_state(run_paths, state)

        if st.sidebar.button("Load as Working Cover Letter"):
            state["inputs"]["working_cover_letter_text"] = text
            save_state(run_paths, state)

        st.sidebar.divider()
        st.sidebar.caption("Loaded assets")
        st.sidebar.write({
        "resume_len": len((state["inputs"].get("resume_text") or "").strip()),
        "starting_CL_len": len((state["inputs"].get("starting_cover_letter_text") or "").strip()),
        "working_CL_len": len((state["inputs"].get("working_cover_letter_text") or "").strip()),
        "job_desc_len": len((state["inputs"].get("job_text") or "").strip()),
        })
    # --- main: inputs ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Resume Text (Step 1 input)")
        state["inputs"]["resume_text"] = st.text_area(
            "Paste resume text", value=state["inputs"]["resume_text"], height=220
        )

    with col2:
        st.subheader("Job Description (Step 3 input)")
        state["inputs"]["job_text"] = st.text_area(
            "Paste job description", value=state["inputs"]["job_text"], height=220
        )

    # NEW: cover letter fields (two-column layout)
    st.divider()
    st.subheader("Cover Letters (optional, used in Step 2 Profile Blueprint)")

    cl1, cl2 = st.columns(2)
    with cl1:
        state["inputs"]["starting_cover_letter_text"] = st.text_area(
            "Starting Cover Letter (baseline voice/template)",
            value=state["inputs"].get("starting_cover_letter_text", ""),
            height=220,
        )

    with cl2:
        state["inputs"]["working_cover_letter_text"] = st.text_area(
            "Working Cover Letter (current draft)",
            value=state["inputs"].get("working_cover_letter_text", ""),
            height=220,
        )

    # Harmonize into cover_letter_texts for compatibility with existing engine prompts
    cover_letters: list[str] = []
    if (state["inputs"].get("starting_cover_letter_text") or "").strip():
        cover_letters.append(state["inputs"]["starting_cover_letter_text"].strip())
    if (state["inputs"].get("working_cover_letter_text") or "").strip():
        cover_letters.append(state["inputs"]["working_cover_letter_text"].strip())
    state["inputs"]["cover_letter_texts"] = cover_letters

    save_state(run_paths, state)

# [END PATCH 2/2]

    # --- main: inputs ---

    st.divider()
    st.subheader("Steps (Run → Review JSON → Approve & Continue)")

    step_cols = st.columns(4)
    steps = [("1", "Candidate Profile"), ("2", "Profile Blueprint"), ("3", "Job Blueprint"), ("4", "Match Report")]

    for i, (sid, label) in enumerate(steps):
        with step_cols[i]:
            if st.button(f"Run Step {sid}\n{label}", use_container_width=True):
                st.session_state.state = run_step(REPO_ROOT, run_paths, sid, st.session_state.state)
                st.success(f"Step {sid} complete.")
            st.caption(f"Artifact: {state['artifacts'].get(_artifact_key(sid), '—')}")

    st.divider()
    st.subheader("Artifacts (latest)")

    for sid, label in steps:
        key = _artifact_key(sid)
        path = state["artifacts"].get(key)
        with st.expander(f"Step {sid}: {label}", expanded=(sid == "4")):
            if path:
                obj = load_json(Path(path))
                st.json(obj)
            else:
                st.info("Not generated yet.")

    st.caption(f"Run ID: {state['run_id']}")


def _artifact_key(step_id: str) -> str:
    return {
        "1": "candidate_profile",
        "2": "profile_blueprint",
        "3": "job_blueprint",
        "4": "match_report",
    }[step_id]


if __name__ == "__main__":
    main()