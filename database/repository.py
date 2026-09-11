"""
Unified Database Repository Module
Provides strictly isolated, parameterized data-access operations across
PostgreSQL / Supabase and local SQLite databases.
"""

import os
import json
import uuid
import base64
import hashlib
import secrets
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple

from database.connection import execute_query, execute_mutation, get_db_connection
from database.models import (
    UserProfile,
    UserPreferences,
    ResumeRecord,
    SavedJob,
    ApplicationRecord,
    StatusHistoryEntry,
    GeneratedDocument,
    STATUS_OPTIONS,
    PRIORITY_OPTIONS
)
from database.migrations import init_db

# Initialize database schema and run migrations once on module import
_initialized = False
if not _initialized:
    init_db()
    _initialized = True


# =========================================================
# 1. USER AUTHENTICATION & CREDENTIALS
# =========================================================

def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Generate salted PBKDF2 HMAC SHA-256 password hash (200,000 iterations)."""
    if not salt:
        salt_bytes = secrets.token_bytes(16)
    else:
        salt_bytes = base64.b64decode(salt.encode("utf-8"))
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 200_000)
    salt_str = base64.b64encode(salt_bytes).decode("utf-8")
    hash_str = base64.b64encode(key).decode("utf-8")
    return salt_str, hash_str


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """Verify password against stored salt and hash with timing-attack prevention."""
    if not salt or not password_hash:
        return False
    _, test_hash = hash_password(password, salt)
    return secrets.compare_digest(test_hash, password_hash)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Validate password strength (min 8 chars, uppercase, lowercase, digit, special char)."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must include at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must include at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must include at least one number."
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Password must include at least one special character (!@#$%^&* etc.)."
    return True, "Strong password."


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Retrieve user record by username."""
    u_clean = username.strip().lower()
    rows = execute_query("SELECT * FROM users WHERE username = ?", (u_clean,))
    if not rows:
        return None
    user_row = rows[0]
    # Fetch associated profile and preferences
    user_row["profile"] = get_user_profile(u_clean)
    user_row["preferences"] = get_user_preferences(u_clean)
    return user_row


get_user = get_user_by_username


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve user record by email address."""
    e_clean = email.strip().lower()
    if not e_clean:
        return None
    rows = execute_query("SELECT * FROM users WHERE LOWER(email) = ?", (e_clean,))
    if not rows:
        return None
    user_row = rows[0]
    username = user_row["username"]
    user_row["profile"] = get_user_profile(username)
    user_row["preferences"] = get_user_preferences(username)
    return user_row


def create_user(
    username: str,
    password: str,
    full_name: str = "",
    email: str = "",
    target_roles: str = ""
) -> Tuple[bool, str]:
    """Create a new user with secure password hash, profile, and preferences."""
    username = username.strip().lower()
    email = email.strip().lower()
    full_name = full_name.strip()
    target_roles = target_roles.strip()

    if not username:
        return False, "Username cannot be empty."
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if not username.isalnum() and "_" not in username:
        return False, "Username can only contain letters, numbers, and underscores."

    # Validate password strength
    ok_pwd, pwd_msg = validate_password_strength(password)
    if not ok_pwd:
        return False, pwd_msg

    # Check for existing username
    if get_user_by_username(username):
        return False, f"Username '{username}' is already taken."

    # Check for duplicate email
    if email and get_user_by_email(email):
        return False, f"An account with email '{email}' already exists."

    salt, p_hash = hash_password(password)
    now_str = datetime.now().isoformat()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_salt, password_hash, email, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, salt, p_hash, email, now_str)
        )
        cursor.execute("""
            INSERT INTO profiles (
                username, full_name, email, target_roles, technical_skills, preferred_locations
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (username, full_name, email, target_roles, "", "India"))
        cursor.execute("""
            INSERT INTO preferences (
                username, preferred_roles, preferred_locations, work_preference
            ) VALUES (?, ?, ?, ?)
        """, (username, target_roles, "India", "Any"))

    return True, "Account created successfully."


def verify_user_credentials(username: str, password: str) -> bool:
    """Verify username and password against stored PBKDF2 hash."""
    user = get_user_by_username(username)
    if not user:
        return False
    return verify_password(password, user.get("password_salt", ""), user.get("password_hash", ""))


def update_user_password(username: str, new_password: str) -> Tuple[bool, str]:
    """Update user password with strength validation."""
    username = username.strip().lower()
    ok_pwd, pwd_msg = validate_password_strength(new_password)
    if not ok_pwd:
        return False, pwd_msg

    salt, p_hash = hash_password(new_password)
    count = execute_mutation(
        "UPDATE users SET password_salt = ?, password_hash = ? WHERE username = ?",
        (salt, p_hash, username)
    )
    if count > 0:
        return True, "Password updated successfully."
    return False, "User not found."


