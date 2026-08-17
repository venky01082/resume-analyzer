import json


# =========================================================
# LOAD JOBS
# =========================================================

def load_jobs():

    with open(
        "jobs.json",
        "r",
        encoding="utf-8"
    ) as file:

        jobs = json.load(file)

    return jobs


# =========================================================
# RECOMMEND JOBS
# =========================================================

def recommend_jobs(
    resume_skills,
    jobs
):

    recommendations = []

    for job in jobs:

        job_skills = job.get(
            "skills",
            []
        )

        resume_lower = [
            skill.lower()
            for skill in resume_skills
        ]

        matching_skills = []

        missing_skills = []

        for skill in job_skills:

            if skill.lower() in resume_lower:

                matching_skills.append(
                    skill
                )

            else:

                missing_skills.append(
                    skill
                )

        if job_skills:

            score = round(
                (
                    len(matching_skills)
                    /
                    len(job_skills)
                ) * 100
            )

        else:

            score = 0

        recommendations.append({

            "job": job,

            "score": score,

            "matching_skills": matching_skills,

            "missing_skills": missing_skills

        })

    # Highest score first

    recommendations.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return recommendations