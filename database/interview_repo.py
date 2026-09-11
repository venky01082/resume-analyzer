"""
Interview Database Repository Module
Provides strictly isolated, parameterized data access for AI Mock Interview sessions,
questions, answers, evaluations, reports, and longitudinal performance analytics.
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from database.connection import execute_query, execute_mutation, get_db_connection
from database.models import (
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    InterviewEvaluation,
    InterviewReport,
    INTERVIEW_TYPES,
    DIFFICULTY_LEVELS,
    INTERVIEWER_PERSONALITIES,
    QUESTION_CATEGORIES,
)


# =========================================================
# 1. INTERVIEW SESSIONS
# =========================================================

def create_interview_session(
    user_id: str,
    target_role: str,
    interview_type: str = "Technical",
    difficulty: str = "Adaptive",
    interviewer_personality: str = "Professional",
    question_count: int = 5,
    duration_minutes: int = 15,
    resume_id: str = "",
    job_id: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """Create a new user-scoped interview session."""
    user_id = user_id.strip().lower()
    if not target_role:
        return False, "Target role is required."

    session_id = f"sess_{uuid.uuid4().hex[:10]}"
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_json = json.dumps(metadata or {})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO interview_sessions (
                session_id, user_id, target_role, interview_type, difficulty,
                interviewer_personality, question_count, duration_minutes,
                resume_id, job_id, status, started_at, completed_at,
                overall_score, current_question_index, weak_topics,
                strong_topics, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, user_id, target_role.strip(), interview_type, difficulty,
            interviewer_personality, question_count, duration_minutes,
            resume_id, job_id, "in_progress", started_at, "",
            0.0, 0, json.dumps([]), json.dumps([]), meta_json
        ))

    return True, session_id


def get_interview_session(user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single interview session strictly scoped to user_id."""
    user_id = user_id.strip().lower()
    rows = execute_query(
        "SELECT * FROM interview_sessions WHERE user_id = ? AND session_id = ?",
        (user_id, session_id)
    )
    if not rows:
        return None
    res = dict(rows[0])
    try:
        res["weak_topics"] = json.loads(res.get("weak_topics") or "[]")
    except Exception:
        res["weak_topics"] = []
    try:
        res["strong_topics"] = json.loads(res.get("strong_topics") or "[]")
    except Exception:
        res["strong_topics"] = []
    try:
        res["metadata"] = json.loads(res.get("metadata") or "{}")
    except Exception:
        res["metadata"] = {}
    return res


