import re
import spacy


nlp = spacy.load(
    "en_core_web_sm"
)


# =========================================================
# NAME
# =========================================================

def extract_name(text):

    lines = [

        line.strip()

        for line in text.splitlines()

        if line.strip()

    ]

    for line in lines[:10]:

        if line.lower() in [

            "resume",
            "cv",
            "curriculum vitae",
            "profile"

        ]:

            continue

        if "@" in line:

            continue

        if re.search(
            r'\d',
            line
        ):

            continue

        words = line.split()

        if 2 <= len(words) <= 4:

            return line

    return "Not Found"


# =========================================================
# EXPERIENCE
# =========================================================

def extract_experience(text):

    lines = text.splitlines()

    experience = []

    capturing = False

    stop_sections = [

        "education",
        "skills",
        "projects",
        "certifications",
        "achievements",
        "hobbies",
        "interests"

    ]

    for line in lines:

        clean_line = line.strip()

        if clean_line.lower() in [

            "experience",
            "work experience",
            "professional experience"

        ]:

            capturing = True

            continue

        if capturing:

            if clean_line.lower() in stop_sections:

                break

            if clean_line:

                experience.append(
                    clean_line
                )

    return experience


# =========================================================
# EDUCATION
# =========================================================

def extract_education_details(text):

    lines = text.splitlines()

    education = []

    capturing = False

    stop_sections = [

        "skills",
        "projects",
        "experience",
        "certifications",
        "achievements",
        "hobbies",
        "interests"

    ]

    for line in lines:

        clean_line = line.strip()

        if clean_line.lower() in [

            "education",
            "academic qualifications",
            "educational qualifications"

        ]:

            capturing = True

            continue

        if capturing:

            if clean_line.lower() in stop_sections:

                break

            if clean_line:

                education.append(
                    clean_line
                )

    return education


# =========================================================
# PROJECTS
# =========================================================

def extract_projects(text):

    lines = text.splitlines()

    projects = []

    capturing = False

    stop_sections = [

        "skills",
        "education",
        "experience",
        "certifications",
        "achievements",
        "hobbies",
        "interests"

    ]

    for line in lines:

        clean_line = line.strip()

        if clean_line.lower() in [

            "projects",
            "academic projects",
            "personal projects"

        ]:

            capturing = True

            continue

        if capturing:

            if clean_line.lower() in stop_sections:

                break

            if clean_line:

                projects.append(
                    clean_line
                )

    return projects