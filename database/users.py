"""
User & Authentication Database Module
Delegates to unified repository with full backward compatibility.
"""

from database.repository import (
    hash_password,
    verify_password,
    validate_password_strength,
    get_user,
    get_user_by_username,
    get_user_by_email,
    create_user,
    verify_user_credentials,
    update_user_password,
    delete_user_account,
    get_user_profile,
    update_user_profile,
    get_user_preferences,
    update_user_preferences,
)
from database.connection import read_json_file, write_json_file

USERS_FILE = "users.json"
