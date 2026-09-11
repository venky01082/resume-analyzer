"""
Application Tracker Module
Provides user-scoped application tracking API backed by the database layer.
Maintains 100% backward compatibility with legacy function signatures.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional

from database.applications import (
    STATUS_OPTIONS,
    PRIORITY_OPTIONS,
    get_applications as db_get_applications,
    get_application as db_get_application,
    create_application as db_create_application,
    update_application as db_update_application,
    delete_application as db_delete_application,
    get_status_counts,
    get_overdue_follow_ups,
    get_today_follow_ups,
    get_upcoming_follow_ups,
    migrate_legacy_applications as migrate_application_file,
)


def _get_active_user(user_id: Optional[str] = None) -> str:
    if user_id:
        return user_id.strip().lower()
    try:
        import streamlit as st
        return st.session_state.get("auth_username", "venky").strip().lower() or "venky"
    except Exception:
        return "venky"


def load_applications(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load applications for the current logged-in user or specified user."""
    uid = _get_active_user(user_id)
    return db_get_applications(uid)


def save_applications(applications: List[Dict[str, Any]], user_id: Optional[str] = None) -> None:
    """Save applications list (backward compatibility wrapper maintaining user scoping)."""
    from database.connection import read_json_file, write_json_file
    uid = _get_active_user(user_id)
    all_apps = read_json_file("applications.json", default=[])
    if not isinstance(all_apps, list):
        all_apps = []
    other_apps = [a for a in all_apps if isinstance(a, dict) and a.get("user_id") != uid]
    for app in applications:
        if isinstance(app, dict) and "user_id" not in app:
            app["user_id"] = uid
    write_json_file("applications.json", other_apps + applications)


def add_application(
    title: str,
    company: str,
    location: str = "",
    score: int = 0,
    application_url: str = "",
    status: str = "Applied",
    priority: str = "Medium",
    applied_date: Optional[str] = None,
    follow_up_date: str = "",
    notes: str = "",
    contact_name: str = "",
    contact_email: str = "",
    salary: str = "",
    source: str = "",
    job_description: str = "",
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new application record for the active user."""
    uid = _get_active_user(user_id)
    return db_create_application(
        user_id=uid,
        title=title,
        company=company,
        location=location,
        score=score,
        application_url=application_url,
        status=status,
        priority=priority,
        applied_date=applied_date,
        follow_up_date=follow_up_date,
        notes=notes,
        contact_name=contact_name,
        contact_email=contact_email,
        salary=salary,
        source=source,
        job_description=job_description
    )


def update_application_status(app_id_or_idx: Any, new_status: str, user_id: Optional[str] = None) -> bool:
    """Update status by app_id (or legacy numeric index)."""
    uid = _get_active_user(user_id)
    apps = db_get_applications(uid)
    if isinstance(app_id_or_idx, int) and 0 <= app_id_or_idx < len(apps):
        target_id = apps[app_id_or_idx].get("app_id")
    else:
        target_id = str(app_id_or_idx)

    if not target_id:
        return False
    return db_update_application(uid, target_id, {"status": new_status})


def update_application(app_id_or_idx: Any, updates: Dict[str, Any], user_id: Optional[str] = None) -> bool:
    """Update application fields by app_id (or legacy numeric index)."""
    uid = _get_active_user(user_id)
    apps = db_get_applications(uid)
    if isinstance(app_id_or_idx, int) and 0 <= app_id_or_idx < len(apps):
        target_id = apps[app_id_or_idx].get("app_id")
    else:
        target_id = str(app_id_or_idx)

    if not target_id:
        return False
    return db_update_application(uid, target_id, updates)


def delete_application(app_id_or_idx: Any, user_id: Optional[str] = None) -> bool:
    """Delete application by app_id (or legacy numeric index)."""
    uid = _get_active_user(user_id)
    apps = db_get_applications(uid)
    if isinstance(app_id_or_idx, int) and 0 <= app_id_or_idx < len(apps):
        target_id = apps[app_id_or_idx].get("app_id")
    else:
        target_id = str(app_id_or_idx)

    if not target_id:
        return False
    return db_delete_application(uid, target_id)


def get_follow_up_items(applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return all follow-up items."""
    return get_overdue_follow_ups(applications) + get_today_follow_ups(applications) + get_upcoming_follow_ups(applications)