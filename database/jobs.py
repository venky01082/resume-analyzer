"""
Saved Jobs Database Module
Handles user-specific saved jobs bookmarking, retrieval, and status tracking.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from database.connection import read_json_file, write_json_file
from database.models import SavedJob

SAVED_JOBS_FILE = "saved_jobs.json"


def _load_all_saved_jobs() -> Dict[str, List[Dict[str, Any]]]:
    """Load all saved jobs grouped by user_id."""
    return read_json_file(SAVED_JOBS_FILE, default={})


def _save_all_saved_jobs(data: Dict[str, List[Dict[str, Any]]]) -> bool:
    """Persist all saved jobs grouped by user_id."""
    return write_json_file(SAVED_JOBS_FILE, data)


def get_saved_jobs(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all saved jobs for a specific user."""
    user_id = user_id.strip().lower()
    data = _load_all_saved_jobs()
    return data.get(user_id, [])


def is_job_saved(user_id: str, title: str, company: str) -> bool:
    """Check if a job is already saved by this user."""
    saved = get_saved_jobs(user_id)
    t_clean = title.strip().lower()
    c_clean = company.strip().lower()
    return any(j.get("title", "").strip().lower() == t_clean and j.get("company", "").strip().lower() == c_clean for j in saved)


def save_job(
    user_id: str,
    title_or_dict: Any,
    company: str = "",
    location: str = "India",
    url: str = "",
    score: int = 0,
    salary: str = "",
    description: str = "",
    status: str = "Saved"
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Save a job for a user. Accepts either parameters or a job dict."""
    user_id = user_id.strip().lower()

    if isinstance(title_or_dict, dict):
        d = title_or_dict
        title = d.get("title", "Unknown")
        company = d.get("company", "Unknown")
        location = d.get("location", "India")
        url = d.get("url", "")
        score = d.get("match_score", d.get("score", 0))
        salary = d.get("salary", "")
        description = d.get("description", "")
        status = d.get("status", "Saved")
    else:
        title = str(title_or_dict)

    if is_job_saved(user_id, title, company):
        return False, "Job is already saved in your bookmarks.", None

    data = _load_all_saved_jobs()
    user_jobs = data.get(user_id, [])

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    record = SavedJob(
        job_id=job_id,
        user_id=user_id,
        title=title.strip(),
        company=company.strip(),
        location=location.strip() or "India",
        url=url.strip(),
        score=score,
        salary=salary.strip(),
        saved_at=now_str,
        description=description.strip(),
        status=status
    )

    rec_dict = record.to_dict()
    rec_dict["saved_id"] = job_id  # alias for saved_jobs_ui
    user_jobs.append(rec_dict)
    data[user_id] = user_jobs
    _save_all_saved_jobs(data)
    return True, "Job successfully saved!", rec_dict


def delete_saved_job(user_id: str, job_id: str) -> bool:
    """Remove a saved job for a user."""
    user_id = user_id.strip().lower()
    data = _load_all_saved_jobs()
    user_jobs = data.get(user_id, [])

    initial_len = len(user_jobs)
    user_jobs = [j for j in user_jobs if j.get("job_id") != job_id and j.get("saved_id") != job_id]

    if len(user_jobs) < initial_len:
        data[user_id] = user_jobs
        return _save_all_saved_jobs(data)
    return False


remove_saved_job = delete_saved_job
