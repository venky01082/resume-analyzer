"""
Job Search Orchestration Service
Coordinates multi-source job searching, filtering, deduplication, and pagination.
"""

from typing import List, Dict, Any, Optional
from services.job_sources import fetch_live_adzuna_jobs, fetch_local_catalog_jobs, get_adzuna_credentials
from services.job_deduplicator import deduplicate_jobs


def search_jobs(
    keyword: str,
    location: str = "india",
    remote_filter: str = "Any",  # Any, Remote, Hybrid, On-site
    limit: int = 20,
    include_live: bool = True,
    include_catalog: bool = True
) -> List[Dict[str, Any]]:
    """
    Unified search querying live job APIs and curated catalog,
    applying remote/location filters, and removing duplicates.
    """
    raw_results: List[Dict[str, Any]] = []

    # 1. Fetch live jobs if enabled and credentials exist
    if include_live:
        app_id, _ = get_adzuna_credentials()
        if app_id:
            live_jobs = fetch_live_adzuna_jobs(keyword, location, results_per_page=limit)
            raw_results.extend(live_jobs)

    # 2. Fetch local catalog jobs
    if include_catalog or not raw_results:
        catalog_jobs = fetch_local_catalog_jobs(keyword, location)
        raw_results.extend(catalog_jobs)

    # 3. Deduplicate
    unique_jobs = deduplicate_jobs(raw_results)

    # 4. Filter by Remote preference if specified
    if remote_filter and remote_filter != "Any":
        r_clean = remote_filter.lower()
        filtered = [
            j for j in unique_jobs
            if j.get("remote_status", "").lower() == r_clean
            or (r_clean == "remote" and "remote" in j.get("description", "").lower())
        ]
        if filtered:
            unique_jobs = filtered

    return unique_jobs[:limit]
