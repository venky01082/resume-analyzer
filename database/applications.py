"""
Application Tracking Database Module
Handles user-scoped application storage, 9-stage pipeline statuses, and follow-ups.
Maintains 100% backward compatibility with existing applications.json files.
"""

import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from database.connection import read_json_file, write_json_file
from database.models import ApplicationRecord

APPLICATIONS_FILE = "applications.json"

STATUS_OPTIONS = [
    "Saved",
    "Applied",
    "Screening",
    "Interview",
    "Technical Round",
    "HR Round",
    "Offer",
    "Rejected",
    "Withdrawn"
]

PRIORITY_OPTIONS = ["High", "Medium", "Low"]


def migrate_legacy_applications() -> None:
    """Ensure existing applications have app_id and user_id fields."""
    raw = read_json_file(APPLICATIONS_FILE, default=[])
    if not isinstance(raw, list):
        return

    modified = False
    for item in raw:
        if not isinstance(item, dict):
            continue
        if "app_id" not in item:
            item["app_id"] = f"app_{uuid.uuid4().hex[:8]}"
            modified = True
        if "user_id" not in item or not item["user_id"]:
            item["user_id"] = "venky"  # Assign legacy un-scoped record to default user
            modified = True
        if "status" not in item or item["status"] not in STATUS_OPTIONS:
            if item.get("status") == "Selected":
                item["status"] = "Offer"
            elif item.get("status") == "Assessment":
                item["status"] = "Technical Round"
            elif item.get("status") not in STATUS_OPTIONS:
                item["status"] = "Applied"
            modified = True

    if modified:
        write_json_file(APPLICATIONS_FILE, raw)


def _load_all_raw_applications() -> List[Dict[str, Any]]:
    migrate_legacy_applications()
    data = read_json_file(APPLICATIONS_FILE, default=[])
    return data if isinstance(data, list) else []


def _save_all_raw_applications(data: List[Dict[str, Any]]) -> bool:
    return write_json_file(APPLICATIONS_FILE, data)


