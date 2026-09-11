"""
AI Job Recommendation Service
Calculates multi-factor candidate-job fit scores and generates transparent match explanations.
"""

import re
from typing import List, Dict, Any, Optional, Tuple

from core_logic import extract_job_skills, compare_skills, calculate_semantic_similarity
from database.repository import get_user_profile, get_user_preferences, get_default_resume, get_saved_jobs, get_applications


def calculate_job_recommendation_score(
    job: Dict[str, Any],
    candidate_skills: List[str],
    target_roles: str = "",
    preferred_locations: str = "India",
    work_preference: str = "Any",
    years_experience: float = 0.0,
    resume_text: str = ""
) -> Tuple[int, Dict[str, Any]]:
    """
    Computes a transparent multi-factor Job Recommendation Score (0-100)
    and generates detailed fit explanations.
    """
    title = job.get("title", "")
    description = job.get("description", "")
    location = job.get("location", "")
    remote_status = job.get("remote_status", "Unspecified")

    job_text = f"{title} {description}"
    job_skills = extract_job_skills(job_text)
    matching_skills, missing_skills = compare_skills(candidate_skills, job_skills)

    # 1. Skill Match Component (40% weight)
    if job_skills:
        skill_score = (len(matching_skills) / len(job_skills)) * 100
    else:
        skill_score = 60.0  # neutral default

    # 2. Target Role Alignment (25% weight)
    role_score = 40.0
    if target_roles:
        target_tokens = [t.strip().lower() for t in re.split(r"[,/|]", target_roles) if t.strip()]
        title_lower = title.lower()
        if any(tok in title_lower for tok in target_tokens):
            role_score = 95.0
        elif any(any(word in title_lower for word in tok.split()) for tok in target_tokens):
            role_score = 75.0

    # 3. Location & Work Mode Compatibility (15% weight)
    loc_score = 70.0
    p_loc = preferred_locations.lower()
    if p_loc and (p_loc in location.lower() or "india" in location.lower()):
        loc_score = 90.0
    if work_preference.lower() == "remote" and remote_status.lower() == "remote":
        loc_score = 100.0

    # 4. Semantic Content Similarity (20% weight)
    if resume_text:
        sim_score = calculate_semantic_similarity(resume_text, job_text)
    else:
        sim_score = skill_score

    # Weighted Composite Score
    composite_score = int(round(
        (0.40 * skill_score) +
        (0.25 * role_score) +
        (0.15 * loc_score) +
        (0.20 * sim_score)
    ))
    composite_score = max(10, min(99, composite_score))

    # Transparent Explanations
    why_match = []
    if matching_skills:
        top_matching = ", ".join(matching_skills[:5])
        why_match.append(f"Strong skill match on key requirements: {top_matching}.")
    if role_score >= 75:
        why_match.append(f"Job title '{title}' closely aligns with your target roles.")
    if loc_score >= 85:
        why_match.append(f"Location '{location}' matches your geographic preference.")

    what_is_missing = []
    if missing_skills:
        top_missing = ", ".join(missing_skills[:4])
        what_is_missing.append(f"Missing desired skills: {top_missing}.")
    if not missing_skills and not matching_skills:
        what_is_missing.append("General job description with limited specific technical requirements.")

    return composite_score, {
        "score": composite_score,
        "skill_score": round(skill_score, 1),
        "role_score": round(role_score, 1),
        "location_score": round(loc_score, 1),
        "semantic_score": round(sim_score, 1),
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "why_match": why_match,
        "what_is_missing": what_is_missing,
    }


def recommend_jobs_for_user(
    user_id: str,
    available_jobs: List[Dict[str, Any]],
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Ranks a list of jobs specifically for the authenticated user,
    combining profile preferences, resume skills, and application history.
    """
    profile = get_user_profile(user_id)
    prefs = get_user_preferences(user_id)
    default_res = get_default_resume(user_id)

    # Compile candidate skills from resume and profile
    candidate_skills = []
    if default_res:
        candidate_skills.extend(default_res.get("skills", []))
    prof_skills = profile.get("technical_skills") or profile.get("skills", "")
    if prof_skills:
        candidate_skills.extend([s.strip().lower() for s in re.split(r"[,;\n]", prof_skills) if s.strip()])
    candidate_skills = list(dict.fromkeys(candidate_skills))

    target_roles = profile.get("target_roles") or prefs.get("preferred_roles", "")
    preferred_loc = profile.get("preferred_locations") or prefs.get("preferred_locations", "India")
    work_pref = profile.get("work_mode_preference") or prefs.get("work_preference", "Any")
    years_exp = float(profile.get("years_of_experience", 0.0) or 0.0)
    resume_text = default_res.get("text", "") if default_res else ""

    scored_jobs = []
    for job in available_jobs:
        score, explanation = calculate_job_recommendation_score(
            job=job,
            candidate_skills=candidate_skills,
            target_roles=target_roles,
            preferred_locations=preferred_loc,
            work_preference=work_pref,
            years_experience=years_exp,
            resume_text=resume_text
        )
        scored_jobs.append({
            "job": job,
            "score": score,
            "explanation": explanation
        })

    scored_jobs.sort(key=lambda x: x["score"], reverse=True)
    return scored_jobs[:limit]
