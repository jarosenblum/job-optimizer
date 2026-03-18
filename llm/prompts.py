# llm/prompts.py
from __future__ import annotations


def system_json_only() -> str:
    return (
        "You are a careful assistant. "
        "Return ONLY valid JSON. No markdown. No commentary. "
        "Use double quotes for all keys/strings. Do not include trailing commas."
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

ROLE OF EACH INPUT (IMPORTANT):
1) RESUME = authoritative evidence source. Prefer resume evidence for claims.
2) STARTING COVER LETTER = tone/voice anchor and baseline positioning language.
3) WORKING COVER LETTER = current draft to critique/improve for alignment and effectiveness.
4) NOTES/OTHER = supplemental context and keywords; treat as non-authoritative for claims unless supported by resume.

REQUIRED OUTPUT SHAPE (high level):
- schema_version, artifact_type="profile_blueprint", created_at, run_id, candidate_id
- targeting (role_families, target_titles, avoid_titles, constraints)
- strengths (list of themes with evidence_chunks)
- tooling_signals (strong/familiar/missing_or_unclear)
- leadership_scope (level, signals, evidence_chunks)
- approved_claims (each with claim_id, claim, evidence_chunks)
- do_not_claim (claim, reason, suggested_safe_rephrase)
- preferred_language (keywords, phrases)

GUIDANCE:
- Use the STARTING COVER LETTER to infer tone (formal vs warm), structure, and “voice”.
- Use the WORKING COVER LETTER to:
  (a) identify mismatches vs the resume and typical target roles,
  (b) identify weak/unclear positioning,
  (c) propose stronger, resume-supported positioning language.
- If the WORKING COVER LETTER contains claims not supported by the resume,
  incorporate those into do_not_claim with safe rephrases.

MATERIALS:
[RESUME — AUTHORITATIVE]
{resume_text}

[STARTING COVER LETTER — TONE/VOICE ANCHOR]
{starting_cl}

[WORKING COVER LETTER — DRAFT TO CRITIQUE/IMPROVE]
{working_cl}

[OPTIONAL: OTHER PRIOR COVER LETTER EXCERPTS (if any)]
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

REQUIRED OUTPUT SHAPE:
- schema_version, artifact_type="job_blueprint", created_at, run_id, job_id
- job_meta (title, company, location, url=null, source="{source}", retrieved_at)
- role_summary
- requirements (must_have, nice_to_have, tools_tech, domain)
- leadership_scope (level, team_size_signals, cross_functional_signals)
- signals (positive, negative_or_misalignment, red_flags)
- keywords_phrases
- validation (jd_length_ok, missing_fields)

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

REQUIRED OUTPUT SHAPE:
- schema_version, artifact_type="match_report", created_at, run_id, candidate_id, job_id
- overall (fit_label Strong/Medium/Weak, fit_score 0-100, confidence, one_sentence_verdict)
- component_scores: title_fit, skills_tools_fit, leadership_scope_fit, domain_fit, red_flag_penalty (each score 0-100 + notes)
- evidence: list of claim/evidence mappings (include resume chunk references when possible)
- gaps: list with impact + recommended_fix + suggested_keywords
- language_optimization: add_keywords, replace_phrases, tone_guidance
- guardrails: blocked_claims, warnings, blockers
- next_actions
- rubric: rubric_version, weights_used=null

IMPORTANT GUARDRAIL:
- If a claim is not supported by profile evidence, include it in guardrails.blocked_claims with a safe rephrase.

[PROFILE_BLUEPRINT_JSON]
{profile_blueprint_json}

[JOB_BLUEPRINT_JSON]
{job_blueprint_json}
""".strip()