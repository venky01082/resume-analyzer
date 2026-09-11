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
    professional_title: str = ""
    target_roles: str = ""
    preferred_locations: str = ""
    work_mode_preference: str = "Any"  # Remote, Hybrid, On-site, Any
    years_of_experience: float = 0.0
    skills: str = ""
    technical_skills: str = ""
    soft_skills: str = ""
    education: str = ""
    certifications: str = ""
    preferred_industries: str = ""
    expected_salary: str = ""
    notice_period: str = ""
    work_authorization: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        if not data:
            return cls()
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
        if not data:
            return cls()
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
    notes: str = ""
    priority: str = "Medium"
    tags: str = ""

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
    status: str = "Applied"
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
    resume_used: str = ""
    cover_letter_used: str = ""
    next_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApplicationRecord":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class StatusHistoryEntry:
    history_id: str
    app_id: str
    user_id: str
    status: str
    changed_at: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusHistoryEntry":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class GeneratedDocument:
    doc_id: str
    user_id: str
    doc_type: str  # tailored_resume, cover_letter, email, follow_up
    title: str
    content: str
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeneratedDocument":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


# Expanded 10-Stage CRM Application Lifecycle Pipeline
STATUS_OPTIONS = [
    "Wishlist",
    "Saved",
    "Applied",
    "Assessment",
    "Interview",
    "Technical Round",
    "HR Round",
    "Offer",
    "Rejected",
    "Withdrawn"
]

PRIORITY_OPTIONS = ["High", "Medium", "Low"]
WORK_MODE_OPTIONS = ["Any", "Remote", "Hybrid", "On-site"]

# =========================================================
# AI MOCK INTERVIEW CONSTANTS & DATA MODELS
# =========================================================

INTERVIEW_TYPES = [
    "General",
    "Technical",
    "Behavioral",
    "HR",
    "Mixed",
    "Job-Specific"
]

DIFFICULTY_LEVELS = [
    "Easy",
    "Medium",
    "Hard",
    "Adaptive"
]

INTERVIEWER_PERSONALITIES = [
    "Professional",
    "Friendly",
    "Strict",
    "Technical",
    "HR"
]

QUESTION_CATEGORIES = [
    "Technical Knowledge",
    "Problem Solving",
    "Coding Concepts",
    "System Design",
    "Projects",
    "Resume Questions",
    "Behavioral",
    "Leadership",
    "Communication",
    "Situational",
    "HR"
]

QUESTION_COUNT_OPTIONS = [5, 10, 15, 20]
DURATION_OPTIONS = [0, 15, 30, 45, 60]


@dataclass
class InterviewSession:
    session_id: str
    user_id: str
    target_role: str
    interview_type: str = "Technical"
    difficulty: str = "Adaptive"
    interviewer_personality: str = "Professional"
    question_count: int = 5
    duration_minutes: int = 15
    resume_id: str = ""
    job_id: str = ""
    status: str = "in_progress"  # in_progress, paused, completed, cancelled
    started_at: str = ""
    completed_at: str = ""
    overall_score: float = 0.0
    current_question_index: int = 0
    weak_topics: List[str] = field(default_factory=list)
    strong_topics: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterviewSession":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class InterviewQuestion:
    question_id: str
    session_id: str
    user_id: str
    question_number: int
    question_text: str
    category: str = "Technical Knowledge"
    difficulty: str = "Medium"
    context_origin: str = ""  # e.g. "resume:sklearn", "job:sql", "follow_up:rest_api"
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterviewQuestion":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class InterviewAnswer:
    answer_id: str
    question_id: str
    session_id: str
    user_id: str
    answer_text: str
    submitted_at: str = ""
    word_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterviewAnswer":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class InterviewEvaluation:
    evaluation_id: str
    answer_id: str
    session_id: str
    user_id: str
    overall_answer_score: float = 0.0
    technical_score: float = 0.0
    relevance_score: float = 0.0
    completeness_score: float = 0.0
    clarity_score: float = 0.0
    problem_solving_score: float = 0.0
    feedback: str = ""
    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    detected_topics: List[str] = field(default_factory=list)
    is_strong: bool = False
    evaluated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterviewEvaluation":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class InterviewReport:
    report_id: str
    session_id: str
    user_id: str
    target_role: str
    overall_score: float = 0.0
    technical_score: float = 0.0
    problem_solving_score: float = 0.0
    communication_score: float = 0.0
    completeness_score: float = 0.0
    relevance_score: float = 0.0
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    question_reviews: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterviewReport":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