def delete_user_account(username: str) -> bool:
    """Delete a user account and cascade delete all user-owned data."""
    username = username.strip().lower()
    count = execute_mutation("DELETE FROM users WHERE username = ?", (username,))
    # Explicit cleanup for SQLite without foreign keys enabled
    execute_mutation("DELETE FROM profiles WHERE username = ?", (username,))
    execute_mutation("DELETE FROM preferences WHERE username = ?", (username,))
    execute_mutation("DELETE FROM resumes WHERE user_id = ?", (username,))
    execute_mutation("DELETE FROM saved_jobs WHERE user_id = ?", (username,))
    execute_mutation("DELETE FROM applications WHERE user_id = ?", (username,))
    execute_mutation("DELETE FROM application_status_history WHERE user_id = ?", (username,))
    execute_mutation("DELETE FROM generated_documents WHERE user_id = ?", (username,))
    execute_mutation("DELETE FROM interview_reports WHERE user_id = ?", (username,))
    execute_mutation("DELETE FROM interview_evaluations WHERE user_id = ?", (username,))
    execute_mutation("DELETE FROM interview_answers WHERE user_id = ?", (username,))
    execute_mutation("DELETE FROM interview_questions WHERE user_id = ?", (username,))
    execute_mutation("DELETE FROM interview_sessions WHERE user_id = ?", (username,))
    return count > 0


# =========================================================
# 2. USER PROFILE & PREFERENCES
# =========================================================

def get_user_profile(username: str) -> Dict[str, Any]:
    """Retrieve full UserProfile for a user."""
    username = username.strip().lower()
    rows = execute_query("SELECT * FROM profiles WHERE username = ?", (username,))
    if not rows:
        return UserProfile().to_dict()
    row = dict(rows[0])
    row.pop("username", None)
    return UserProfile.from_dict(row).to_dict()


def auth_get_profile(username: str) -> Dict[str, Any]:
    """
    Retrieve the authenticated user's profile with strict user isolation.
    Backward-compatible alias for get_user_profile.
    """
    return get_user_profile(username)


def update_user_profile(username: str, profile_data: Dict[str, Any]) -> bool:
    """Update UserProfile fields for a user."""
    username = username.strip().lower()
    current = get_user_profile(username)
    current.update(profile_data)
    prof = UserProfile.from_dict(current)

    count = execute_mutation("""
        INSERT INTO profiles (
            username, full_name, email, phone, location, professional_title,
            target_roles, preferred_locations, work_mode_preference, years_of_experience,
            skills, technical_skills, soft_skills, education, certifications,
            preferred_industries, expected_salary, notice_period, work_authorization,
            linkedin, github, portfolio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
            full_name=excluded.full_name,
            email=excluded.email,
            phone=excluded.phone,
            location=excluded.location,
            professional_title=excluded.professional_title,
            target_roles=excluded.target_roles,
            preferred_locations=excluded.preferred_locations,
            work_mode_preference=excluded.work_mode_preference,
            years_of_experience=excluded.years_of_experience,
            skills=excluded.skills,
            technical_skills=excluded.technical_skills,
            soft_skills=excluded.soft_skills,
            education=excluded.education,
            certifications=excluded.certifications,
            preferred_industries=excluded.preferred_industries,
            expected_salary=excluded.expected_salary,
            notice_period=excluded.notice_period,
            work_authorization=excluded.work_authorization,
            linkedin=excluded.linkedin,
            github=excluded.github,
            portfolio=excluded.portfolio
    """, (
        username, prof.full_name, prof.email, prof.phone, prof.location, prof.professional_title,
        prof.target_roles, prof.preferred_locations, prof.work_mode_preference, prof.years_of_experience,
        prof.skills, prof.technical_skills, prof.soft_skills, prof.education, prof.certifications,
        prof.preferred_industries, prof.expected_salary, prof.notice_period, prof.work_authorization,
        prof.linkedin, prof.github, prof.portfolio
    ))

    # Keep users.email in sync
    if prof.email:
        execute_mutation("UPDATE users SET email = ? WHERE username = ?", (prof.email.strip().lower(), username))

    return count > 0


def get_user_preferences(username: str) -> Dict[str, Any]:
    """Retrieve UserPreferences for a user."""
    username = username.strip().lower()
    rows = execute_query("SELECT * FROM preferences WHERE username = ?", (username,))
    if not rows:
        return UserPreferences().to_dict()
    row = dict(rows[0])
    row.pop("username", None)
    return UserPreferences.from_dict(row).to_dict()


