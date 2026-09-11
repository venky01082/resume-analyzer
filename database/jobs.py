"""
Saved Jobs Database Module
Delegates to unified repository with full backward compatibility.
"""

from database.repository import (
    get_saved_jobs,
    is_job_saved,
    save_job,
    remove_saved_job,
    delete_saved_job,
    update_saved_job_notes,
)

SAVED_JOBS_FILE = "saved_jobs.json"