def get_user_interview_sessions(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve all interview sessions for a user, ordered from newest to oldest."""
    user_id = user_id.strip().lower()
    rows = execute_query(
        "SELECT * FROM interview_sessions WHERE user_id = ? ORDER BY started_at DESC LIMIT ?",
        (user_id, limit)
    )
    sessions = []
    for r in rows:
        d = dict(r)
        try:
            d["weak_topics"] = json.loads(d.get("weak_topics") or "[]")
        except Exception:
            d["weak_topics"] = []
        try:
            d["strong_topics"] = json.loads(d.get("strong_topics") or "[]")
        except Exception:
            d["strong_topics"] = []
        try:
            d["metadata"] = json.loads(d.get("metadata") or "{}")
        except Exception:
            d["metadata"] = {}
        sessions.append(d)
    return sessions


def update_interview_session(user_id: str, session_id: str, **kwargs) -> bool:
    """Update fields on an interview session record with strict user isolation."""
    user_id = user_id.strip().lower()
    allowed = {
        "status", "completed_at", "overall_score", "current_question_index",
        "weak_topics", "strong_topics", "metadata", "target_role", "difficulty"
    }

    set_clauses = []
    params = []

    for k, v in kwargs.items():
        if k in allowed:
            if k in ("weak_topics", "strong_topics", "metadata"):
                val = json.dumps(v) if isinstance(v, (list, dict)) else str(v)
            else:
                val = v
            set_clauses.append(f"{k} = ?")
            params.append(val)

    if not set_clauses:
        return False

    params.extend([user_id, session_id])
    sql = f"UPDATE interview_sessions SET {', '.join(set_clauses)} WHERE user_id = ? AND session_id = ?"
    count = execute_mutation(sql, tuple(params))
    return count > 0


def delete_interview_session(user_id: str, session_id: str) -> bool:
    """Delete an interview session and its child questions/answers/reports."""
    user_id = user_id.strip().lower()
    execute_mutation("DELETE FROM interview_reports WHERE user_id = ? AND session_id = ?", (user_id, session_id))
    execute_mutation("DELETE FROM interview_evaluations WHERE user_id = ? AND session_id = ?", (user_id, session_id))
    execute_mutation("DELETE FROM interview_answers WHERE user_id = ? AND session_id = ?", (user_id, session_id))
    execute_mutation("DELETE FROM interview_questions WHERE user_id = ? AND session_id = ?", (user_id, session_id))
    count = execute_mutation("DELETE FROM interview_sessions WHERE user_id = ? AND session_id = ?", (user_id, session_id))
    return count > 0


# =========================================================
# 2. INTERVIEW QUESTIONS
# =========================================================

def add_interview_question(
    session_id: str,
    user_id: str,
    question_number: int,
    question_text: str,
    category: str = "Technical Knowledge",
    difficulty: str = "Medium",
    context_origin: str = "",
) -> Tuple[bool, str]:
    """Add a question to an active interview session."""
    user_id = user_id.strip().lower()
    question_id = f"q_{uuid.uuid4().hex[:10]}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Verify session ownership first
    sess = get_interview_session(user_id, session_id)
    if not sess:
        return False, "Session not found or access denied."

    count = execute_mutation("""
        INSERT INTO interview_questions (
            question_id, session_id, user_id, question_number,
            question_text, category, difficulty, context_origin, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        question_id, session_id, user_id, question_number,
        question_text.strip(), category, difficulty, context_origin, created_at
    ))

    return count > 0, question_id


