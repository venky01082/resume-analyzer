"""
Job Deduplicator Service
Identifies and removes duplicate job postings across multiple sources.
"""

import re
from typing import List, Dict, Any, Set


def _normalize_token_key(title: str, company: str) -> str:
    """Generate a sanitized canonical key from title and company."""
    t = re.sub(r"[^a-zA-Z0-9]", "", title.lower())
    c = re.sub(r"[^a-zA-Z0-9]", "", company.lower())
    return f"{c}_{t}"


def deduplicate_jobs(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates a list of normalized job dictionaries based on unique ID
    and canonical (company, title) pairing while preserving original order.
    """
    seen_ids: Set[str] = set()
    seen_keys: Set[str] = set()
    unique_jobs: List[Dict[str, Any]] = []

    for job in jobs:
        jid = str(job.get("job_id") or job.get("id") or "").strip()
        title = job.get("title", "")
        company = job.get("company", "")
        key = _normalize_token_key(title, company)

        if jid and jid in seen_ids:
            continue
        if key and key in seen_keys:
            continue

        if jid:
            seen_ids.add(jid)
        if key:
            seen_keys.add(key)

        unique_jobs.append(job)

    return unique_jobs
