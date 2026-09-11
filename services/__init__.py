"""
Services Package Interface
Exposes job normalization, deduplication, search, and recommendation services.
"""

from services.job_normalizer import normalize_job, detect_remote_status
from services.job_deduplicator import deduplicate_jobs
from services.job_sources import fetch_live_adzuna_jobs, fetch_local_catalog_jobs, get_adzuna_credentials
from services.job_search import search_jobs
from services.job_recommendation import calculate_job_recommendation_score, recommend_jobs_for_user

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
]
