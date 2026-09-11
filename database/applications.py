"""
Applications Database Module
Delegates to unified repository with full backward compatibility.
"""

from database.models import STATUS_OPTIONS, PRIORITY_OPTIONS
from database.migrations import migrate_legacy_data as migrate_legacy_applications
from database.repository import (
    get_applications,
    get_application,
    create_application,
    update_application,
    delete_application,
    get_status_history,
    get_status_counts,
    get_overdue_follow_ups,
    get_today_follow_ups,
    get_upcoming_follow_ups,
)

APPLICATIONS_FILE = "applications.json"