def update_user_preferences(username: str, prefs_data: Dict[str, Any]) -> bool:
    """Update UserPreferences fields for a user."""
    username = username.strip().lower()
    current = get_user_preferences(username)
    current.update(prefs_data)
    prefs = UserPreferences.from_dict(current)

    count = execute_mutation("""
        INSERT INTO preferences (
            username, preferred_roles, preferred_locations, work_preference,
            default_cover_letter_tone, default_email_length, default_resume_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
            preferred_roles=excluded.preferred_roles,
            preferred_locations=excluded.preferred_locations,
            work_preference=excluded.work_preference,
            default_cover_letter_tone=excluded.default_cover_letter_tone,
            default_email_length=excluded.default_email_length,
            default_resume_id=excluded.default_resume_id
    """, (
        username, prefs.preferred_roles, prefs.preferred_locations, prefs.work_preference,
        prefs.default_cover_letter_tone, prefs.default_email_length, prefs.default_resume_id
    ))
    return count > 0


# =========================================================
# 3. MULTI-RESUME REPOSITORY
# =========================================================

def get_resumes(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all resumes owned by a user."""
    user_id = user_id.strip().lower()
    rows = execute_query("SELECT * FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC", (user_id,))
    resumes = []
    for r in rows:
        item = dict(r)
        # Parse JSON parsed_data
        try:
            item["parsed_data"] = json.loads(item.get("parsed_data") or "{}")
        except Exception:
            item["parsed_data"] = {}
        item["is_default"] = bool(item.get("is_default"))
        item["content"] = item.get("text", "")
        item["skills"] = item.get("parsed_data", {}).get("skills", [])
        resumes.append(item)
    return resumes


def get_resume(user_id: str, resume_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific resume owned by a user."""
    user_id = user_id.strip().lower()
    rows = execute_query("SELECT * FROM resumes WHERE user_id = ? AND resume_id = ?", (user_id, resume_id))
    if not rows:
        return None
    item = dict(rows[0])
    try:
        item["parsed_data"] = json.loads(item.get("parsed_data") or "{}")
    except Exception:
        item["parsed_data"] = {}
    item["is_default"] = bool(item.get("is_default"))
    item["content"] = item.get("text", "")
    item["skills"] = item.get("parsed_data", {}).get("skills", [])
    return item


def get_default_resume(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the primary default resume for a user."""
    resumes = get_resumes(user_id)
    if not resumes:
        return None
    for r in resumes:
        if r.get("is_default"):
            return r
    return resumes[0]


class ResumeSaveResult(dict):
    """
    Dual-interface return object for save_resume:
    - Dict interface: record.get("text"), record["resume_id"], etc. for UI callers.
    - Tuple unpacking: ok, resume_id = save_resume(...) for test & script callers.
    - Truthiness: bool(record) evaluates to True if saved, False on failure.
    """
    def __iter__(self):
        yield self.get("success", False)
        yield self.get("resume_id", "")

    def __bool__(self):
        return bool(self.get("success", False))


def save_resume(
    user_id: str,
    title: str,
    filename: str,
    text: str = "",
    score: int = 0,
    parsed_data: Optional[Dict[str, Any]] = None,
    is_default: bool = False,
    set_default: Optional[bool] = None,
    content: Optional[str] = None,
    **kwargs
) -> ResumeSaveResult:
    """Save or update a resume record in database with full backward compatibility."""
    user_id = user_id.strip().lower()
    resume_id = f"res_{uuid.uuid4().hex[:10]}"
    uploaded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Resolve text / content alias
    actual_text = content if (content is not None and not text) else text

    # Resolve set_default / is_default alias
    actual_default = bool(set_default) if set_default is not None else bool(is_default)

    parsed_dict = parsed_data or {}
    parsed_json = json.dumps(parsed_dict)

    # If first resume or requested default, reset others
    resumes = get_resumes(user_id)
    if actual_default or len(resumes) == 0:
        execute_mutation("UPDATE resumes SET is_default = 0 WHERE user_id = ?", (user_id,))
        is_def_val = 1
    else:
        is_def_val = 0

    count = execute_mutation("""
        INSERT INTO resumes (resume_id, user_id, title, filename, text, uploaded_at, score, is_default, parsed_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (resume_id, user_id, title, filename, actual_text, uploaded_at, int(score), is_def_val, parsed_json))

    if count > 0:
        return ResumeSaveResult({
            "success": True,
            "resume_id": resume_id,
            "user_id": user_id,
            "title": title.strip() or filename or "Resume",
            "filename": filename,
            "text": actual_text,
            "uploaded_at": uploaded_at,
            "score": int(score),
            "is_default": bool(is_def_val),
            "parsed_data": parsed_dict,
            "content": actual_text,
            "skills": parsed_dict.get("skills", [])
        })

    return ResumeSaveResult({
        "success": False,
        "resume_id": "",
        "user_id": user_id,
        "title": title,
        "filename": filename,
        "text": actual_text,
        "uploaded_at": uploaded_at,
        "score": int(score),
        "is_default": False,
        "parsed_data": parsed_dict,
        "content": actual_text,
        "skills": []
    })


def create_resume(
    user_id: str,
    title: str,
    content: str = "",
    skills: Optional[List[str]] = None,
    score: int = 0,
    filename: str = "resume.txt",
    is_default: bool = False,
    text: Optional[str] = None,
    parsed_data: Optional[Dict[str, Any]] = None,
    set_default: Optional[bool] = None,
    **kwargs
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Create a new resume record returning (success, message, record_dict).
    Compatible with ui/tailoring_ui.py and callers expecting a 3-element sequence.
    """
    resume_text = text if text is not None else content
    p_data = dict(parsed_data or {})
    if skills and "skills" not in p_data:
        p_data["skills"] = skills

    rec = save_resume(
        user_id=user_id,
        title=title,
        filename=filename,
        text=resume_text,
        score=score,
        parsed_data=p_data,
        is_default=is_default,
        set_default=set_default,
        **kwargs
    )
    if rec.get("success"):
        return True, "Resume saved successfully", rec
    return False, "Failed to save resume", rec


def set_default_resume(user_id: str, resume_id: str) -> bool:
    """Set a specific resume as default for the user."""
    user_id = user_id.strip().lower()
    execute_mutation("UPDATE resumes SET is_default = 0 WHERE user_id = ?", (user_id,))
    count = execute_mutation("UPDATE resumes SET is_default = 1 WHERE user_id = ? AND resume_id = ?", (user_id, resume_id))
    return count > 0


def delete_resume(user_id: str, resume_id: str) -> bool:
    """Delete a resume owned by a user."""
    user_id = user_id.strip().lower()
    count = execute_mutation("DELETE FROM resumes WHERE user_id = ? AND resume_id = ?", (user_id, resume_id))
    # If the default was deleted, promote another if available
    resumes = get_resumes(user_id)
    if resumes and not any(r.get("is_default") for r in resumes):
        execute_mutation("UPDATE resumes SET is_default = 1 WHERE user_id = ? AND resume_id = ?", (user_id, resumes[0]["resume_id"]))
    return count > 0


def update_resume_title(user_id: str, resume_id: str, new_title: str) -> bool:
    """
    Update only the title of a resume owned by user_id with strict user isolation.
    Preserves all resume text, metadata, parsed data, and default status.
    """
    user_id = user_id.strip().lower()
    resume_id = resume_id.strip()
    new_title = new_title.strip()
    if not new_title or not resume_id:
        return False
    count = execute_mutation(
        "UPDATE resumes SET title = ? WHERE user_id = ? AND resume_id = ?",
        (new_title, user_id, resume_id)
    )
    return count > 0


# =========================================================
# 4. SAVED JOBS (BOOKMARKS) REPOSITORY
# =========================================================

def get_saved_jobs(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all bookmarked jobs for a user."""
    user_id = user_id.strip().lower()
    rows = execute_query("SELECT * FROM saved_jobs WHERE user_id = ? ORDER BY saved_at DESC", (user_id,))
    return [dict(r) for r in rows]


def is_job_saved(user_id: str, title: str, company: str) -> bool:
    """Check if a job is already bookmarked by a user."""
    user_id = user_id.strip().lower()
    t_clean = title.strip().lower()
    c_clean = company.strip().lower()
    rows = execute_query(
        "SELECT job_id FROM saved_jobs WHERE user_id = ? AND LOWER(title) = ? AND LOWER(company) = ?",
        (user_id, t_clean, c_clean)
    )
    return len(rows) > 0


def save_job(
    user_id: str,
    title_or_dict: Any,
    company: str = "",
    location: str = "India",
    url: str = "",
    score: int = 0,
    salary: str = "",
    description: str = "",
    notes: str = "",
    priority: str = "Medium",
    tags: str = ""
) -> Tuple[bool, str]:
    """Save a job opportunity to the user's bookmarks catalog."""
    user_id = user_id.strip().lower()

    if isinstance(title_or_dict, dict):
        d = title_or_dict
        title = d.get("title", "Untitled Position")
        company = d.get("company", company or "Unknown Company")
        location = d.get("location", location)
        url = d.get("application_url", d.get("url", url))
        score = d.get("score", score)
        salary = d.get("salary", salary)
        description = d.get("description", description)
        notes = d.get("notes", notes)
        priority = d.get("priority", priority)
        tags = d.get("tags", tags)
    else:
        title = str(title_or_dict)

    if is_job_saved(user_id, title, company):
        return False, "Job is already in your saved bookmarks."

    job_id = f"job_{uuid.uuid4().hex[:10]}"
    saved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    count = execute_mutation("""
        INSERT INTO saved_jobs (job_id, user_id, title, company, location, url, score, salary, saved_at, description, status, notes, priority, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (job_id, user_id, title, company, location, url, int(score), salary, saved_at, description, "Saved", notes, priority, tags))

    if count > 0:
        return True, "Job bookmarked successfully!"
    return False, "Failed to bookmark job."


def remove_saved_job(user_id: str, job_id: str) -> bool:
    """Remove a bookmarked job for a user."""
    user_id = user_id.strip().lower()
    count = execute_mutation("DELETE FROM saved_jobs WHERE user_id = ? AND job_id = ?", (user_id, job_id))
    return count > 0


delete_saved_job = remove_saved_job


def update_saved_job_notes(user_id: str, job_id: str, notes: str, priority: str = "Medium") -> bool:
    """Update user notes and priority on a saved job."""
    user_id = user_id.strip().lower()
    count = execute_mutation(
        "UPDATE saved_jobs SET notes = ?, priority = ? WHERE user_id = ? AND job_id = ?",
        (notes, priority, user_id, job_id)
    )
    return count > 0


# =========================================================
# 5. APPLICATIONS CRM REPOSITORY (10-STAGE LIFECYCLE)
# =========================================================

def get_applications(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all tracked applications for a user."""
    user_id = user_id.strip().lower()
    rows = execute_query("SELECT * FROM applications WHERE user_id = ? ORDER BY last_updated DESC", (user_id,))
    return [dict(r) for r in rows]


def get_application(user_id: str, app_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single application record for a user."""
    user_id = user_id.strip().lower()
    rows = execute_query("SELECT * FROM applications WHERE user_id = ? AND app_id = ?", (user_id, app_id))
    if not rows:
        return None
    return dict(rows[0])


def create_application(
    user_id: str,
    title: str = "",
    company: str = "",
    location: str = "India",
    score: int = 0,
    application_url: str = "",
    status: str = "Applied",
    priority: str = "Medium",
    applied_date: str = "",
    follow_up_date: str = "",
    notes: str = "",
    contact_name: str = "",
    contact_email: str = "",
    salary: str = "",
    source: str = "",
    job_description: str = "",
    resume_used: str = "",
    cover_letter_used: str = "",
    next_action: str = "",
    job_title: Optional[str] = None,
    resume_version: Optional[str] = None,
    **kwargs
) -> Tuple[bool, str]:
    """Create a new tracked application record with initial status history."""
    user_id = user_id.strip().lower()
    actual_title = (job_title if job_title is not None else title).strip()
    actual_company = company.strip()
    actual_resume_used = (resume_version if resume_version is not None else resume_used).strip()

    if not actual_title or not actual_company:
        return False, "Job title and Company name are required."

    if status not in STATUS_OPTIONS:
        status = "Applied"
    if priority not in PRIORITY_OPTIONS:
        priority = "Medium"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not applied_date:
        applied_date = datetime.now().strftime("%Y-%m-%d")

    app_id = f"app_{uuid.uuid4().hex[:8]}"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applications (
                app_id, user_id, title, company, location, score, application_url,
                status, priority, applied_date, follow_up_date, last_updated,
                notes, contact_name, contact_email, salary, source, job_description,
                resume_used, cover_letter_used, next_action
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app_id, user_id, actual_title, actual_company, location, int(score), application_url,
            status, priority, applied_date, follow_up_date, now_str,
            notes, contact_name, contact_email, salary, source, job_description,
            actual_resume_used, cover_letter_used, next_action
        ))

        # Log initial status history
        hist_id = f"hist_{uuid.uuid4().hex[:8]}"
        cursor.execute("""
            INSERT INTO application_status_history (history_id, app_id, user_id, status, changed_at, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (hist_id, app_id, user_id, status, now_str, f"Application registered with status '{status}'."))

    return True, app_id


def update_application(
    user_id: str,
    app_id_or_index: Any = None,
    updates: Optional[Dict[str, Any]] = None,
    **kwargs
) -> bool:
    """Update fields on an application record and record status history if changed."""
    user_id = user_id.strip().lower()
    all_updates = {}
    if updates and isinstance(updates, dict):
        all_updates.update(updates)
    all_updates.update(kwargs)

    # Allow app_id_or_index to be passed as 'identifier' or 'app_id' in kwargs
    if app_id_or_index is None:
        app_id_or_index = all_updates.pop("identifier", None) or all_updates.pop("app_id", None)

    if not all_updates and app_id_or_index is None:
        return False

    # Resolve app_id
    app_id = None
    if isinstance(app_id_or_index, str):
        app_id = app_id_or_index
    elif isinstance(app_id_or_index, int):
        apps = get_applications(user_id)
        if 0 <= app_id_or_index < len(apps):
            app_id = apps[app_id_or_index]["app_id"]

    if not app_id:
        return False

    existing = get_application(user_id, app_id)
    if not existing:
        return False

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_updates["last_updated"] = now_str

    old_status = existing.get("status")
    new_status = all_updates.get("status", old_status)

    # Build parameterized UPDATE statement
    set_clauses = []
    params = []
    for k, v in all_updates.items():
        if k in [
            "title", "company", "location", "score", "application_url", "status",
            "priority", "applied_date", "follow_up_date", "last_updated", "notes",
            "contact_name", "contact_email", "salary", "source", "job_description",
            "resume_used", "cover_letter_used", "next_action"
        ]:
            set_clauses.append(f"{k} = ?")
            params.append(v)

    if not set_clauses:
        return False

    params.extend([user_id, app_id])
    sql = f"UPDATE applications SET {', '.join(set_clauses)} WHERE user_id = ? AND app_id = ?"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))

        # If status changed, append to status history
        if new_status != old_status:
            hist_id = f"hist_{uuid.uuid4().hex[:8]}"
            status_note = all_updates.get("notes") or f"Status transitioned from '{old_status}' to '{new_status}'."
            cursor.execute("""
                INSERT INTO application_status_history (history_id, app_id, user_id, status, changed_at, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (hist_id, app_id, user_id, new_status, now_str, status_note))

    return True


def delete_application(user_id: str, app_id_or_index: Any = None, **kwargs) -> bool:
    """Delete an application record and its history."""
    user_id = user_id.strip().lower()
    if app_id_or_index is None:
        app_id_or_index = kwargs.get("identifier") or kwargs.get("app_id")

    app_id = None
    if isinstance(app_id_or_index, str):
        app_id = app_id_or_index
    elif isinstance(app_id_or_index, int):
        apps = get_applications(user_id)
        if 0 <= app_id_or_index < len(apps):
            app_id = apps[app_id_or_index]["app_id"]

    if not app_id:
        return False

    execute_mutation("DELETE FROM application_status_history WHERE user_id = ? AND app_id = ?", (user_id, app_id))
    count = execute_mutation("DELETE FROM applications WHERE user_id = ? AND app_id = ?", (user_id, app_id))
    return count > 0


def get_status_history(user_id: str, app_id: str) -> List[Dict[str, Any]]:
    """Retrieve chronological status history for an application."""
    user_id = user_id.strip().lower()
    rows = execute_query(
        "SELECT * FROM application_status_history WHERE user_id = ? AND app_id = ? ORDER BY changed_at ASC",
        (user_id, app_id)
    )
    return [dict(r) for r in rows]


def get_status_counts(user_id_or_apps: Any) -> Dict[str, int]:
    """Retrieve count of applications per pipeline status. Accepts user_id or list of apps."""
    counts = {s: 0 for s in STATUS_OPTIONS}
    if isinstance(user_id_or_apps, list):
        apps = user_id_or_apps
    else:
        apps = get_applications(str(user_id_or_apps))
    for a in apps:
        st_val = a.get("status", "Applied")
        if st_val in counts:
            counts[st_val] += 1
        else:
            counts[st_val] = counts.get(st_val, 0) + 1
    return counts


def get_overdue_follow_ups(user_id_or_apps: Any, reference_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve applications with overdue follow-ups. Accepts user_id or list of apps."""
    try:
        ref_dt = date.fromisoformat(reference_date) if reference_date else date.today()
    except (ValueError, TypeError):
        ref_dt = date.today()
    ref_iso = ref_dt.isoformat()

    if isinstance(user_id_or_apps, list):
        apps = user_id_or_apps
    else:
        apps = get_applications(str(user_id_or_apps))
    overdue = []
    for a in apps:
        if not isinstance(a, dict):
            continue
        raw_f_date = a.get("follow_up_date")
        if not raw_f_date or not isinstance(raw_f_date, str):
            continue
        f_date_str = raw_f_date.strip()
        if not f_date_str:
            continue
        try:
            parsed_d = date.fromisoformat(f_date_str.split()[0].split("T")[0])
            app_iso = parsed_d.isoformat()
        except (ValueError, TypeError):
            continue

        status = a.get("status", "")
        if status in ("Offer", "Rejected", "Withdrawn"):
            continue

        if app_iso < ref_iso:
            overdue.append(a)
    return overdue


def get_today_follow_ups(user_id_or_apps: Any, reference_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve applications with follow-ups scheduled for today. Accepts user_id or list of apps."""
    try:
        ref_dt = date.fromisoformat(reference_date) if reference_date else date.today()
    except (ValueError, TypeError):
        ref_dt = date.today()
    ref_iso = ref_dt.isoformat()

    if isinstance(user_id_or_apps, list):
        apps = user_id_or_apps
    else:
        apps = get_applications(str(user_id_or_apps))
    today_list = []
    for a in apps:
        if not isinstance(a, dict):
            continue
        raw_f_date = a.get("follow_up_date")
        if not raw_f_date or not isinstance(raw_f_date, str):
            continue
        f_date_str = raw_f_date.strip()
        if not f_date_str:
            continue
        try:
            parsed_d = date.fromisoformat(f_date_str.split()[0].split("T")[0])
            app_iso = parsed_d.isoformat()
        except (ValueError, TypeError):
            continue

        status = a.get("status", "")
        if status in ("Offer", "Rejected", "Withdrawn"):
            continue

        if app_iso == ref_iso:
            today_list.append(a)
    return today_list


def get_upcoming_follow_ups(
    user_id_or_apps: Any,
    reference_date: Optional[str] = None,
    days_ahead: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve applications with future follow-ups scheduled.
    Supports both user_id string or pre-fetched list of applications.
    Accepts reference_date (default today) and optional days_ahead window (e.g. days_ahead=14).
    """
    try:
        ref_dt = date.fromisoformat(reference_date) if reference_date else date.today()
    except (ValueError, TypeError):
        ref_dt = date.today()
    ref_iso = ref_dt.isoformat()

    max_iso = None
    if days_ahead is not None:
        try:
            max_iso = (ref_dt + timedelta(days=int(days_ahead))).isoformat()
        except (ValueError, TypeError):
            max_iso = None

    if isinstance(user_id_or_apps, list):
        apps = user_id_or_apps
    else:
        apps = get_applications(str(user_id_or_apps))

    upcoming = []
    for a in apps:
        if not isinstance(a, dict):
            continue
        raw_f_date = a.get("follow_up_date")
        if not raw_f_date or not isinstance(raw_f_date, str):
            continue
        f_date_str = raw_f_date.strip()
        if not f_date_str:
            continue

        # Parse date defensively
        try:
            parsed_d = date.fromisoformat(f_date_str.split()[0].split("T")[0])
            app_iso = parsed_d.isoformat()
        except (ValueError, TypeError):
            continue

        status = a.get("status", "")
        if status in ("Offer", "Rejected", "Withdrawn"):
            continue

        # Must be strictly in the future
        if app_iso > ref_iso:
            if max_iso is not None:
                if app_iso <= max_iso:
                    upcoming.append(a)
            else:
                upcoming.append(a)

    return upcoming


# =========================================================
# 6. GENERATED DOCUMENTS REPOSITORY
# =========================================================

def save_generated_document(
    user_id: str,
    doc_type: str,
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str]:
    """Save a generated document (tailored resume, cover letter, email)."""
    user_id = user_id.strip().lower()
    doc_id = f"doc_{uuid.uuid4().hex[:10]}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_json = json.dumps(metadata or {})

    count = execute_mutation("""
        INSERT INTO generated_documents (doc_id, user_id, doc_type, title, content, created_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (doc_id, user_id, doc_type, title, content, now_str, meta_json))

    if count > 0:
        return True, doc_id
    return False, ""


def get_generated_documents(user_id: str, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve saved documents for a user, optionally filtered by doc_type."""
    user_id = user_id.strip().lower()
    if doc_type:
        rows = execute_query(
            "SELECT * FROM generated_documents WHERE user_id = ? AND doc_type = ? ORDER BY created_at DESC",
            (user_id, doc_type)
        )
    else:
        rows = execute_query(
            "SELECT * FROM generated_documents WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
    docs = []
    for r in rows:
        item = dict(r)
        try:
            item["metadata"] = json.loads(item.get("metadata") or "{}")
        except Exception:
            item["metadata"] = {}
        docs.append(item)
    return docs


# =========================================================
# 7. FACTUAL USER ANALYTICS ENGINE
# =========================================================

def calculate_user_analytics(user_id: str) -> Dict[str, Any]:
    """Calculate strictly factual pipeline metrics and conversion rates for a user."""
    apps = get_applications(user_id)
    total_apps = len(apps)

    empty_metrics = {
        "total_applications": 0,
        "submitted_applications": 0,
        "active_interviews": 0,
        "total_offers": 0,
        "total_rejections": 0,
        "total_rejected": 0,
        "applications_this_week": 0,
        "applications_this_month": 0,
        "response_rate": 0.0,
        "interview_rate": 0.0,
        "offer_rate": 0.0,
        "rejection_rate": 0.0,
        "average_days_to_response": 0.0,
        "avg_match_score": 0.0,
        "status_distribution": {s: 0 for s in STATUS_OPTIONS},
        "status_counts": {s: 0 for s in STATUS_OPTIONS},
        "recent_velocity": {"this_week": 0, "this_month": 0},
        "top_companies": {},
        "top_roles": {},
        "has_sufficient_data": False,
        "insights": ["Start tracking applications to view your personalized conversion funnel!"]
    }

    if total_apps == 0:
        return empty_metrics

    status_counts = get_status_counts(user_id)

    # Submissions count (excluding Wishlist/Saved)
    submitted = sum(
        count for st_name, count in status_counts.items()
        if st_name not in ("Wishlist", "Saved")
    )

    # Active interviews (Interview, Technical Round, HR Round)
    interview_count = (
        status_counts.get("Interview", 0) +
        status_counts.get("Technical Round", 0) +
        status_counts.get("HR Round", 0)
    )

    offers = status_counts.get("Offer", 0) + status_counts.get("Selected", 0)
    rejected = status_counts.get("Rejected", 0)

    # Responses = anything progressed past Applied/Saved/Wishlist
    responses = sum(
        count for st_name, count in status_counts.items()
        if st_name in ("Screening", "Assessment", "Interview", "Technical Round", "HR Round", "Offer", "Selected", "Rejected")
    )

    resp_rate = round((responses / submitted) * 100, 1) if submitted > 0 else 0.0
    int_rate = round((interview_count / submitted) * 100, 1) if submitted > 0 else 0.0
    off_rate = round((offers / submitted) * 100, 1) if submitted > 0 else 0.0
    rej_rate = round((rejected / submitted) * 100, 1) if submitted > 0 else 0.0

    scores = [a.get("score", 0) for a in apps if a.get("score", 0) and a.get("score", 0) > 0]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    # Weekly and Monthly application velocity & Days to response
    today = date.today()
    this_week_start = today - timedelta(days=today.weekday())
    this_month_prefix = today.strftime("%Y-%m")

    apps_this_week = 0
    apps_this_month = 0
    response_days_list = []

    for a in apps:
        app_date_str = str(a.get("applied_date", "")).strip()[:10]
        if app_date_str:
            try:
                ad = datetime.strptime(app_date_str, "%Y-%m-%d").date()
                if ad >= this_week_start:
                    apps_this_week += 1
                if app_date_str.startswith(this_month_prefix):
                    apps_this_month += 1

                st = a.get("status", "")
                if st in ("Screening", "Assessment", "Interview", "Technical Round", "HR Round", "Offer", "Selected", "Rejected"):
                    last_up = str(a.get("last_updated", "")).strip()[:10]
                    if last_up:
                        l_date = datetime.strptime(last_up, "%Y-%m-%d").date()
                        diff_days = (l_date - ad).days
                        if diff_days >= 0:
                            response_days_list.append(diff_days)
            except Exception:
                pass

    avg_days_to_response = round(sum(response_days_list) / len(response_days_list), 1) if response_days_list else 0.0

    # Company & Role counts (as dictionaries)
    comp_map = {}
    role_map = {}
    for a in apps:
        c = a.get("company", "Unknown").strip()
        t = a.get("title", "Unknown").strip()
        if c:
            comp_map[c] = comp_map.get(c, 0) + 1
        if t:
            role_map[t] = role_map.get(t, 0) + 1

    top_companies = dict(sorted(comp_map.items(), key=lambda x: x[1], reverse=True)[:6])
    top_roles = dict(sorted(role_map.items(), key=lambda x: x[1], reverse=True)[:6])

    # Honest Insights
    insights = []
    has_sufficient_data = submitted >= 3

    if not has_sufficient_data:
        insights.append(f"Track at least 3 submitted applications to unlock statistical insights (currently: {submitted}).")
    else:
        if resp_rate >= 30:
            insights.append(f"Strong response rate ({resp_rate}%) indicates high resume keyword relevance.")
        elif resp_rate < 15:
            insights.append("Response rate is below 15%. Consider running the 7-Component Health Audit and tailoring resumes.")

        if interview_count > 0:
            insights.append(f"Active interview momentum: {interview_count} applications currently in interview rounds.")

        if top_roles:
            first_role = next(iter(top_roles.keys()))
            insights.append(f"Primary focus area: '{first_role}' is your most actively targeted role.")

    return {
        "total_applications": total_apps,
        "submitted_applications": submitted,
        "active_interviews": interview_count,
        "total_offers": offers,
        "total_rejections": rejected,
        "total_rejected": rejected,
        "applications_this_week": apps_this_week,
        "applications_this_month": apps_this_month,
        "response_rate": resp_rate,
        "interview_rate": int_rate,
        "offer_rate": off_rate,
        "rejection_rate": rej_rate,
        "average_days_to_response": avg_days_to_response,
        "avg_match_score": avg_score,
        "status_distribution": status_counts,
        "status_counts": status_counts,
        "recent_velocity": {"this_week": apps_this_week, "this_month": apps_this_month},
        "top_companies": top_companies,
        "top_roles": top_roles,
        "has_sufficient_data": has_sufficient_data,
        "insights": insights
    }


# =========================================================
# 8. AI MOCK INTERVIEW DELEGATES
# =========================================================

from database.interview_repo import (
    create_interview_session,
    get_interview_session,
    get_user_interview_sessions,
    update_interview_session,
    delete_interview_session,
    add_interview_question,
    get_interview_questions,
    save_interview_answer,
    get_interview_answers,
    save_interview_evaluation,
    get_interview_evaluations,
    save_interview_report,
    get_interview_report,
    get_user_interview_reports,
    get_interview_progress_analytics,
)

