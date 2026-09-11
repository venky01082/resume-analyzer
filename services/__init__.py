"""
Services Package Interface
Exposes job normalization, deduplication, search, and recommendation services.
"""

from services.job_normalizer import normalize_job, detect_remote_status
from services.job_deduplicator import deduplicate_jobs
from services.job_sources import fetch_live_adzuna_jobs, fetch_local_catalog_jobs, get_adzuna_credentials
from services.job_search import search_jobs
from services.job_recommendation import calculate_job_recommendation_score, recommend_jobs_for_user
from services.interview_questions import generate_first_question, generate_adaptive_next_question
from services.interview_evaluator import evaluate_answer
from services.interview_recommendations import synthesize_session_report, generate_improvement_interview_plan
from services.interview_engine import (
    start_new_interview,
    get_interview_session_state,
    process_answer_submission,
    finalize_interview_session,
    pause_interview,
    resume_interview,
)
from services.voice_provider import (
    SpeechToTextProvider,
    TextToSpeechProvider,
    WebSpeechBridgeProvider,
    analyze_observable_speech_metrics,
    get_web_speech_input_html,
)

__all__ = [
    "normalize_job",
    "detect_remote_status",
    "deduplicate_jobs",
    "fetch_live_adzuna_jobs",
    "fetch_local_catalog_jobs",
    "get_adzuna_credentials",
    "search_jobs",
    "calculate_job_recommendation_score",
    "recommend_jobs_for_user",
    "generate_first_question",
    "generate_adaptive_next_question",
    "evaluate_answer",
    "synthesize_session_report",
    "generate_improvement_interview_plan",
    "start_new_interview",
    "get_interview_session_state",
    "process_answer_submission",
    "finalize_interview_session",
    "pause_interview",
    "resume_interview",
    "SpeechToTextProvider",
    "TextToSpeechProvider",
    "WebSpeechBridgeProvider",
    "analyze_observable_speech_metrics",
    "get_web_speech_input_html",
]