def get_applications(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all applications for a specific user."""
    user_id = user_id.strip().lower()
    all_apps = _load_all_raw_applications()
    return [a for a in all_apps if a.get("user_id", "").strip().lower() == user_id]


def get_application(user_id: str, app_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single application by app_id for a user."""
    user_apps = get_applications(user_id)
    for a in user_apps:
        if a.get("app_id") == app_id:
            return a
    return None


def create_application(
    user_id: str,
    title: str,
    company: str,
    location: str = "India",
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
    job_description: str = ""
) -> Dict[str, Any]:
    """Create and persist a new user application record."""
    user_id = user_id.strip().lower()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    applied_str = applied_date or datetime.now().strftime("%Y-%m-%d")

    # Default follow-up date 7 days later if not provided
    if not follow_up_date:
        follow_up_date = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")

    app_id = f"app_{uuid.uuid4().hex[:8]}"

    record = ApplicationRecord(
        app_id=app_id,
        user_id=user_id,
        title=title.strip(),
        company=company.strip(),
        location=location.strip() or "India",
        score=score,
        application_url=application_url.strip(),
        status=status if status in STATUS_OPTIONS else "Applied",
        priority=priority if priority in PRIORITY_OPTIONS else "Medium",
        applied_date=applied_str,
        follow_up_date=follow_up_date.strip(),
        last_updated=now_str,
        notes=notes.strip(),
        contact_name=contact_name.strip(),
        contact_email=contact_email.strip(),
        salary=salary.strip(),
        source=source.strip(),
        job_description=job_description.strip()
    )

    all_apps = _load_all_raw_applications()
    all_apps.append(record.to_dict())
    _save_all_raw_applications(all_apps)
    return record.to_dict()


def update_application(
    user_id: str,
    identifier: Any,
    updates: Optional[Dict[str, Any]] = None,
    **kwargs
) -> bool:
    """Update fields on an existing application for a user. Supports dict or kwargs, and app_id or index."""
    user_id = user_id.strip().lower()
    all_apps = _load_all_raw_applications()
    user_apps = [a for a in all_apps if a.get("user_id", "").strip().lower() == user_id]

    # Resolve identifier (could be app_id or integer index)
    target_id = None
    if isinstance(identifier, int) and 0 <= identifier < len(user_apps):
        target_id = user_apps[identifier].get("app_id")
    else:
        target_id = str(identifier)

    combined_updates = {}
    if isinstance(updates, dict):
        combined_updates.update(updates)
    combined_updates.update(kwargs)

    found = False
    for a in all_apps:
        if a.get("app_id") == target_id and a.get("user_id", "").strip().lower() == user_id:
            a.update(combined_updates)
            a["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            found = True
            break

    if found:
        return _save_all_raw_applications(all_apps)
    return False


def delete_application(user_id: str, identifier: Any) -> bool:
    """Delete an application record for a user. Supports app_id or integer index."""
    user_id = user_id.strip().lower()
    all_apps = _load_all_raw_applications()
    user_apps = [a for a in all_apps if a.get("user_id", "").strip().lower() == user_id]

    target_id = None
    if isinstance(identifier, int) and 0 <= identifier < len(user_apps):
        target_id = user_apps[identifier].get("app_id")
    else:
        target_id = str(identifier)

    initial_len = len(all_apps)
    all_apps = [a for a in all_apps if not (a.get("app_id") == target_id and a.get("user_id", "").strip().lower() == user_id)]

    if len(all_apps) < initial_len:
        return _save_all_raw_applications(all_apps)
    return False


# =========================================================
# APPLICATION PIPELINE & FOLLOW-UP CALCULATIONS
# =========================================================

def get_status_counts(applications: List[Dict[str, Any]]) -> Dict[str, int]:
    """Return count per status for the provided application list."""
    counts = {status: 0 for status in STATUS_OPTIONS}
    for app in applications:
        status = app.get("status", "Applied")
        if status in counts:
            counts[status] += 1
        elif status == "Selected":
            counts["Offer"] += 1
        elif status == "Assessment":
            counts["Technical Round"] += 1
        else:
            counts["Applied"] += 1
    return counts


def _parse_ref_date(reference_date: Optional[Any]) -> date:
    if reference_date is None:
        return date.today()
    if isinstance(reference_date, str):
        return datetime.strptime(reference_date, "%Y-%m-%d").date()
    if isinstance(reference_date, datetime):
        return reference_date.date()
    return reference_date


def get_overdue_follow_ups(applications: List[Dict[str, Any]], reference_date: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Return items with follow-up dates strictly before today (or reference date)."""
    today = _parse_ref_date(reference_date)
    overdue = []
    for app in applications:
        status = app.get("status", "")
        if status in ["Offer", "Rejected", "Withdrawn"]:
            continue
        fu = app.get("follow_up_date", "")
        if not fu:
            continue
        try:
            d = datetime.strptime(fu, "%Y-%m-%d").date()
            if d < today:
                overdue.append({
                    "application": app,
                    "date": d,
                    "days_diff": (today - d).days,
                    "type": "overdue"
                })
        except ValueError:
            continue
    overdue.sort(key=lambda x: x["date"])
    return overdue


def get_today_follow_ups(applications: List[Dict[str, Any]], reference_date: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Return items with follow-up date equal to today (or reference date)."""
    today = _parse_ref_date(reference_date)
    today_items = []
    for app in applications:
        status = app.get("status", "")
        if status in ["Offer", "Rejected", "Withdrawn"]:
            continue
        fu = app.get("follow_up_date", "")
        if not fu:
            continue
        try:
            d = datetime.strptime(fu, "%Y-%m-%d").date()
            if d == today:
                today_items.append({
                    "application": app,
                    "date": d,
                    "type": "today"
                })
        except ValueError:
            continue
    return today_items


def get_upcoming_follow_ups(applications: List[Dict[str, Any]], days_ahead: Any = 14, reference_date: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Return items with follow-up date within the next N days from today (or reference date)."""
    if isinstance(days_ahead, (str, date, datetime)) and reference_date is None:
        reference_date = days_ahead
        days_ahead = 14
    today = _parse_ref_date(reference_date)
    limit = today + timedelta(days=int(days_ahead))
    upcoming = []
    for app in applications:
        status = app.get("status", "")
        if status in ["Offer", "Rejected", "Withdrawn"]:
            continue
        fu = app.get("follow_up_date", "")
        if not fu:
            continue
        try:
            d = datetime.strptime(fu, "%Y-%m-%d").date()
            if today < d <= limit:
                upcoming.append({
                    "application": app,
                    "date": d,
                    "days_diff": (d - today).days,
                    "type": "upcoming"
                })
        except ValueError:
            continue
    upcoming.sort(key=lambda x: x["date"])
    return upcoming

