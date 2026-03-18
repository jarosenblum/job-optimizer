from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from jsonschema import validate as js_validate
from jsonschema.exceptions import ValidationError


SCHEMA_MAP = {
    "candidate_profile": "schemas/candidate_profile.schema.json",
    "profile_blueprint": "schemas/profile_blueprint.schema.json",
    "job_blueprint": "schemas/job_blueprint.schema.json",
    "match_report": "schemas/match_report.schema.json",
}


def load_schema(repo_root: Path, artifact_type: str) -> Dict[str, Any]:
    schema_path = repo_root / SCHEMA_MAP[artifact_type]
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_artifact(repo_root: Path, artifact: Dict[str, Any]) -> Optional[str]:
    """
    Returns None if valid, else returns an error message string.
    """
    artifact_type = artifact.get("artifact_type")
    if artifact_type not in SCHEMA_MAP:
        return f"Unknown artifact_type: {artifact_type}"

    try:
        schema = load_schema(repo_root, artifact_type)
        js_validate(instance=artifact, schema=schema)
    except ValidationError as e:
        return f"Schema validation failed for {artifact_type}: {e.message}"

    # extra sanity checks (lightweight)
    if artifact_type == "match_report":
        score = artifact.get("overall", {}).get("fit_score")
        if score is None or not (0 <= float(score) <= 100):
            return f"match_report fit_score out of bounds: {score}"

    return None