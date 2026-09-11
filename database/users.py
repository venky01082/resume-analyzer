"""
User & Authentication Database Module
Handles secure user accounts, password hashing, profiles, and preferences.
"""

import os
import base64
import hashlib
import secrets
from typing import Dict, Any, Optional, Tuple
from database.connection import read_json_file, write_json_file
from database.models import UserProfile, UserPreferences

USERS_FILE = "users.json"


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Generate salted PBKDF2 HMAC SHA-256 password hash."""
    if not salt:
        salt_bytes = secrets.token_bytes(16)
    else:
        salt_bytes = base64.b64decode(salt.encode("utf-8"))
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 200_000)
    salt_str = base64.b64encode(salt_bytes).decode("utf-8")
    hash_str = base64.b64encode(key).decode("utf-8")
    return salt_str, hash_str


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """Verify password against stored salt and hash."""
    if not salt or not password_hash:
        return False
    _, test_hash = hash_password(password, salt)
    return secrets.compare_digest(test_hash, password_hash)


def load_users() -> Dict[str, Any]:
    """Load all users from storage."""
    return read_json_file(USERS_FILE, default={})


def save_users(users: Dict[str, Any]) -> bool:
    """Save users dictionary to storage."""
    return write_json_file(USERS_FILE, users)


def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Retrieve user record by username."""
    users = load_users()
    return users.get(username.strip().lower())


get_user_by_username = get_user


def create_user(
    username: str,
    password: str,
    full_name: str = "",
    email: str = "",
    target_roles: str = ""
) -> Tuple[bool, str]:
    """Create a new user account with secure password hash and isolated profile."""
    username = username.strip().lower()
    if not username:
        return False, "Username cannot be empty."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    users = load_users()
    if username in users:
        return False, "Username already exists."

    salt, p_hash = hash_password(password)
    profile = UserProfile(
        full_name=full_name.strip(),
        email=email.strip(),
        target_roles=target_roles.strip()
    )
    prefs = UserPreferences(
        preferred_roles=target_roles.strip()
    )

    users[username] = {
        "username": username,
        "password_salt": salt,
        "password_hash": p_hash,
        "profile": profile.to_dict(),
        "preferences": prefs.to_dict(),
        "created_at": str(secrets.token_hex(4))  # safe placeholder id
    }
    save_users(users)
    return True, "Account created successfully."


def verify_user_credentials(username: str, password: str) -> bool:
    """Authenticate username and password."""
    user = get_user(username)
    if not user:
        return False
    return verify_password(password, user.get("password_salt", ""), user.get("password_hash", ""))


def get_user_profile(username: str) -> Dict[str, Any]:
    """Get the UserProfile dict for a user."""
    user = get_user(username)
    if not user:
        return UserProfile().to_dict()
    profile_data = user.get("profile", {})
    return UserProfile.from_dict(profile_data).to_dict()


def update_user_profile(username: str, profile_data: Dict[str, Any]) -> bool:
    """Update user profile."""
    username = username.strip().lower()
    users = load_users()
    if username not in users:
        return False

    existing_profile = users[username].get("profile", {})
    existing_profile.update(profile_data)
    users[username]["profile"] = UserProfile.from_dict(existing_profile).to_dict()
    return save_users(users)


def get_user_preferences(username: str) -> Dict[str, Any]:
    """Get user preferences."""
    user = get_user(username)
    if not user:
        return UserPreferences().to_dict()
    prefs_data = user.get("preferences", {})
    return UserPreferences.from_dict(prefs_data).to_dict()


def update_user_preferences(username: str, prefs_data: Dict[str, Any]) -> bool:
    """Update user preferences."""
    username = username.strip().lower()
    users = load_users()
    if username not in users:
        return False

    existing_prefs = users[username].get("preferences", {})
    existing_prefs.update(prefs_data)
    users[username]["preferences"] = UserPreferences.from_dict(existing_prefs).to_dict()
    return save_users(users)


def delete_user_account(username: str) -> bool:
    """Delete a user account."""
    username = username.strip().lower()
    users = load_users()
    if username in users:
        del users[username]
        return save_users(users)
    return False
