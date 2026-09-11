"""
Resumes Database Module
Handles multiple resume storage, versioning, default selection, and metadata per user.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from database.connection import read_json_file, write_json_file
from database.models import ResumeRecord

RESUMES_FILE = "resumes.json"


def _load_all_resumes() -> Dict[str, List[Dict[str, Any]]]:
    """Load all resumes grouped by user_id."""
    return read_json_file(RESUMES_FILE, default={})


def _save_all_resumes(data: Dict[str, List[Dict[str, Any]]]) -> bool:
    """Persist all resumes grouped by user_id."""
    return write_json_file(RESUMES_FILE, data)


def get_resumes(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all resumes for a specific user."""
    user_id = user_id.strip().lower()
    data = _load_all_resumes()
    resumes = data.get(user_id, [])
    # Normalize keys for backwards/flexible compatibility
    for r in resumes:
        if "content" not in r:
            r["content"] = r.get("text", "")
        if "skills" not in r:
            r["skills"] = r.get("parsed_data", {}).get("skills", [])
    return resumes


def get_resume(user_id: str, resume_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific resume by ID for a user."""
    resumes = get_resumes(user_id)
    for r in resumes:
        if r.get("resume_id") == resume_id:
            return r
    return None


def get_default_resume(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the default resume for a user."""
    resumes = get_resumes(user_id)
    if not resumes:
        return None
    for r in resumes:
        if r.get("is_default"):
            return r
    return resumes[0]  # Fallback to first resume


def save_resume(
    user_id: str,
    title: str,
    filename: str,
    text: str,
    score: int = 0,
    parsed_data: Optional[Dict[str, Any]] = None,
    set_default: bool = False
) -> Dict[str, Any]:
    """Save a new resume record for a user."""
    user_id = user_id.strip().lower()
    data = _load_all_resumes()
    user_resumes = data.get(user_id, [])

    resume_id = f"res_{uuid.uuid4().hex[:8]}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # If this is the first resume or set_default is True, make it default
    is_default = set_default or len(user_resumes) == 0

    if is_default:
        for r in user_resumes:
            r["is_default"] = False

    record = ResumeRecord(
        resume_id=resume_id,
        user_id=user_id,
        title=title.strip() or filename or "Resume",
        filename=filename,
        text=text,
        uploaded_at=now_str,
        score=score,
        is_default=is_default,
        parsed_data=parsed_data or {}
    )

    user_resumes.append(record.to_dict())
    data[user_id] = user_resumes
    _save_all_resumes(data)
    result = record.to_dict()
    result["content"] = text
    result["skills"] = parsed_data.get("skills", []) if parsed_data else []
    return result


def create_resume(
    user_id: str,
    title: str,
    content: str,
    skills: Optional[List[str]] = None,
    score: int = 0,
    filename: str = "resume.txt",
    is_default: bool = False
) -> Tuple[bool, str, Dict[str, Any]]:
    """Create a new resume record returning (success, message, record)."""
    try:
        rec = save_resume(
            user_id=user_id,
            title=title,
            filename=filename,
            text=content,
            score=score,
            parsed_data={"skills": skills or []},
            set_default=is_default
        )
        return True, "Resume saved successfully", rec
    except Exception as e:
        return False, str(e), {}


def set_default_resume(user_id: str, resume_id: str) -> bool:
    """Set a specific resume as the user's default."""
    user_id = user_id.strip().lower()
    data = _load_all_resumes()
    user_resumes = data.get(user_id, [])

    found = False
    for r in user_resumes:
        if r.get("resume_id") == resume_id:
            r["is_default"] = True
            found = True
        else:
            r["is_default"] = False

    if found:
        data[user_id] = user_resumes
        return _save_all_resumes(data)
    return False


def update_resume_title(user_id: str, resume_id: str, new_title: str) -> bool:
    """Rename a resume title."""
    user_id = user_id.strip().lower()
    data = _load_all_resumes()
    user_resumes = data.get(user_id, [])

    for r in user_resumes:
        if r.get("resume_id") == resume_id:
            r["title"] = new_title.strip()
            data[user_id] = user_resumes
            return _save_all_resumes(data)
    return False


def delete_resume(user_id: str, resume_id: str) -> bool:
    """Delete a resume for a user."""
    user_id = user_id.strip().lower()
    data = _load_all_resumes()
    user_resumes = data.get(user_id, [])

    initial_len = len(user_resumes)
    user_resumes = [r for r in user_resumes if r.get("resume_id") != resume_id]

    if len(user_resumes) < initial_len:
        # If deleted was default, make first remaining default
        if user_resumes and not any(r.get("is_default") for r in user_resumes):
            user_resumes[0]["is_default"] = True
        data[user_id] = user_resumes
        return _save_all_resumes(data)
    return False