def get_interview_questions(session_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all questions for a session, ordered by question number."""
    user_id = user_id.strip().lower()
    rows = execute_query(
        "SELECT * FROM interview_questions WHERE session_id = ? AND user_id = ? ORDER BY question_number ASC",
        (session_id, user_id)
    )
    return [dict(r) for r in rows]


# =========================================================
# 3. INTERVIEW ANSWERS
# =========================================================

def save_interview_answer(
    question_id: str,
    session_id: str,
    user_id: str,
    answer_text: str,
) -> Tuple[bool, str]:
    """Record a user's answer to a specific interview question."""
    user_id = user_id.strip().lower()
    answer_id = f"ans_{uuid.uuid4().hex[:10]}"
    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    words = len(answer_text.strip().split()) if answer_text.strip() else 0

    count = execute_mutation("""
        INSERT INTO interview_answers (
            answer_id, question_id, session_id, user_id,
            answer_text, submitted_at, word_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        answer_id, question_id, session_id, user_id,
        answer_text.strip(), submitted_at, words
    ))

    return count > 0, answer_id


def get_interview_answers(session_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all answers submitted for an interview session."""
    user_id = user_id.strip().lower()
    rows = execute_query(
        "SELECT * FROM interview_answers WHERE session_id = ? AND user_id = ? ORDER BY submitted_at ASC",
        (session_id, user_id)
    )
    return [dict(r) for r in rows]


# =========================================================
# 4. INTERVIEW EVALUATIONS
# =========================================================

def save_interview_evaluation(
    answer_id: str,
    session_id: str,
    user_id: str,
    overall_answer_score: float,
    technical_score: float,
    relevance_score: float,
    completeness_score: float,
    clarity_score: float,
    problem_solving_score: float,
    feedback: str,
    strengths: Optional[List[str]] = None,
    improvements: Optional[List[str]] = None,
    detected_topics: Optional[List[str]] = None,
    is_strong: bool = False,
) -> Tuple[bool, str]:
    """Persist an objective evaluation for a submitted answer."""
    user_id = user_id.strip().lower()
    evaluation_id = f"eval_{uuid.uuid4().hex[:10]}"
    evaluated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    count = execute_mutation("""
        INSERT INTO interview_evaluations (
            evaluation_id, answer_id, session_id, user_id,
            overall_answer_score, technical_score, relevance_score,
            completeness_score, clarity_score, problem_solving_score,
            feedback, strengths, improvements, detected_topics,
            is_strong, evaluated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        evaluation_id, answer_id, session_id, user_id,
        float(overall_answer_score), float(technical_score), float(relevance_score),
        float(completeness_score), float(clarity_score), float(problem_solving_score),
        feedback, json.dumps(strengths or []), json.dumps(improvements or []),
        json.dumps(detected_topics or []), 1 if is_strong else 0, evaluated_at
    ))

    return count > 0, evaluation_id


def get_interview_evaluations(session_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all answer evaluations for a session."""
    user_id = user_id.strip().lower()
    rows = execute_query(
        "SELECT * FROM interview_evaluations WHERE session_id = ? AND user_id = ? ORDER BY evaluated_at ASC",
        (session_id, user_id)
    )
    evals = []
    for r in rows:
        d = dict(r)
        try:
            d["strengths"] = json.loads(d.get("strengths") or "[]")
        except Exception:
            d["strengths"] = []
        try:
            d["improvements"] = json.loads(d.get("improvements") or "[]")
        except Exception:
            d["improvements"] = []
        try:
            d["detected_topics"] = json.loads(d.get("detected_topics") or "[]")
        except Exception:
            d["detected_topics"] = []
        evals.append(d)
    return evals


# =========================================================
# 5. FINAL INTERVIEW PERFORMANCE REPORTS
# =========================================================

def save_interview_report(
    session_id: str,
    user_id: str,
    target_role: str,
    overall_score: float,
    technical_score: float,
    problem_solving_score: float,
    communication_score: float,
    completeness_score: float,
    relevance_score: float,
    strengths: Optional[List[str]] = None,
    weaknesses: Optional[List[str]] = None,
    recommendations: Optional[List[str]] = None,
    question_reviews: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[bool, str]:
    """Save or update the final performance report for an interview session."""
    user_id = user_id.strip().lower()
    report_id = f"rep_{uuid.uuid4().hex[:10]}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Delete prior report for this session if re-finalizing
        cursor.execute("DELETE FROM interview_reports WHERE user_id = ? AND session_id = ?", (user_id, session_id))
        cursor.execute("""
            INSERT INTO interview_reports (
                report_id, session_id, user_id, target_role,
                overall_score, technical_score, problem_solving_score,
                communication_score, completeness_score, relevance_score,
                strengths, weaknesses, recommendations, question_reviews,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report_id, session_id, user_id, target_role,
            float(overall_score), float(technical_score), float(problem_solving_score),
            float(communication_score), float(completeness_score), float(relevance_score),
            json.dumps(strengths or []), json.dumps(weaknesses or []),
            json.dumps(recommendations or []), json.dumps(question_reviews or []),
            created_at
        ))

    # Mark session as completed
    update_interview_session(
        user_id=user_id,
        session_id=session_id,
        status="completed",
        completed_at=created_at,
        overall_score=overall_score,
        weak_topics=weaknesses or [],
        strong_topics=strengths or []
    )

    return True, report_id


def get_interview_report(user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the performance report for a session with strict user isolation."""
    user_id = user_id.strip().lower()
    rows = execute_query(
        "SELECT * FROM interview_reports WHERE user_id = ? AND session_id = ?",
        (user_id, session_id)
    )
    if not rows:
        return None
    d = dict(rows[0])
    try:
        d["strengths"] = json.loads(d.get("strengths") or "[]")
    except Exception:
        d["strengths"] = []
    try:
        d["weaknesses"] = json.loads(d.get("weaknesses") or "[]")
    except Exception:
        d["weaknesses"] = []
    try:
        d["recommendations"] = json.loads(d.get("recommendations") or "[]")
    except Exception:
        d["recommendations"] = []
    try:
        d["question_reviews"] = json.loads(d.get("question_reviews") or "[]")
    except Exception:
        d["question_reviews"] = []
    return d


def get_user_interview_reports(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve all performance reports for a user."""
    user_id = user_id.strip().lower()
    rows = execute_query(
        "SELECT * FROM interview_reports WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    )
    reports = []
    for r in rows:
        d = dict(r)
        try:
            d["strengths"] = json.loads(d.get("strengths") or "[]")
        except Exception:
            d["strengths"] = []
        try:
            d["weaknesses"] = json.loads(d.get("weaknesses") or "[]")
        except Exception:
            d["weaknesses"] = []
        try:
            d["recommendations"] = json.loads(d.get("recommendations") or "[]")
        except Exception:
            d["recommendations"] = []
        try:
            d["question_reviews"] = json.loads(d.get("question_reviews") or "[]")
        except Exception:
            d["question_reviews"] = []
        reports.append(d)
    return reports


# =========================================================
# 6. PROGRESS TRACKING & LONGITUDINAL ANALYTICS
# =========================================================

def get_interview_progress_analytics(user_id: str) -> Dict[str, Any]:
    """
    Calculate strictly factual longitudinal progress metrics:
    overall score progression, category trends, total interviews completed,
    and weak/strong topic tallies.
    """
    reports = get_user_interview_reports(user_id)
    # Reverse to chronological order (oldest -> newest) for charting
    chrono_reports = list(reversed(reports))

    if not reports:
        return {
            "has_data": False,
            "total_completed": 0,
            "latest_score": 0.0,
            "previous_score": 0.0,
            "score_delta": 0.0,
            "average_score": 0.0,
            "score_trend": [],
            "technical_trend": [],
            "problem_solving_trend": [],
            "communication_trend": [],
            "top_weak_topics": [],
            "top_strong_topics": [],
            "recent_reports": []
        }

    latest = reports[0]
    prev_score = reports[1]["overall_score"] if len(reports) > 1 else None
    latest_score = latest["overall_score"]
    delta = round(latest_score - prev_score, 1) if prev_score is not None else 0.0

    scores = [r["overall_score"] for r in reports]
    avg_score = round(sum(scores) / len(scores), 1)

    score_trend = [{"index": idx + 1, "date": r["created_at"][:10], "role": r["target_role"], "score": r["overall_score"]} for idx, r in enumerate(chrono_reports)]
    tech_trend = [{"index": idx + 1, "score": r.get("technical_score", 0.0)} for idx, r in enumerate(chrono_reports)]
    ps_trend = [{"index": idx + 1, "score": r.get("problem_solving_score", 0.0)} for idx, r in enumerate(chrono_reports)]
    comm_trend = [{"index": idx + 1, "score": r.get("communication_score", 0.0)} for idx, r in enumerate(chrono_reports)]

    # Aggregate weak & strong topic frequencies
    weak_map: Dict[str, int] = {}
    strong_map: Dict[str, int] = {}

    for r in reports:
        for w in r.get("weaknesses", []):
            if isinstance(w, str) and w.strip():
                clean_w = w.strip()
                weak_map[clean_w] = weak_map.get(clean_w, 0) + 1
        for s in r.get("strengths", []):
            if isinstance(s, str) and s.strip():
                clean_s = s.strip()
                strong_map[clean_s] = strong_map.get(clean_s, 0) + 1

    top_weak = sorted(weak_map.items(), key=lambda x: x[1], reverse=True)[:5]
    top_strong = sorted(strong_map.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "has_data": True,
        "total_completed": len(reports),
        "latest_score": latest_score,
        "previous_score": prev_score if prev_score is not None else latest_score,
        "score_delta": delta,
        "has_previous": prev_score is not None,
        "average_score": avg_score,
        "score_trend": score_trend,
        "technical_trend": tech_trend,
        "problem_solving_trend": ps_trend,
        "communication_trend": comm_trend,
        "top_weak_topics": [w[0] for w in top_weak],
        "top_strong_topics": [s[0] for s in top_strong],
        "recent_reports": reports[:5]
    }
