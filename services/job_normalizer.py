"""
Job Normalizer Service
Transforms heterogeneous job postings from various sources into a uniform, robust schema.
"""

import re
import uuid
from typing import Dict, Any, List


def detect_remote_status(text: str) -> str:
    """Detect whether a job is Remote, Hybrid, or On-site from text content."""
    t_lower = text.lower()
    if any(k in t_lower for k in ["fully remote", "100% remote", "work from home", "wfh", "remote-first"]):
        return "Remote"
    if any(k in t_lower for k in ["hybrid", "partially remote", "flexible working"]):
        return "Hybrid"
    if "remote" in t_lower:
        return "Remote"
    if any(k in t_lower for k in ["on-site", "onsite", "in-office", "in office"]):
        return "On-site"
    return "Unspecified"


def normalize_job(raw_job: Dict[str, Any], default_source: str = "Catalog") -> Dict[str, Any]:
    """Normalize a raw job dictionary into standard schema."""
    # 1. Job ID
    job_id = str(raw_job.get("id") or raw_job.get("job_id") or f"job_{uuid.uuid4().hex[:8]}")

    # 2. Title & Company
    raw_company = raw_job.get("company", {})
    if isinstance(raw_company, dict):
        company = raw_company.get("display_name", "Unknown Company").strip()
    else:
        company = str(raw_company or "Unknown Company").strip()

    title = str(raw_job.get("title") or "Untitled Role").strip()

    # 3. Location
    raw_loc = raw_job.get("location", {})
    if isinstance(raw_loc, dict):
        location = raw_loc.get("display_name", "India").strip()
    else:
        location = str(raw_loc or "India").strip()

    # 4. Description
    description = str(raw_job.get("description") or "").strip()

    # 5. Remote Status
    combined_text = f"{title} {location} {description}"
    remote_status = raw_job.get("remote_status") or detect_remote_status(combined_text)

    # 6. Application URL
    app_url = (
        raw_job.get("application_url")
        or raw_job.get("redirect_url")
        or raw_job.get("url")
        or ""
    ).strip()

    # 7. Salary
    salary_min = raw_job.get("salary_min")
    salary_max = raw_job.get("salary_max")
    salary_str = str(raw_job.get("salary") or "").strip()
    if not salary_str:
        if salary_min and salary_max:
            salary_str = f"₹{int(salary_min):,} - ₹{int(salary_max):,}"
        elif salary_min:
            salary_str = f"From ₹{int(salary_min):,}"
        elif salary_max:
            salary_str = f"Up to ₹{int(salary_max):,}"

    # 8. Posted Date
    posted_date = str(raw_job.get("created") or raw_job.get("posted_date") or "").strip()

    # 9. Source
    source = str(raw_job.get("source") or default_source).strip()

    # 10. Skills
    skills = raw_job.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]

    return {
        "job_id": job_id,
        "id": job_id,
        "title": title,
        "company": company,
        "location": location,
        "remote_status": remote_status,
        "description": description,
        "skills": skills,
        "salary": salary_str,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "posted_date": posted_date,
        "application_url": app_url,
        "source": source,
    }
