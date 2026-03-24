# llm/prompts.py
from __future__ import annotations


def system_json_only() -> str:
    return (
        "You are a careful assistant that returns ONLY valid JSON. "
        "Do not return markdown, code fences, commentary, or prose before or after the JSON. "
        "Use double quotes for all keys and all string values. "
        "Do not include trailing commas. "
        "Do not wrap arrays inside objects like {\"list\": [...]} or {\"items\": [...]}. "
        "When a field is specified as an array, return a raw JSON array."
    )


def build_profile_blueprint_prompt(resume_text: str, cover_letters: list[str], notes: list[str]) -> str:
    """
    Step 2 (Profile Blueprint)

    IMPORTANT:
    - We keep this signature (resume_text, cover_letters, notes) for compatibility
      with the current engine/workflow.py call site.
    - Convention:
        cover_letters[0] = Starting cover letter (tone/voice anchor)
        cover_letters[1] = Working cover letter (current draft to critique)
      If only one is provided, we treat it as the Starting cover letter.
    """
    starting_cl = cover_letters[0] if cover_letters and len(cover_letters) >= 1 else ""
    working_cl = cover_letters[1] if cover_letters and len(cover_letters) >= 2 else ""
    extra_cls = cover_letters[2:] if cover_letters and len(cover_letters) > 2 else []

    extra_cl_text = "\n\n".join(extra_cls[:2]) if extra_cls else ""
    notes_text = "\n\n".join(notes[:3]) if notes else ""

    return f"""
Create a Profile Blueprint JSON for Janet based on the materials below.

Return EXACTLY one JSON object.
Do NOT return markdown.
Do NOT return explanations.
Do NOT wrap arrays in objects like {{"list": [...]}}.
For any field described as a list, return a raw JSON array.

ROLE OF EACH INPUT:
1) RESUME = authoritative evidence source. Prefer resume evidence for claims.
2) STARTING COVER LETTER = tone/voice anchor and baseline positioning language.
3) WORKING COVER LETTER = current draft to critique/improve for alignment and effectiveness.
4) NOTES/OTHER = supplemental context and keywords; treat as non-authoritative for claims unless supported by resume.

REQUIRED OUTPUT SHAPE:
{{
  "schema_version": "1.0",
  "artifact_type": "profile_blueprint",
  "created_at": "",
  "run_id": "",
  "candidate_id": "",
  "targeting": {{
    "role_families": [],
    "target_titles": [],
    "avoid_titles": [],
    "constraints": []
  }},
  "strengths": [
    {{
      "theme": "",
      "evidence_chunks": ["", ""]
    }}
  ],
  "tooling_signals": {{
    "strong": [],
    "familiar": [],
    "missing_or_unclear": []
  }},
  "leadership_scope": {{
    "level": "",
    "signals": [],
    "evidence_chunks": []
  }},
  "approved_claims": [
    {{
      "claim_id": "",
      "claim": "",
      "evidence_chunks": ["", ""]
    }}
  ],
  "do_not_claim": [
    {{
      "claim": "",
      "reason": "",
      "suggested_safe_rephrase": ""
    }}
  ],
  "preferred_language": {{
    "keywords": [],
    "phrases": []
  }}
}}

IMPORTANT ARRAY RULES:
- strengths must be a JSON array
- approved_claims must be a JSON array
- do_not_claim must be a JSON array
- role_families, target_titles, avoid_titles, constraints, strong, familiar, missing_or_unclear,
  signals, evidence_chunks, keywords, and phrases must all be plain JSON arrays

GUIDANCE:
- Use the STARTING COVER LETTER to infer tone, structure, and voice.
- Use the WORKING COVER LETTER to:
  (a) identify mismatches vs the resume and likely target roles,
  (b) identify weak or unclear positioning,
  (c) propose stronger, resume-supported positioning language.
- If the WORKING COVER LETTER contains claims not supported by the resume,
  include those in do_not_claim with safe rephrases.
- Keep all claims grounded in the resume.
- Do not invent evidence.

MATERIALS:
[RESUME — AUTHORITATIVE]
{resume_text}

[STARTING COVER LETTER — TONE/VOICE ANCHOR]
{starting_cl}

[WORKING COVER LETTER — DRAFT TO CRITIQUE/IMPROVE]
{working_cl}

[OPTIONAL: OTHER PRIOR COVER LETTER EXCERPTS]
{extra_cl_text}

[NOTES / LINKEDIN / OTHER CONTEXT]
{notes_text}
""".strip()

