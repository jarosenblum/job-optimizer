from __future__ import annotations

from typing import Any, Dict, List


def match_report_to_ui_payload(match_report: Dict[str, Any]) -> Dict[str, Any]:
    if not match_report:
        return {
            "overall_score": None,
            "strengths": [],
            "gaps": [],
            "keywords": [],
            "raw": None,
        }

    overall = match_report.get("overall", {})
    gaps = match_report.get("gaps", {})
    evidence = match_report.get("evidence", {})

    return {
        "overall_score": overall.get("fit_score"),
        "strengths": evidence.get("strengths", []),
        "gaps": gaps.get("priority_gaps", []) or gaps.get("gaps", []),
        "keywords": overall.get("matched_keywords", []),
        "raw": match_report,
    }