# =========================================================
# JOB MATCHER
# =========================================================


SKILLS_DATABASE = [

    "Python",
    "Java",
    "C",
    "C++",
    "SQL",

    "HTML",
    "CSS",
    "JavaScript",

    "Machine Learning",
    "Deep Learning",
    "Artificial Intelligence",
    "Data Science",
    "Data Analysis",

    "Pandas",
    "NumPy",
    "TensorFlow",
    "PyTorch",
    "Scikit-learn",

    "Power BI",
    "Excel",
    "Git",
    "GitHub",
    "Tableau",

    "AWS",
    "Azure",
    "Google Cloud",

    "Statistics",
    "Data Visualization",

    "NLP",
    "Computer Vision",

    "Matplotlib",
    "Seaborn",

    "MongoDB",
    "MySQL",
    "PostgreSQL",

    "FastAPI",
    "Flask",
    "Django"
]


# =========================================================
# EXTRACT JOB SKILLS
# =========================================================

def extract_job_skills(job_description):

    found_skills = []

    text = job_description.lower()

    for skill in SKILLS_DATABASE:

        if skill.lower() in text:

            if skill not in found_skills:

                found_skills.append(
                    skill
                )

    return found_skills


# =========================================================
# COMPARE RESUME AND JOB SKILLS
# =========================================================

def compare_skills(
    resume_skills,
    job_skills
):

    resume_lower = [

        skill.lower()

        for skill in resume_skills

    ]

    matching = []

    missing = []

    for skill in job_skills:

        if skill.lower() in resume_lower:

            matching.append(
                skill
            )

        else:

            missing.append(
                skill
            )

    return matching, missing


# =========================================================
# CALCULATE MATCH SCORE
# =========================================================

def calculate_match_score(
    matching_skills,
    job_skills
):

    if not job_skills:

        return 0

    score = (

        len(matching_skills)
        /
        len(job_skills)

    ) * 100

    return round(
        score
    )


# =========================================================
# GENERATE RECOMMENDATION
# =========================================================

def generate_recommendation(
    score
):

    if score >= 90:

        return (
            "Excellent match! "
            "Your skills strongly match this job."
        )

    elif score >= 75:

        return (
            "Very good match. "
            "You meet most of the required skills."
        )

    elif score >= 60:

        return (
            "Good match, but you should improve "
            "some of the missing skills."
        )

    elif score >= 40:

        return (
            "Partial match. "
            "Consider developing the missing skills."
        )

    else:

        return (
            "Low match. "
            "This job requires several skills "
            "that are missing from your resume."
        )