def build_job_blueprint_prompt(
    job_text: str,
    title: str = "",
    company: str = "",
    location: str = "",
    source: str = "manual",
) -> str:
    return f"""
Create a Job Blueprint JSON from the job description below.

Return EXACTLY one JSON object.
Do NOT return markdown.
Do NOT return explanations.
Do NOT wrap arrays in objects like {{"list": [...]}}.
For any field described as a list, return a raw JSON array.

REQUIRED OUTPUT SHAPE:
{{
  "schema_version": "1.0",
  "artifact_type": "job_blueprint",
  "created_at": "",
  "run_id": "",
  "job_id": "",
  "job_meta": {{
    "title": "{title}",
    "company": "{company}",
    "location": "{location}",
    "url": null,
    "source": "{source}",
    "retrieved_at": ""
  }},
  "role_summary": "",
  "requirements": {{
    "must_have": [],
    "nice_to_have": [],
    "tools_tech": [],
    "domain": []
  }},
  "leadership_scope": {{
    "level": "",
    "team_size_signals": [],
    "cross_functional_signals": []
  }},
  "signals": {{
    "positive": [],
    "negative_or_misalignment": [],
    "red_flags": []
  }},
  "keywords_phrases": [],
  "validation": {{
    "jd_length_ok": true,
    "missing_fields": []
  }}
}}

IMPORTANT ARRAY RULES:
- must_have, nice_to_have, tools_tech, domain must be plain JSON arrays
- team_size_signals and cross_functional_signals must be plain JSON arrays
- positive, negative_or_misalignment, red_flags must be plain JSON arrays
- keywords_phrases and missing_fields must be plain JSON arrays

JOB META (if provided):
title="{title}"
company="{company}"
location="{location}"

[JOB DESCRIPTION]
{job_text}
""".strip()


def build_match_report_prompt(profile_blueprint_json: str, job_blueprint_json: str) -> str:
    return f"""
Compare the Profile Blueprint to the Job Blueprint and produce a Match Report JSON.

Return EXACTLY one JSON object.
Do NOT return markdown.
Do NOT return explanations.
Do NOT wrap arrays in objects like {{"list": [...]}}.
For any field described as a list, return a raw JSON array.

REQUIRED OUTPUT SHAPE:
{{
  "schema_version": "1.0",
  "artifact_type": "match_report",
  "created_at": "",
  "run_id": "",
  "candidate_id": "",
  "job_id": "",
  "overall": {{
    "fit_label": "",
    "fit_score": 0.0,
    "confidence": 0.0,
    "one_sentence_verdict": ""
  }},
  "component_scores": {{
    "title_fit": {{"score": 0.0, "notes": []}},
    "skills_tools_fit": {{"score": 0.0, "notes": []}},
    "leadership_scope_fit": {{"score": 0.0, "notes": []}},
    "domain_fit": {{"score": 0.0, "notes": []}},
    "red_flag_penalty": {{"score": 0.0, "notes": []}}
  }},
  "evidence": [
    {{
      "claim": "",
      "evidence_chunks": ["", ""]
    }}
  ],
  "gaps": [
    {{
      "gap": "",
      "impact": "",
      "recommended_fix": "",
      "suggested_keywords": []
    }}
  ],
  "language_optimization": {{
    "add_keywords": [],
    "replace_phrases": [],
    "tone_guidance": []
  }},
  "guardrails": {{
    "blocked_claims": [],
    "warnings": [],
    "blockers": []
  }},
  "next_actions": [],
  "rubric": {{
    "rubric_version": "1.0",
    "weights_used": null
  }}
}}

IMPORTANT ARRAY RULES:
- evidence must be a JSON array
- gaps must be a JSON array
- notes fields inside component_scores must be JSON arrays
- suggested_keywords must be a JSON array
- add_keywords, replace_phrases, tone_guidance must be JSON arrays
- blocked_claims, warnings, blockers must be JSON arrays
- next_actions must be a JSON array

IMPORTANT CONTENT RULES:
- Ground all claims in the profile blueprint evidence.
- Do not invent unsupported experience.
- If a claim is not supported by profile evidence, include it in guardrails.blocked_claims.
- Keep gap statements concise and action-oriented.
- Keep suggested_keywords as a simple array of strings.
- Keep replace_phrases as a simple array of strings, not a dictionary.
- fit_score must be a number from 0.0 to 1.0
- confidence must be a number from 0.0 to 1.0
- every component_scores.*.score must be a number from 0.0 to 1.0
- do not use 0 to 100 percentages
- do not use text like "High", "Medium", or "Low" for confidence
- fit_label must be one of: "Strong", "Medium", or "Weak"

[PROFILE_BLUEPRINT_JSON]
{profile_blueprint_json}

[JOB_BLUEPRINT_JSON]
{job_blueprint_json}
""".strip()