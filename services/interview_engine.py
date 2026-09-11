"""
Interview Engine & State Machine
Orchestrates the active interview lifecycle: session initialization, answer submission,
adaptive question sequencing, pausing, resuming, and final report generation.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from database.repository import (
    create_interview_session,
    get_interview_session,
    update_interview_session,
    add_interview_question,
    get_interview_questions,
    save_interview_answer,
    get_interview_answers,
    save_interview_evaluation,
    get_interview_evaluations,
    save_interview_report,
    get_interview_report,
    get_resume,
    get_saved_jobs,
)
from services.interview_questions import (
    generate_first_question,
    generate_adaptive_next_question,
)
from services.interview_evaluator import evaluate_answer
from services.interview_recommendations import synthesize_session_report


def start_new_interview(
    user_id: str,
    target_role: str,
    interview_type: str = "Technical",
    difficulty: str = "Adaptive",
    interviewer_personality: str = "Professional",
    question_count: int = 5,
    duration_minutes: int = 15,
    resume_id: str = "",
    job_id: str = "",
    job_data: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Initialize a new interview session and generate the grounded first question.
    """
    user_id = user_id.strip().lower()
    if not target_role or not target_role.strip():
        return False, "Target role is required to begin an interview.", None

    resume_text = ""
    if resume_id:
        r_rec = get_resume(user_id, resume_id)
        if r_rec:
            resume_text = r_rec.get("text", "")

    job_description = ""
    if job_data:
        job_description = job_data.get("description") or job_data.get("job_description") or ""
    elif job_id:
        saved_list = get_saved_jobs(user_id)
        matched_job = next((j for j in saved_list if j.get("job_id") == job_id), None)
        if matched_job:
            job_description = matched_job.get("description", "")

    metadata = {
        "job_title": job_data.get("title", "") if job_data else "",
        "company": job_data.get("company", "") if job_data else "",
        "custom_notes": ""
    }

    ok, session_id = create_interview_session(
        user_id=user_id,
        target_role=target_role.strip(),
        interview_type=interview_type,
        difficulty=difficulty,
        interviewer_personality=interviewer_personality,
        question_count=question_count,
        duration_minutes=duration_minutes,
        resume_id=resume_id,
        job_id=job_id,
        metadata=metadata
    )

    if not ok:
        return False, session_id, None

    # Generate initial question
    first_q_data = generate_first_question(
        target_role=target_role.strip(),
        interview_type=interview_type,
        difficulty=difficulty,
        interviewer_personality=interviewer_personality,
        resume_text=resume_text,
        job_description=job_description
    )

    # Persist Question 1
    q_ok, q_id = add_interview_question(
        session_id=session_id,
        user_id=user_id,
        question_number=1,
        question_text=first_q_data["question_text"],
        category=first_q_data["category"],
        difficulty=first_q_data["difficulty"],
        context_origin=first_q_data["context_origin"]
    )

    if not q_ok:
        return False, "Failed to save initial interview question.", None

    first_q_data["question_id"] = q_id
    first_q_data["session_id"] = session_id

    session_state = get_interview_session_state(user_id, session_id)
    return True, session_id, session_state


