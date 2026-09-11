"""
Data Models for AI Job Application Assistant
Defines dataclasses and schema structures for multi-user isolation.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class UserProfile:
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    target_roles: str = ""
    skills: str = ""
    experience: str = ""
    education: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class UserPreferences:
    preferred_roles: str = ""
    preferred_locations: str = "India"
    work_preference: str = "Any"  # Remote, Hybrid, On-site, Any
    default_cover_letter_tone: str = "Professional"
    default_email_length: str = "Medium"
    default_resume_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreferences":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class ResumeRecord:
    resume_id: str
    user_id: str
    title: str
    filename: str
    text: str
    uploaded_at: str
    score: int = 0
    is_default: bool = False
    parsed_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResumeRecord":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class SavedJob:
    job_id: str
    user_id: str
    title: str
    company: str
    location: str
    url: str = ""
    score: int = 0
    salary: str = ""
    saved_at: str = ""
    description: str = ""
    status: str = "Saved"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SavedJob":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class ApplicationRecord:
    app_id: str
    user_id: str
    title: str
    company: str
    location: str
    score: int = 0
    application_url: str = ""
    status: str = "Applied"  # Saved, Applied, Screening, Interview, Technical Round, HR Round, Offer, Rejected, Withdrawn
    priority: str = "Medium"  # High, Medium, Low
    applied_date: str = ""
    follow_up_date: str = ""
    last_updated: str = ""
    notes: str = ""
    contact_name: str = ""
    contact_email: str = ""
    salary: str = ""
    source: str = ""
    job_description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApplicationRecord":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


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
