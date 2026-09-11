"""
Resumes Database Module
Delegates to unified repository with full backward compatibility.
"""

from database.repository import (
    get_resumes,
    get_resume,
    get_default_resume,
    save_resume,
    create_resume,
    set_default_resume,
    delete_resume,
)

RESUMES_FILE = "resumes.json"
