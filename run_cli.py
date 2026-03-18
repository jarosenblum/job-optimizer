from __future__ import annotations

import argparse
from pathlib import Path

from store.run_store import make_run_id, init_run, save_state
from engine.workflow import run_step


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", type=str, required=True)
    parser.add_argument("--jd", type=str, required=True)
    parser.add_argument("--candidate_id", type=str, default="janet")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.resolve()

    run_id = make_run_id()
    run_paths = init_run(repo_root, run_id)

    resume_text = Path(args.resume).read_text(encoding="utf-8")
    job_text = Path(args.jd).read_text(encoding="utf-8")

    state = {
        "run_id": run_id,
        "candidate_id": args.candidate_id,
        "approved_steps": [],
        "artifacts": {},
        "inputs": {
            "resume_text": resume_text,
            "cover_letter_texts": [],
            "notes_texts": [],
            "job_text": job_text,
            "job_meta": {"source": "manual"}
        }
    }
    save_state(run_paths, state)

    for step in ["1", "2", "3", "4"]:
        state = run_step(repo_root, run_paths, step, state)

    print(f"✅ Run complete: {run_id}")
    print("Artifacts:")
    for k, v in state["artifacts"].items():
        print(f"  - {k}: {v}")


if __name__ == "__main__":
    main()