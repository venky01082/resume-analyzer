import json
import os
from datetime import datetime, date

FILE_NAME = "applications.json"

STATUS_OPTIONS = [
    "Saved", "Applied", "Assessment", "Interview",
    "Offer", "Selected", "Rejected", "Withdrawn"
]

PRIORITY_OPTIONS = ["Low", "Medium", "High"]


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_applications():
    if not os.path.exists(FILE_NAME):
        return []
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_applications(applications):
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(applications, file, indent=4, ensure_ascii=False)


def _normalize(item):
    defaults = {
        "title": "", "company": "", "location": "", "score": 0,
        "application_url": "", "status": "Saved", "priority": "Medium",
        "applied_date": "", "follow_up_date": "", "last_updated": "",
        "notes": "", "contact_name": "", "contact_email": "",
        "salary": "", "source": "", "job_description": ""
    }
    changed = False
    for key, value in defaults.items():
        if key not in item:
            item[key] = value
            changed = True
    if item["status"] not in STATUS_OPTIONS:
        item["status"] = "Saved"
        changed = True
    if item["priority"] not in PRIORITY_OPTIONS:
        item["priority"] = "Medium"
        changed = True
    return changed


def migrate_application_file():
    applications = load_applications()
    changed = False
    for item in applications:
        if _normalize(item):
            changed = True
    if changed:
        save_applications(applications)
    return applications


def add_application(
    title, company, location, score, application_url,
    status="Saved", priority="Medium", applied_date="",
    follow_up_date="", notes="", contact_name="",
    contact_email="", salary="", source="", job_description=""
):
    applications = load_applications()
    for item in applications:
        if (item.get("title", "").strip().lower() == title.strip().lower()
                and item.get("company", "").strip().lower() == company.strip().lower()):
            return False

    applications.append({
        "title": title, "company": company, "location": location,
        "score": score, "application_url": application_url,
        "status": status if status in STATUS_OPTIONS else "Saved",
        "priority": priority if priority in PRIORITY_OPTIONS else "Medium",
        "applied_date": applied_date, "follow_up_date": follow_up_date,
        "last_updated": _now(), "notes": notes,
        "contact_name": contact_name, "contact_email": contact_email,
        "salary": salary, "source": source,
        "job_description": job_description
    })
    save_applications(applications)
    return True


def update_application_status(index, status):
    applications = load_applications()
    if 0 <= index < len(applications) and status in STATUS_OPTIONS:
        _normalize(applications[index])
        applications[index]["status"] = status
        if status == "Applied" and not applications[index].get("applied_date"):
            applications[index]["applied_date"] = date.today().isoformat()
        applications[index]["last_updated"] = _now()
        save_applications(applications)
        return True
    return False


def update_application(index, status=None, priority=None, applied_date=None,
                       follow_up_date=None, notes=None, contact_name=None,
                       contact_email=None, salary=None, source=None):
    applications = load_applications()
    if not 0 <= index < len(applications):
        return False
    item = applications[index]
    _normalize(item)

    if status is not None:
        if status not in STATUS_OPTIONS:
            return False
        item["status"] = status
    if priority is not None:
        if priority not in PRIORITY_OPTIONS:
            return False
        item["priority"] = priority
    if applied_date is not None:
        item["applied_date"] = applied_date
    if follow_up_date is not None:
        item["follow_up_date"] = follow_up_date
    if notes is not None:
        item["notes"] = notes
    if contact_name is not None:
        item["contact_name"] = contact_name
    if contact_email is not None:
        item["contact_email"] = contact_email
    if salary is not None:
        item["salary"] = salary
    if source is not None:
        item["source"] = source

    if item["status"] == "Applied" and not item.get("applied_date"):
        item["applied_date"] = date.today().isoformat()

    item["last_updated"] = _now()
    save_applications(applications)
    return True


def delete_application(index):
    applications = load_applications()
    if 0 <= index < len(applications):
        applications.pop(index)
        save_applications(applications)
        return True
    return False


def get_status_counts(applications=None):
    applications = applications if applications is not None else load_applications()
    counts = {status: 0 for status in STATUS_OPTIONS}
    for item in applications:
        status = item.get("status", "Saved")
        counts[status if status in counts else "Saved"] += 1
    return counts


def get_follow_up_items(applications=None, include_future=True):
    applications = applications if applications is not None else load_applications()
    today = date.today()
    result = []
    for index, item in enumerate(applications):
        value = str(item.get("follow_up_date", "")).strip()
        if not value:
            continue
        try:
            follow_date = date.fromisoformat(value)
        except ValueError:
            continue
        state = "overdue" if follow_date < today else "today" if follow_date == today else "upcoming"
        if include_future or state in {"overdue", "today"}:
            result.append({"index": index, "application": item,
                           "state": state, "date": follow_date})
    return sorted(result, key=lambda x: x["date"])


def get_overdue_follow_ups(applications=None):
    return [x for x in get_follow_up_items(applications, False) if x["state"] == "overdue"]


def get_today_follow_ups(applications=None):
    return [x for x in get_follow_up_items(applications, False) if x["state"] == "today"]