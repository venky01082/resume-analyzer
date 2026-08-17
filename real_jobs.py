import requests
import streamlit as st


# =========================================================
# SEARCH REAL JOBS
# =========================================================

def search_real_jobs(
    keyword,
    location="india",
    results_per_page=20
):

    app_id = st.secrets["ADZUNA_APP_ID"]
    app_key = st.secrets["ADZUNA_APP_KEY"]

    url = (
        "https://api.adzuna.com/v1/api/"
        f"jobs/in/search/1"
    )

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": results_per_page,
        "what": keyword,
        "where": location,
        "content-type": "application/json"
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    return data.get(
        "results",
        []
    )


# =========================================================
# CONVERT API JOB TO OUR FORMAT
# =========================================================

def normalize_job(job):

    location = job.get(
        "location",
        {}
    )

    company = job.get(
        "company",
        {}
    )

    return {

        "id": job.get(
            "id",
            ""
        ),

        "title": job.get(
            "title",
            "Unknown"
        ),

        "company": company.get(
            "display_name",
            "Unknown"
        ),

        "location": location.get(
            "display_name",
            "India"
        ),

        "description": job.get(
            "description",
            ""
        ),

        "application_url": job.get(
            "redirect_url",
            ""
        ),

        "salary_min": job.get(
            "salary_min"
        ),

        "salary_max": job.get(
            "salary_max"
        ),

        "contract_type": job.get(
            "contract_type",
            ""
        ),

        "contract_time": job.get(
            "contract_time",
            ""
        )
    }


# =========================================================
# SEARCH AND NORMALIZE
# =========================================================

def get_real_jobs(
    keyword,
    location="india",
    results_per_page=20
):

    jobs = search_real_jobs(
        keyword,
        location,
        results_per_page
    )

    normalized_jobs = []

    for job in jobs:

        normalized_jobs.append(
            normalize_job(job)
        )

    return normalized_jobs