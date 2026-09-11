"""
User-Specific Application Analytics Database Module
Calculates real metrics, funnels, and trends for a specific user.
Strictly adheres to: DO NOT FABRICATE DATA.
"""

from typing import Dict, Any, List
from collections import Counter
from database.applications import get_applications, get_status_counts
from database.jobs import get_saved_jobs
from database.resumes import get_resumes


def calculate_user_analytics(user_id: str) -> Dict[str, Any]:
    """Calculate comprehensive, factual analytics for a specific user."""
    apps = get_applications(user_id)
    saved_jobs = get_saved_jobs(user_id)
    resumes = get_resumes(user_id)

    total_apps = len(apps)
    total_saved = len(saved_jobs)
    total_resumes = len(resumes)

    status_counts = get_status_counts(apps)

    # Active pipeline stages
    interview_count = (
        status_counts.get("Interview", 0) +
        status_counts.get("Technical Round", 0) +
        status_counts.get("HR Round", 0)
    )
    offer_count = status_counts.get("Offer", 0)
    rejected_count = status_counts.get("Rejected", 0)
    screening_count = status_counts.get("Screening", 0)

    # Rate calculations
    submitted_apps = [a for a in apps if a.get("status") != "Saved"]
    total_submitted = len(submitted_apps)

    if total_submitted > 0:
        responded_count = total_submitted - status_counts.get("Applied", 0)
        response_rate = round((responded_count / total_submitted) * 100, 1)
        interview_rate = round((interview_count / total_submitted) * 100, 1)
        offer_rate = round((offer_count / total_submitted) * 100, 1)
        rejection_rate = round((rejected_count / total_submitted) * 100, 1)
    else:
        response_rate = 0.0
        interview_rate = 0.0
        offer_rate = 0.0
        rejection_rate = 0.0

    # Scores
    scores = [a.get("score", 0) for a in apps if isinstance(a.get("score"), (int, float)) and a.get("score", 0) > 0]
    avg_match_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    # Group by Company
    companies = [a.get("company", "Unknown") for a in apps if a.get("company")]
    top_companies = dict(Counter(companies).most_common(8))

    # Group by Role / Title
    titles = [a.get("title", "Unknown") for a in apps if a.get("title")]
    top_roles = dict(Counter(titles).most_common(8))

    # Group by Month (Trend)
    month_counts = Counter()
    for a in apps:
        app_date = a.get("applied_date", "")
        if len(app_date) >= 7:
            month_counts[app_date[:7]] += 1
    monthly_trend = dict(sorted(month_counts.items()))

    return {
        "total_applications": total_apps,
        "total_submitted": total_submitted,
        "submitted_applications": total_submitted,
        "total_saved_jobs": total_saved,
        "total_resumes": total_resumes,
        "status_counts": status_counts,
        "status_distribution": status_counts,
        "interview_count": interview_count,
        "active_interviews": interview_count,
        "offer_count": offer_count,
        "total_offers": offer_count,
        "rejected_count": rejected_count,
        "total_rejections": rejected_count,
        "screening_count": screening_count,
        "response_rate": response_rate,
        "interview_rate": interview_rate,
        "offer_rate": offer_rate,
        "rejection_rate": rejection_rate,
        "avg_match_score": avg_match_score,
        "top_companies": top_companies,
        "top_roles": top_roles,
        "monthly_trend": monthly_trend
    }

