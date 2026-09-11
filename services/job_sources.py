"""
Job Sources Service
Manages live external APIs (Adzuna) and local curated opportunity catalog.
"""

import os
import requests
from typing import List, Dict, Any, Optional, Tuple

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

from database.connection import read_json_file
from services.job_normalizer import normalize_job

LOCAL_JOBS_FILE = "jobs.json"


def get_adzuna_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Retrieve Adzuna API credentials from Streamlit secrets or environment variables."""
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")

    if (not app_id or not app_key) and HAS_STREAMLIT:
        try:
            app_id = app_id or st.secrets.get("ADZUNA_APP_ID")
            app_key = app_key or st.secrets.get("ADZUNA_APP_KEY")
        except Exception:
            pass

    return (app_id.strip() if app_id else None, app_key.strip() if app_key else None)


def fetch_live_adzuna_jobs(
    keyword: str,
    location: str = "india",
    results_per_page: int = 20,
    timeout: int = 15
) -> List[Dict[str, Any]]:
    """Fetch live jobs from Adzuna API and return normalized results."""
    app_id, app_key = get_adzuna_credentials()
    if not app_id or not app_key:
        return []

    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": results_per_page,
        "what": keyword.strip(),
        "where": location.strip() if location else "india",
        "content-type": "application/json"
    }

    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        raw_results = data.get("results", [])
        return [normalize_job(j, default_source="Adzuna Live") for j in raw_results]
    except Exception as e:
        print(f"[Job Sources Warning] Adzuna API request error: {e}")
        return []


def fetch_local_catalog_jobs(
    keyword: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetch jobs from local curated jobs.json catalog and return normalized results."""
    raw_list = read_json_file(LOCAL_JOBS_FILE, default=[])
    normalized = [normalize_job(j, default_source="Curated Catalog") for j in raw_list]

    if not keyword and not location:
        return normalized

    k_clean = keyword.strip().lower() if keyword else ""
    l_clean = location.strip().lower() if location else ""

    filtered = []
    for job in normalized:
        title = job.get("title", "").lower()
        desc = job.get("description", "").lower()
        company = job.get("company", "").lower()
        loc = job.get("location", "").lower()

        match_k = not k_clean or (k_clean in title or k_clean in desc or k_clean in company)
        match_l = not l_clean or (l_clean in loc or "india" in loc)

        if match_k and match_l:
            filtered.append(job)

    return filtered
