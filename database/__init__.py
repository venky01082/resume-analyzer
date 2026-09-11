"""
Database Abstraction Layer for AI Job Application Assistant
Provides clean, decoupled, user-isolated storage APIs.
"""

from database.models import (
    UserProfile,
    UserPreferences,
    ResumeRecord,
    SavedJob,
    ApplicationRecord
)

from database.users import (
    create_user,
    get_user,
    verify_user_credentials,
    get_user_profile,
    update_user_profile,
    get_user_preferences,
    update_user_preferences,
    delete_user_account,
    hash_password,
    verify_password
)

from database.resumes import (
    save_resume,
    get_resumes,
    get_resume,
    get_default_resume,
    set_default_resume,
    update_resume_title,
    delete_resume
)

from database.jobs import (
    get_saved_jobs,
    is_job_saved,
    save_job,
    delete_saved_job
)

from database.applications import (
    get_applications,
    get_application,
    create_application,
    update_application,
    delete_application,
    get_status_counts,
    get_overdue_follow_ups,
    get_today_follow_ups,
    get_upcoming_follow_ups,
    migrate_legacy_applications,
    STATUS_OPTIONS,
    PRIORITY_OPTIONS
)

from database.analytics import (
    calculate_user_analytics
)