def get_interview_session_state(user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve full aggregate state of an interview session:
    session metadata, all questions, answers, evaluations, and progress indicators.
    """
    user_id = user_id.strip().lower()
    session = get_interview_session(user_id, session_id)
    if not session:
        return None

    questions = get_interview_questions(session_id, user_id)
    answers = get_interview_answers(session_id, user_id)
    evaluations = get_interview_evaluations(session_id, user_id)

    total_q = session.get("question_count", 5)
    answered_count = len(answers)
    is_completed = (session.get("status") == "completed") or (answered_count >= total_q)

    # Current active question is the latest generated question if not finished
    current_q = None
    if not is_completed:
        if answered_count < len(questions):
            current_q = questions[answered_count]
        elif questions:
            current_q = questions[-1]

    progress_pct = min(100, int((answered_count / max(total_q, 1)) * 100))

    # Calculate live score average
    avg_score = 0.0
    if evaluations:
        avg_score = round(sum(e["overall_answer_score"] for e in evaluations) / len(evaluations), 1)

    return {
        "session": session,
        "session_id": session_id,
        "target_role": session.get("target_role", ""),
        "interview_type": session.get("interview_type", "Technical"),
        "difficulty": session.get("difficulty", "Adaptive"),
        "total_questions": total_q,
        "answered_count": answered_count,
        "current_question": current_q,
        "current_question_number": answered_count + 1 if not is_completed else total_q,
        "questions": questions,
        "answers": answers,
        "evaluations": evaluations,
        "is_completed": is_completed,
        "status": session.get("status", "in_progress"),
        "progress_pct": progress_pct,
        "live_score_average": avg_score
    }


def process_answer_submission(
    user_id: str,
    session_id: str,
    question_id: str,
    answer_text: str,
) -> Dict[str, Any]:
    """
    Evaluate user's submitted answer, update session analytics, and either generate
    the adaptive next question or finalize the session report.
    """
    user_id = user_id.strip().lower()
    session = get_interview_session(user_id, session_id)
    if not session:
        return {"success": False, "error": "Interview session not found."}

    questions = get_interview_questions(session_id, user_id)
    target_q = next((q for q in questions if q.get("question_id") == question_id), None)
    if not target_q:
        return {"success": False, "error": "Question not found in this session."}

    # 1. Save candidate answer
    a_ok, answer_id = save_interview_answer(
        question_id=question_id,
        session_id=session_id,
        user_id=user_id,
        answer_text=answer_text
    )
    if not a_ok:
        return {"success": False, "error": "Failed to save candidate answer."}

    # 2. Evaluate answer
    eval_result = evaluate_answer(
        question_text=target_q.get("question_text", ""),
        answer_text=answer_text,
        category=target_q.get("category", "Technical Knowledge"),
        difficulty=target_q.get("difficulty", "Medium"),
        target_role=session.get("target_role", "")
    )

    # 3. Persist evaluation
    save_interview_evaluation(
        answer_id=answer_id,
        session_id=session_id,
        user_id=user_id,
        overall_answer_score=eval_result["overall_answer_score"],
        technical_score=eval_result["technical_score"],
        relevance_score=eval_result["relevance_score"],
        completeness_score=eval_result["completeness_score"],
        clarity_score=eval_result["clarity_score"],
        problem_solving_score=eval_result["problem_solving_score"],
        feedback=eval_result["feedback"],
        strengths=eval_result["strengths"],
        improvements=eval_result["improvements"],
        detected_topics=eval_result["detected_topics"],
        is_strong=eval_result["is_strong"]
    )

    # 4. Check if interview is finished
    current_answers = get_interview_answers(session_id, user_id)
    total_allowed = session.get("question_count", 5)

    if len(current_answers) >= total_allowed:
        # Finalize report
        finalize_interview_session(user_id, session_id)
        return {
            "success": True,
            "is_completed": True,
            "evaluation": eval_result,
            "next_question": None,
            "message": "Interview completed! Generating final report..."
        }

    # 5. Generate Adaptive Next Question
    resume_text = ""
    if session.get("resume_id"):
        r_rec = get_resume(user_id, session["resume_id"])
        if r_rec:
            resume_text = r_rec.get("text", "")

    job_description = ""
    if session.get("job_id"):
        saved_list = get_saved_jobs(user_id)
        matched_job = next((j for j in saved_list if j.get("job_id") == session["job_id"]), None)
        if matched_job:
            job_description = matched_job.get("description", "")

    asked_concepts = [q.get("concept") or q.get("context_origin") for q in questions]

    next_q_num = len(current_answers) + 1
    next_q_data = generate_adaptive_next_question(
        target_role=session.get("target_role", "Software Engineer"),
        question_number=next_q_num,
        total_questions=total_allowed,
        previous_question=target_q,
        last_evaluation=eval_result,
        interview_type=session.get("interview_type", "Technical"),
        difficulty=session.get("difficulty", "Adaptive"),
        interviewer_personality=session.get("interviewer_personality", "Professional"),
        resume_text=resume_text,
        job_description=job_description,
        asked_concepts=asked_concepts
    )

    q_ok, next_q_id = add_interview_question(
        session_id=session_id,
        user_id=user_id,
        question_number=next_q_num,
        question_text=next_q_data["question_text"],
        category=next_q_data["category"],
        difficulty=next_q_data["difficulty"],
        context_origin=next_q_data["context_origin"]
    )

    next_q_data["question_id"] = next_q_id
    next_q_data["session_id"] = session_id

    # Update session pointer
    update_interview_session(
        user_id=user_id,
        session_id=session_id,
        current_question_index=next_q_num - 1
    )

    return {
        "success": True,
        "is_completed": False,
        "evaluation": eval_result,
        "next_question": next_q_data,
        "message": "Answer evaluated. Next question ready."
    }


def finalize_interview_session(user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    """Synthesize cumulative evaluation metrics and persist the final performance report."""
    user_id = user_id.strip().lower()
    session = get_interview_session(user_id, session_id)
    if not session:
        return None

    questions = get_interview_questions(session_id, user_id)
    answers = get_interview_answers(session_id, user_id)
    evaluations = get_interview_evaluations(session_id, user_id)

    report_data = synthesize_session_report(
        target_role=session.get("target_role", ""),
        questions=questions,
        answers=answers,
        evaluations=evaluations
    )

    save_interview_report(
        session_id=session_id,
        user_id=user_id,
        target_role=session.get("target_role", "Professional"),
        overall_score=report_data["overall_score"],
        technical_score=report_data["technical_score"],
        problem_solving_score=report_data["problem_solving_score"],
        communication_score=report_data["communication_score"],
        completeness_score=report_data["completeness_score"],
        relevance_score=report_data["relevance_score"],
        strengths=report_data["strengths"],
        weaknesses=report_data["weaknesses"],
        recommendations=report_data["recommendations"],
        question_reviews=report_data["question_reviews"]
    )

    return get_interview_report(user_id, session_id)


def pause_interview(user_id: str, session_id: str) -> bool:
    """Pause an in-progress interview session so user can return later."""
    return update_interview_session(user_id, session_id, status="paused")


def resume_interview(user_id: str, session_id: str) -> bool:
    """Resume a paused interview session."""
    return update_interview_session(user_id, session_id, status="in_progress")
