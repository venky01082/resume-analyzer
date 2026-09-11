"""
Core business logic for AI Job Application Assistant.
Preserves all existing functions, models, algorithms, and data structures.
"""

import os
import re
import json
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, date
import streamlit as st

# Internal imports from existing project files
from resume_parser import extract_text
from nlp_parser import (
    extract_name,
    extract_experience,
    extract_education_details,
    extract_projects,
)
from job_matcher import (
    extract_job_skills,
    compare_skills,
    calculate_match_score,
    generate_recommendation,
    SKILLS_DATABASE,
)
from job_database import load_jobs, recommend_jobs
from real_jobs import get_real_jobs
from application_tracker import (
    load_applications,
    save_applications,
    add_application,
    update_application_status,
    update_application,
    delete_application,
    STATUS_OPTIONS,
    PRIORITY_OPTIONS,
    get_status_counts,
    get_follow_up_items,
    get_overdue_follow_ups,
    get_today_follow_ups,
    migrate_application_file,
)


# =========================================================
# AUTHENTICATION & USER PROFILE
# =========================================================

USER_FILE = "users.json"


def auth_load_users():
    if not os.path.exists(USER_FILE):
        return {}
    try:
        with open(USER_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def auth_save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4, ensure_ascii=False)


def auth_hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200_000
    )
    return (
        base64.b64encode(salt).decode("utf-8"),
        base64.b64encode(password_hash).decode("utf-8")
    )


def auth_verify_password(password, salt_b64, hash_b64):
    try:
        salt = base64.b64decode(salt_b64.encode("utf-8"))
        expected = base64.b64decode(hash_b64.encode("utf-8"))
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            200_000
        )
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def auth_create_user(
    username, password, full_name="", email="", phone="",
    location="", target_roles="", skills="", experience="",
    education="", linkedin="", github="", portfolio=""
):
    username = username.strip().lower()
    if not username or not password:
        return False, "Username and password are required."
    users = auth_load_users()
    if username in users:
        return False, "Username already exists."
    if len(username) < 3:
        return False, "Username must contain at least 3 characters."
    if len(password) < 6:
        return False, "Password must contain at least 6 characters."

    salt, password_hash = auth_hash_password(password)
    users[username] = {
        "username": username,
        "password_hash": password_hash,
        "password_salt": salt,
        "profile": {
            "full_name": full_name.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "location": location.strip(),
            "target_roles": target_roles.strip(),
            "skills": skills.strip(),
            "experience": experience.strip(),
            "education": education.strip(),
            "linkedin": linkedin.strip(),
            "github": github.strip(),
            "portfolio": portfolio.strip()
        }
    }
    auth_save_users(users)
    return True, "Account created successfully."


def auth_login(username, password):
    username = username.strip().lower()
    users = auth_load_users()
    if username not in users:
        return False
    user = users[username]
    return auth_verify_password(
        password,
        user.get("password_salt", ""),
        user.get("password_hash", "")
    )


def auth_get_profile(username):
    users = auth_load_users()
    if username not in users:
        return {}
    return users[username].get("profile", {})


def auth_update_profile(
    username, full_name, email, phone, location,
    target_roles, skills, experience, education,
    linkedin, github, portfolio
):
    users = auth_load_users()
    if username not in users:
        return False
    users[username]["profile"] = {
        "full_name": full_name.strip(),
        "email": email.strip(),
        "phone": phone.strip(),
        "location": location.strip(),
        "target_roles": target_roles.strip(),
        "skills": skills.strip(),
        "experience": experience.strip(),
        "education": education.strip(),
        "linkedin": linkedin.strip(),
        "github": github.strip(),
        "portfolio": portfolio.strip()
    }
    auth_save_users(users)
    return True


def auth_delete_account(username):
    users = auth_load_users()
    if username not in users:
        return False
    del users[username]
    auth_save_users(users)
    return True


# =========================================================
# RESUME PARSER & SCORING HELPERS
# =========================================================

def extract_email(text):
    m = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
    return m.group() if m else "Not Found"


def extract_phone(text):
    m = re.search(r'(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)', text)
    return m.group() if m else "Not Found"


def extract_skills(text):
    database = [
        "Python", "Java", "C", "C++", "SQL", "HTML", "CSS", "JavaScript",
        "Machine Learning", "Deep Learning", "Artificial Intelligence",
        "Data Science", "Data Analysis", "Pandas", "NumPy", "TensorFlow",
        "PyTorch", "Scikit-learn", "Power BI", "Excel", "Tableau", "Git",
        "GitHub", "AWS", "Azure", "Google Cloud", "Statistics",
        "Data Visualization", "NLP", "Computer Vision", "Matplotlib", "Seaborn",
        "MongoDB", "MySQL", "PostgreSQL", "FastAPI", "Flask", "Django",
        "OpenCV", "R", "Spark", "Hadoop", "Docker", "Kubernetes"
    ]
    lower = text.lower()
    return [skill for skill in database if skill.lower() in lower]


def extract_section(text, names):
    lines = text.splitlines()
    wanted = {x.lower() for x in names}
    stops = {
        "skills", "technical skills", "education", "academic qualifications",
        "educational qualifications", "projects", "academic projects",
        "personal projects", "experience", "work experience",
        "professional experience", "certifications", "certificates",
        "achievements", "hobbies", "interests", "languages", "declaration",
        "objective", "career objective", "summary", "profile"
    }
    result, capturing = [], False
    for line in lines:
        clean = line.strip()
        if not clean:
            continue
        low = clean.lower()
        if low in wanted:
            capturing = True
            continue
        if capturing and low in stops:
            break
        if capturing:
            result.append(clean)
    return result


def resume_score(text, skills, education, projects, experience, certifications):
    score = min(len(skills) * 2.5, 25)
    score += 15 if education else 0
    score += min(len(projects) * 5, 20)
    score += 15 if experience else 0
    score += min(len(certifications) * 5, 10)
    lower = text.lower()
    sections = ["skills", "education", "projects", "experience", "certifications"]
    score += sum(3 for section in sections if section in lower)
    return round(min(score, 100))


def missing_skills(skills):
    recommended = [
        "Python", "SQL", "Machine Learning", "Deep Learning", "Pandas",
        "NumPy", "Scikit-learn", "Power BI", "Excel", "Git", "GitHub",
        "Statistics", "Data Visualization", "TensorFlow", "PyTorch"
    ]
    have = {x.lower() for x in skills}
    return [x for x in recommended if x.lower() not in have]


def suggestions(score, skills, projects, experience, certifications):
    result = []
    if len(skills) < 5:
        result.append("Add more relevant technical skills.")
    if len(projects) < 2:
        result.append("Add at least two strong technical projects.")
    if not experience:
        result.append("Add internship, training or practical experience.")
    if not certifications:
        result.append("Add relevant certifications or courses.")
    if "GitHub" not in skills:
        result.append("Add your GitHub profile and project repositories.")
    if score < 60:
        result.append("Improve measurable achievements, projects and relevant keywords.")
    elif score < 80:
        result.append("Tailor your resume keywords to each target job.")
    else:
        result.append("Your resume structure is good; tailor it to each job description.")
    return result


def calculate_detailed_resume_health(text, skills=None, education=None, projects=None, experience=None, certifications=None):
    """
    Computes deep, multi-metric resume health breakdown and detects defects:
    weak action verbs, missing metrics, paragraph bloat, and missing links.
    Auto-extracts missing components from text when omitted.
    """
    if skills is None:
        skills = extract_skills(text)
    if education is None:
        education = extract_education_details(text)
    if projects is None:
        projects = extract_section(text, ["Projects", "Project"])
    if experience is None:
        experience = extract_section(text, ["Experience", "Work Experience", "Employment"])
    if certifications is None:
        certifications = extract_section(text, ["Certifications", "Certificates"])

    lower = text.lower()
    words = re.findall(r'\b[a-z0-9+#.-]+\b', lower)
    word_count = len(words)

    # 1. Component Scores (0 - 100%)
    skills_score_val = min(100, round((len(skills) / 8) * 100))
    education_score_val = 100 if education else 30
    projects_score_val = min(100, len(projects) * 35) if projects else 25
    experience_score_val = 100 if experience else (60 if projects else 30)

    # ATS Structure Score
    standard_sections = ["skills", "education", "experience", "projects", "certifications"]
    sections_found = sum(1 for s in standard_sections if s in lower)
    ats_score_val = round((sections_found / len(standard_sections)) * 100)

    # Keyword Density Score
    tech_keywords = ["python", "sql", "data", "machine learning", "analysis", "git", "cloud", "model", "pipeline"]
    kw_hits = sum(1 for k in tech_keywords if k in lower)
    keyword_score_val = min(100, round((kw_hits / len(tech_keywords)) * 100 + len(skills) * 3))

    # Formatting Score
    formatting_score_val = 100
    if word_count < 250:
        formatting_score_val -= 30
    elif word_count > 1200:
        formatting_score_val -= 20
    bullet_count = text.count("•") + text.count("- ") + text.count("* ")
    if bullet_count < 4:
        formatting_score_val -= 25
    formatting_score_val = max(20, min(formatting_score_val, 100))

    # Completeness Score
    completeness_score_val = 30
    if "@" in text:
        completeness_score_val += 20
    if re.search(r'\b\d{10}\b|\+91', text):
        completeness_score_val += 15
    if "linkedin" in lower:
        completeness_score_val += 15
    if "github" in lower or "portfolio" in lower:
        completeness_score_val += 20
    completeness_score_val = min(100, completeness_score_val)

    # Overall Health Score (Weighted)
    health_overall = round(
        skills_score_val * 0.25 +
        ats_score_val * 0.20 +
        experience_score_val * 0.15 +
        projects_score_val * 0.15 +
        keyword_score_val * 0.10 +
        formatting_score_val * 0.08 +
        completeness_score_val * 0.07
    )

    # 2. Defect Detection
    weak_phrases = ["worked on", "handled", "helped", "assisted with", "responsible for", "duties included", "involved in"]
    detected_weak_verbs = [p for p in weak_phrases if p in lower]

    strong_verbs = ["architected", "engineered", "implemented", "optimized", "developed", "built", "deployed", "spearheaded", "automated", "delivered", "designed", "streamlined"]
    detected_strong_verbs = [v for v in strong_verbs if v in lower]

    # Detect missing metrics (check if numbers, percentages, or scale appear in bullet points)
    metric_pattern = re.compile(r'\b\d+%(?!\w)|\b\d+[,.]?\d*\s*(?:percent|users|clients|records|databases|uptime|x|ms|k|m|\+)?\b|\$\d+|\b\d+\+', re.IGNORECASE)
    quantified_bullets = [line.strip() for line in text.split("\n") if line.strip().startswith(("-", "•", "*")) and metric_pattern.search(line)]
    has_metrics = len(quantified_bullets) > 0

    # Detect paragraph bloat (> 80 words without line breaks)
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip().split()) > 75]
    has_long_paragraphs = len(paragraphs) > 0

    # Detect missing links
    missing_links = []
    links_found = [m for m in ["linkedin.com", "github.com", "http", ".dev", ".io"] if m in lower]
    if "linkedin.com" not in lower:
        missing_links.append("LinkedIn profile URL")
    if "github.com" not in lower:
        missing_links.append("GitHub repository link")

    # Actionable suggestions
    health_recommendations = []
    if detected_weak_verbs:
        health_recommendations.append(f"Replace passive verbs like '{detected_weak_verbs[0]}' with impact action verbs (e.g., 'Engineered', 'Optimized', 'Automated').")
    if not has_metrics:
        health_recommendations.append("Quantify your project results with numbers or percentages (e.g., 'Improved accuracy by 14%', 'Reduced query latency by 35%').")
    if has_long_paragraphs:
        health_recommendations.append("Break down dense paragraphs into concise, punchy bullet points of 1-2 lines each.")
    if missing_links:
        health_recommendations.append(f"Add direct links to your {', '.join(missing_links)} in the header.")
    if len(skills) < 6:
        health_recommendations.append("Expand technical competencies section with verified tools, frameworks, and databases.")

    return {
        "score": health_overall,
        "overall_health": health_overall,
        "breakdown": {
            "Skills": skills_score_val,
            "ATS Compatibility": ats_score_val,
            "Experience": experience_score_val,
            "Projects": projects_score_val,
            "Education": education_score_val,
            "Keyword Density": keyword_score_val,
            "Formatting & Brevity": formatting_score_val,
        },
        "skills_score": skills_score_val,
        "ats_score": ats_score_val,
        "experience_score": experience_score_val,
        "projects_score": projects_score_val,
        "education_score": education_score_val,
        "keyword_score": keyword_score_val,
        "formatting_score": formatting_score_val,
        "completeness_score": completeness_score_val,
        "weak_verbs": detected_weak_verbs,
        "strong_verbs": detected_strong_verbs,
        "strong_verbs_detected": detected_strong_verbs,
        "has_metrics": has_metrics,
        "quantified_bullets": quantified_bullets,
        "has_long_paragraphs": has_long_paragraphs,
        "missing_links": missing_links,
        "links_found": links_found,
        "recommendations": health_recommendations
    }



# =========================================================
# STEP 11 - ADVANCED ATS ANALYZER
# =========================================================

def normalize_ats_text(value):
    value = value.lower()
    value = re.sub(r"[\u2010-\u2015]", "-", value)
    value = re.sub(r"[^a-z0-9+#.\-/ ]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def contains_ats_term(text, term):
    normalized_text = normalize_ats_text(text)
    normalized_term = normalize_ats_text(term)
    if normalized_term in normalized_text:
        return True
    variations = {
        "machine learning": ["ml"],
        "artificial intelligence": ["ai"],
        "natural language processing": ["nlp"],
        "computer vision": ["cv"],
        "data analysis": ["data analytics"],
        "data analytics": ["data analysis"],
        "scikit-learn": ["sklearn", "scikit learn"],
        "power bi": ["microsoft power bi"],
        "google cloud": ["gcp"],
        "generative ai": ["genai", "gen ai"],
        "javascript": ["js"],
        "typescript": ["ts"],
        "c++": ["cpp"],
        "node.js": ["nodejs", "node js"],
        "postgresql": ["postgres"],
        "rest api": ["rest apis"],
    }
    for variation in variations.get(normalized_term, []):
        if variation in normalized_text:
            return True
    return False


def extract_ats_keywords(job_text):
    keyword_groups = {
        "Programming": [
            "Python", "Java", "C", "C++", "C#", "R",
            "JavaScript", "TypeScript", "Go", "PHP"
        ],
        "Data": [
            "SQL", "MySQL", "PostgreSQL", "MongoDB",
            "Oracle", "Excel", "Power BI", "Tableau",
            "Pandas", "NumPy", "Statistics",
            "Data Analysis", "Data Analytics",
            "Data Visualization", "Matplotlib", "Seaborn",
            "ETL", "Spark", "Hadoop"
        ],
        "AI/ML": [
            "Machine Learning", "Deep Learning",
            "Artificial Intelligence", "Generative AI",
            "Natural Language Processing", "Computer Vision",
            "Scikit-learn", "TensorFlow", "PyTorch",
            "Keras", "OpenCV", "NLP", "MLOps",
            "LLM", "Large Language Models", "RAG"
        ],
        "Cloud/DevOps": [
            "AWS", "Azure", "Google Cloud", "GCP",
            "Vertex AI", "Docker", "Kubernetes",
            "Linux", "Git", "GitHub", "CI/CD"
        ],
        "Web/Backend": [
            "HTML", "CSS", "React", "Angular",
            "Node.js", "Django", "Flask", "FastAPI",
            "REST API", "API", "Spring Boot"
        ],
        "Soft Skills": [
            "Communication", "Leadership", "Teamwork",
            "Problem Solving", "Analytical Skills",
            "Time Management", "Collaboration"
        ]
    }
    found = {}
    for group, terms in keyword_groups.items():
        group_terms = []
        for term in terms:
            if contains_ats_term(job_text, term):
                group_terms.append(term)
        if group_terms:
            found[group] = group_terms
    return found


def extract_job_role_keywords(job_text):
    roles = [
        "Data Analyst", "Data Scientist", "Machine Learning Engineer",
        "AI Engineer", "AI/ML Engineer", "Software Engineer",
        "Software Developer", "Python Developer", "Java Developer",
        "Full Stack Developer", "Backend Developer", "Frontend Developer",
        "Web Developer", "Business Analyst", "Data Engineer",
        "Cloud Engineer", "DevOps Engineer", "MLOps Engineer",
        "AI Intern", "ML Intern", "Data Analyst Intern",
        "Data Science Intern", "Software Developer Intern",
        "Software Engineer Intern"
    ]
    return [role for role in roles if contains_ats_term(job_text, role)]


def analyze_ats_keywords(resume_text, job_text):
    grouped_keywords = extract_ats_keywords(job_text)
    all_keywords = []
    for terms in grouped_keywords.values():
        for term in terms:
            if term not in all_keywords:
                all_keywords.append(term)
    matching = []
    missing = []
    for keyword in all_keywords:
        if contains_ats_term(resume_text, keyword):
            matching.append(keyword)
        else:
            missing.append(keyword)
    if all_keywords:
        keyword_score = round(len(matching) / len(all_keywords) * 30)
    else:
        keyword_score = 0
    return {
        "groups": grouped_keywords,
        "all": all_keywords,
        "matching": matching,
        "missing": missing,
        "score": min(keyword_score, 30)
    }


def analyze_skill_categories(resume_text, job_text):
    ats_data = analyze_ats_keywords(resume_text, job_text)
    groups = ats_data["groups"]
    total = 0
    matched = 0
    for terms in groups.values():
        for term in terms:
            total += 1
            if contains_ats_term(resume_text, term):
                matched += 1
    score = round(matched / total * 20) if total else 0
    return {
        "score": min(score, 20),
        "matched": matched,
        "required": total
    }


def analyze_experience(resume_text, experience):
    lower = resume_text.lower()
    experience_section = bool(experience)
    role_words = [
        "intern", "internship", "experience", "developer",
        "engineer", "analyst", "trainee", "work experience",
        "professional experience"
    ]
    role_evidence = sum(1 for word in role_words if word in lower)
    date_pattern = r"\b(?:19|20)\d{2}\b"
    date_count = len(re.findall(date_pattern, resume_text))
    if not experience_section:
        return {
            "score": 0,
            "feedback": "No clear experience section was detected.",
            "date_count": date_count
        }
    score = 6
    if role_evidence >= 2:
        score += 3
    if date_count >= 2:
        score += 2
    if re.search(r"\b\d+(?:\.\d+)?\s*%", resume_text):
        score += 2
    if re.search(r"\b(?:20|[1-9])\+?\b", resume_text):
        score += 1
    return {
        "score": min(score, 15),
        "feedback": "Experience evidence was detected.",
        "date_count": date_count
    }


def analyze_projects(resume_text, projects):
    if not projects:
        return {"score": 0, "feedback": "No project section was detected."}
    score = min(len(projects) * 3, 6)
    project_text = " ".join(projects)
    technical_words = [
        "python", "sql", "machine learning", "deep learning", "api",
        "dashboard", "tensorflow", "pytorch", "power bi", "data",
        "model", "github", "deployed"
    ]
    technical_hits = sum(1 for word in technical_words if word in project_text.lower())
    score += min(technical_hits, 2)
    if re.search(r"\b\d+(?:\.\d+)?\s*%", project_text):
        score += 2
    return {
        "score": min(score, 10),
        "feedback": "Projects detected. Add technologies and measurable results."
    }


def analyze_achievements(resume_text):
    percentage_matches = re.findall(r"\b\d+(?:\.\d+)?\s*%", resume_text)
    metric_patterns = [
        r"\b\d+\+?\s*(?:users|customers|records|projects|models|days|months|years)\b",
        r"\b\d+(?:\.\d+)?\s*(?:x|times)\b",
        r"\b(?:increased|improved|reduced|decreased|saved|achieved|boosted)\b"
    ]
    metric_hits = 0
    for pattern in metric_patterns:
        metric_hits += len(re.findall(pattern, resume_text, flags=re.IGNORECASE))
    score = min(len(percentage_matches) * 2 + min(metric_hits, 6), 10)
    return {
        "score": score,
        "percentages": len(percentage_matches),
        "metrics": metric_hits
    }


def analyze_action_verbs(resume_text):
    action_verbs = [
        "developed", "designed", "implemented", "built", "created", "analyzed",
        "optimized", "automated", "improved", "deployed", "managed", "led",
        "tested", "predicted", "processed", "integrated", "engineered",
        "configured", "trained", "evaluated", "delivered"
    ]
    lower = resume_text.lower()
    found = [verb for verb in action_verbs if re.search(r"\b" + re.escape(verb) + r"\b", lower)]
    score = min(round(len(found) / 5), 5)
    weak_phrases = ["worked on", "responsible for", "helped with", "was involved in", "did"]
    weak_found = [phrase for phrase in weak_phrases if phrase in lower]
    return {
        "score": score,
        "found": found,
        "weak": weak_found
    }


def analyze_structure(resume_text, education, projects, experience, certifications):
    lower = resume_text.lower()
    section_checks = {
        "Contact": ("@" in resume_text or bool(re.search(r"\b[6-9]\d{9}\b", resume_text))),
        "Skills": "skill" in lower,
        "Education": bool(education) or "education" in lower,
        "Projects": bool(projects) or "project" in lower,
        "Experience": bool(experience) or "experience" in lower,
        "Certifications": bool(certifications) or "certification" in lower
    }
    found = [name for name, present in section_checks.items() if present]
    score = round(len(found) / len(section_checks) * 5)
    return {
        "score": min(score, 5),
        "found": found,
        "missing": [name for name, present in section_checks.items() if not present]
    }


def analyze_resume_length(resume_text):
    words = len(re.findall(r"\b[\w+#.-]+\b", resume_text))
    if words < 250:
        message = "Resume is very short. Add relevant projects, skills and achievements."
        status = "Needs Improvement"
    elif words <= 900:
        message = "Resume length is generally reasonable."
        status = "Good"
    else:
        message = "Resume may be too long. Remove repetitive or low-value content."
        status = "Review"
    return {"words": words, "message": message, "status": status}


def analyze_keyword_stuffing(resume_text):
    technical_terms = [
        "python", "java", "sql", "machine learning", "deep learning",
        "power bi", "excel", "pandas", "numpy", "tensorflow", "pytorch",
        "aws", "azure", "docker", "git"
    ]
    lower = resume_text.lower()
    counts = {}
    for term in technical_terms:
        counts[term] = len(re.findall(r"(?<!\w)" + re.escape(term) + r"(?!\w)", lower))
    return {term: count for term, count in counts.items() if count >= 6}


def analyze_job_title(resume_text, job_text):
    roles = extract_job_role_keywords(job_text)
    if not roles:
        return {
            "score": 5, "roles": [],
            "message": "No clear job title detected; keyword analysis used instead."
        }
    matched_roles = [role for role in roles if contains_ats_term(resume_text, role)]
    if matched_roles:
        score = 5
    elif any(term in normalize_ats_text(resume_text) for term in [
        "data", "analyst", "machine learning", "software", "developer", "engineer", "artificial intelligence"
    ]):
        score = 3
    else:
        score = 1
    return {
        "score": score,
        "roles": roles,
        "matched": matched_roles,
        "message": "Job title terminology is aligned." if matched_roles else "Consider using target role title naturally."
    }


def generate_advanced_ats_recommendations(
    keyword_data, experience_data, project_data, achievement_data,
    action_data, structure_data, length_data, repeated_keywords, title_data
):
    recommendations = []
    if keyword_data["missing"]:
        recommendations.append("Add missing job keywords only when you genuinely have related knowledge.")
    if keyword_data["score"] < 24:
        recommendations.append("Tailor your Skills, Projects and Summary to target job description.")
    if experience_data["score"] < 10:
        recommendations.append("Strengthen experience bullets with role, technology and measurable outcomes.")
    if project_data["score"] < 7:
        recommendations.append("Add project technologies, contribution and measurable results.")
    if achievement_data["score"] < 6:
        recommendations.append("Add measurable achievements (metrics, percentages, numbers).")
    if action_data["score"] < 3:
        recommendations.append("Start bullets with strong action verbs (Developed, Implemented, Analyzed).")
    if action_data["weak"]:
        recommendations.append("Replace weak phrases (" + ", ".join(action_data["weak"]) + ") with specific action verbs.")
    if structure_data["missing"]:
        recommendations.append("Add these sections if relevant: " + ", ".join(structure_data["missing"]) + ".")
    if length_data["words"] > 900:
        recommendations.append("Reduce repetitive content and keep job-relevant info.")
    if length_data["words"] < 250:
        recommendations.append("Add stronger project, skills and achievement details.")
    if repeated_keywords:
        repeated_text = ", ".join(f"{k} ({v}x)" for k, v in repeated_keywords.items())
        recommendations.append("Avoid excessive keyword repetition: " + repeated_text + ".")
    if title_data["score"] < 4:
        recommendations.append("Use target job title naturally in professional summary.")
    if not recommendations:
        recommendations.append("Your resume has good ATS coverage. Continue tailoring to each specific job.")
    return recommendations


def calculate_advanced_ats_score(
    keyword_score, skill_score, experience_score, project_score,
    achievement_score, education_score, action_score, structure_score, title_score
):
    total = (
        keyword_score + skill_score + experience_score + project_score
        + achievement_score + education_score + action_score + structure_score
    )
    return min(max(round(total), 0), 100)


# =========================================================
# STEP 12 - SEMANTIC AI JOB MATCHING
# =========================================================

@st.cache_resource(show_spinner=False)
def load_semantic_model():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


def calculate_semantic_similarity(resume_text, job_description):
    model = load_semantic_model()
    if model is not None:
        try:
            resume_embedding = model.encode(resume_text, normalize_embeddings=True)
            job_embedding = model.encode(job_description, normalize_embeddings=True)
            similarity = float(resume_embedding @ job_embedding)
            similarity = max(0.0, min(similarity, 1.0))
            return round(similarity * 100, 2)
        except Exception:
            pass

    # Pure Python Cosine Similarity fallback (resilient across all Windows environments)
    import math
    from collections import Counter
    words_resume = re.findall(r'\w+', resume_text.lower())
    words_job = re.findall(r'\w+', job_description.lower())
    if not words_resume or not words_job:
        return 0.0
    vec1 = Counter(words_resume)
    vec2 = Counter(words_job)
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    sum1 = sum([val ** 2 for val in vec1.values()])
    sum2 = sum([val ** 2 for val in vec2.values()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator:
        return 0.0
    similarity = float(numerator) / denominator
    return round(max(0.0, min(similarity, 1.0)) * 100, 2)


def calculate_semantic_keyword_score(resume_text, job_description):
    job_data = analyze_ats_keywords(resume_text, job_description)
    total = len(job_data["all"])
    matched = len(job_data["matching"])
    if total == 0:
        return 0
    return round(matched / total * 100, 2)


def calculate_title_relevance_score(resume_text, job_description):
    title_data = analyze_job_title(resume_text, job_description)
    return round(title_data["score"] / 5 * 100, 2)


def calculate_combined_semantic_score(semantic_score, keyword_score, title_score):
    final_score = semantic_score * 0.70 + keyword_score * 0.20 + title_score * 0.10
    return round(max(0, min(final_score, 100)), 2)


def get_semantic_match_label(score):
    if score >= 85:
        return ("🟢 Excellent Semantic Match", "The resume is highly relevant to this job.")
    if score >= 70:
        return ("🟢 Strong Semantic Match", "The resume is strongly related to the job.")
    if score >= 55:
        return ("🟡 Moderate Semantic Match", "The resume has useful overlap but can be tailored.")
    if score >= 40:
        return ("🟠 Weak Semantic Match", "Several important requirements may be missing.")
    return ("🔴 Low Semantic Match", "The resume is not strongly aligned with this job.")


def build_semantic_match_explanation(semantic_score, keyword_score, title_score, keyword_data):
    explanation = []
    if semantic_score >= 75:
        explanation.append("The resume and job description have strong semantic similarity.")
    elif semantic_score >= 55:
        explanation.append("The resume and job description have moderate semantic similarity.")
    else:
        explanation.append("The resume and job description have limited semantic similarity.")

    if keyword_score >= 70:
        explanation.append("Most detected job keywords are present in the resume.")
    elif keyword_score >= 40:
        explanation.append("Some important job keywords are present, but several are missing.")
    else:
        explanation.append("Many detected job keywords are missing from the resume.")

    if title_score >= 80:
        explanation.append("The target job title is well aligned with the resume.")
    elif title_score >= 50:
        explanation.append("The resume contains related role terminology.")
    else:
        explanation.append("The resume does not strongly reflect the target role.")

    if keyword_data["missing"]:
        explanation.append("Important missing keywords: " + ", ".join(keyword_data["missing"][:8]) + ".")
    return explanation


# =========================================================
# STEP 13 - AI COVER LETTER GENERATOR
# =========================================================

def clean_cover_letter_value(value):
    value = str(value or "").strip()
    return re.sub(r"\s+", " ", value)


def extract_candidate_name_from_resume(resume_text):
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    for line in lines[:8]:
        clean = re.sub(r"[^A-Za-z .'-]", "", line).strip()
        words = clean.split()
        if (2 <= len(words) <= 4 and not any(char.isdigit() for char in line)
                and "@" not in line and len(clean) <= 60):
            blocked = {"resume", "curriculum vitae", "cv", "profile", "objective", "summary", "skills", "education"}
            if clean.lower() not in blocked:
                return clean
    return ""


def extract_cover_letter_job_title(job_text):
    roles = extract_job_role_keywords(job_text)
    if roles:
        return roles[0]
    lines = [line.strip() for line in job_text.splitlines() if line.strip()]
    for line in lines[:10]:
        if 3 <= len(line) <= 100:
            lower = line.lower()
            if any(w in lower for w in [
                "analyst", "developer", "engineer", "intern", "scientist", "manager", "designer", "consultant", "specialist"
            ]):
                return line
    return "the position"


def extract_cover_letter_company(job_text):
    patterns = [r"company\s*[:\-]\s*([^\n]+)", r"organization\s*[:\-]\s*([^\n]+)", r"employer\s*[:\-]\s*([^\n]+)"]
    for pattern in patterns:
        match = re.search(pattern, job_text, flags=re.IGNORECASE)
        if match:
            return clean_cover_letter_value(match.group(1))
    return ""


def select_cover_letter_skills(resume_text, job_text, maximum=6):
    job_data = analyze_ats_keywords(resume_text, job_text)
    return job_data["matching"][:maximum]


def select_cover_letter_projects(resume_text, projects, job_text, maximum=2):
    if not projects:
        return []
    job_lower = job_text.lower()
    relevant = []
    for project in projects:
        project_lower = project.lower()
        score = sum(1 for term in [
            "python", "sql", "machine learning", "deep learning", "data", "analytics",
            "power bi", "tableau", "tensorflow", "pytorch", "nlp", "computer vision",
            "api", "cloud", "docker", "aws", "azure", "google cloud"
        ] if term in job_lower and term in project_lower)
        relevant.append((score, project))
    relevant.sort(key=lambda item: item[0], reverse=True)
    return [project for score, project in relevant[:maximum]]


def generate_cover_letter(
    candidate_name, job_title, company_name, hiring_manager,
    resume_text, job_description, tone, length
):
    candidate_name = clean_cover_letter_value(candidate_name)
    job_title = clean_cover_letter_value(job_title) or "the position"
    company_name = clean_cover_letter_value(company_name)
    hiring_manager = clean_cover_letter_value(hiring_manager)

    matching_skills = select_cover_letter_skills(resume_text, job_description, maximum=6)
    job_data = analyze_ats_keywords(resume_text, job_description)
    projects = extract_section(resume_text, ["Projects", "Project"])
    selected_projects = select_cover_letter_projects(resume_text, projects, job_description, maximum=2)
    education = extract_education_details(resume_text)
    experience = extract_section(resume_text, ["Experience", "Work Experience", "Internship", "Internships"])

    greeting = f"Dear {hiring_manager}," if hiring_manager else "Dear Hiring Manager,"

    if company_name:
        opening = (f"I am writing to express my interest in the {job_title} position at {company_name}. "
                   "My academic background and practical experience have prepared me to contribute effectively.")
    else:
        opening = (f"I am writing to express my interest in the {job_title} position. "
                   "My academic background and practical experience have prepared me to contribute effectively.")

    if matching_skills:
        skill_text = ", ".join(matching_skills)
        skills_paragraph = (f"Through my academic and project experience, I have developed practical knowledge of {skill_text}. "
                            "These skills align well with the requirements described for this position.")
    else:
        skills_paragraph = ("My academic and project experience has helped me build a strong technical foundation, "
                            "analytical thinking and problem-solving ability.")

    if selected_projects:
        project_names = [clean_cover_letter_value(p)[:177] + ("..." if len(clean_cover_letter_value(p)) > 180 else "")
                         for p in selected_projects]
        projects_paragraph = ("My project experience includes " + "; ".join(project_names) +
                              ". These projects strengthened my ability to translate technical concepts into practical solutions.")
    else:
        projects_paragraph = "My academic work has provided opportunities to apply technical concepts through hands-on projects."

    if experience:
        experience_paragraph = "I have developed practical experience through the work described in my resume."
    elif education:
        experience_paragraph = "As a dedicated student, I have built my technical foundation through coursework and projects."
    else:
        experience_paragraph = "I am an eager learner motivated to contribute to real-world engineering and analytics problems."

    if tone == "Professional":
        closing_paragraph = "I would welcome the opportunity to discuss how my background could contribute to your team."
    elif tone == "Confident":
        closing_paragraph = "I am confident that my technical foundation and project experience will allow me to contribute positively."
    else:
        closing_paragraph = "I would be grateful for the opportunity to discuss my background and learn more about the role."

    if length == "Short":
        paragraphs = [opening, skills_paragraph, closing_paragraph]
    elif length == "Long":
        missing = job_data["missing"][:4]
        kw_line = f"I am also actively strengthening my knowledge in {', '.join(missing)}." if missing else ""
        paragraphs = [opening, skills_paragraph, projects_paragraph, experience_paragraph, kw_line, closing_paragraph]
        paragraphs = [p for p in paragraphs if p.strip()]
    else:
        paragraphs = [opening, skills_paragraph, projects_paragraph, experience_paragraph, closing_paragraph]

    signature_name = candidate_name if candidate_name else "Your Name"
    letter = greeting + "\n\n" + "\n\n".join(paragraphs) + "\n\nSincerely,\n" + signature_name
    return letter, matching_skills, selected_projects


def create_cover_letter_pdf(cover_letter_text, candidate_name, job_title, company_name):
    try:
        from io import BytesIO
        from xml.sax.saxutils import escape
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

        buffer = BytesIO()
        document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=55, leftMargin=55, topMargin=55, bottomMargin=55)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("CoverLetterTitle", parent=styles["Title"], alignment=TA_LEFT, fontSize=16, spaceAfter=12)
        body_style = ParagraphStyle("CoverLetterBody", parent=styles["BodyText"], fontSize=10, leading=15, spaceAfter=10)

        story = []
        title = "COVER LETTER"
        if job_title:
            title += f" - {job_title}"
        if company_name:
            title += f" | {company_name}"
        story.append(Paragraph(escape(title), title_style))
        story.append(Spacer(1, 8))

        for paragraph in cover_letter_text.split("\n\n"):
            p = paragraph.strip()
            if not p:
                continue
            safe = escape(p).replace("\n", "<br/>")
            story.append(Paragraph(safe, body_style))

        document.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception:
        return None


# =========================================================
# STEP 14 - AI APPLICATION EMAIL GENERATOR
# =========================================================

def generate_application_email(
    candidate_name, job_title, company_name, hiring_manager,
    resume_text, job_description, tone, email_length, include_subject=True
):
    candidate_name = clean_cover_letter_value(candidate_name)
    job_title = clean_cover_letter_value(job_title) or "the position"
    company_name = clean_cover_letter_value(company_name)
    hiring_manager = clean_cover_letter_value(hiring_manager)

    matching_skills = select_cover_letter_skills(resume_text, job_description, maximum=5)
    projects = extract_section(resume_text, ["Projects", "Project"])
    selected_projects = select_cover_letter_projects(resume_text, projects, job_description, maximum=1)
    education = extract_education_details(resume_text)
    experience = extract_section(resume_text, ["Experience", "Work Experience", "Internship", "Internships"])
    email_data = analyze_ats_keywords(resume_text, job_description)

    subject = f"Application for {job_title}" + (f" - {company_name}" if company_name else "")
    greeting = f"Dear {hiring_manager}," if hiring_manager else "Dear Hiring Manager,"

    opening = f"I am writing to apply for the {job_title} position" + (f" at {company_name}." if company_name else ".")
    education_line = ("My academic background has given me a strong foundation in the technical and analytical skills "
                      "relevant to this opportunity.") if education else "My background provides a strong technical foundation."

    skills_line = ("My relevant skills include " + ", ".join(matching_skills) + ".") if matching_skills else (
        "I have developed relevant technical and problem-solving skills through academic and practical work."
    )

    if selected_projects:
        project_clean = clean_cover_letter_value(selected_projects[0])[:217]
        project_line = f"One relevant project from my resume is {project_clean}."
    else:
        project_line = "My project-based work has helped me apply technical concepts to practical problems."

    experience_line = ("My practical experience has strengthened my ability to solve problems and deliver objectives."
                       if experience else "I am enthusiastic about applying my skills to real-world projects in this role.")

    if tone == "Professional":
        closing = "I would appreciate the opportunity to discuss how my background and skills could contribute to your team."
    elif tone == "Confident":
        closing = "I am confident that my technical foundation and willingness to learn would allow me to contribute positively."
    else:
        closing = "I would be happy to discuss the role and how my background could be a good fit for your team."

    if email_length == "Short":
        body_paragraphs = [opening, skills_line, closing]
    elif email_length == "Detailed":
        body_paragraphs = [opening, education_line, skills_line, project_line, experience_line, closing]
    else:
        body_paragraphs = [opening, education_line, skills_line, project_line, closing]

    body_paragraphs = [p for p in body_paragraphs if p.strip()]
    signature_name = candidate_name if candidate_name else "Your Name"
    email_body = greeting + "\n\n" + "\n\n".join(body_paragraphs) + "\n\nBest regards,\n" + signature_name
    full_email = ("Subject: " + subject + "\n\n" + email_body) if include_subject else email_body

    return full_email, subject, matching_skills, selected_projects, email_data


def create_application_email_pdf(email_text, job_title, company_name):
    try:
        from io import BytesIO
        from xml.sax.saxutils import escape
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

        buffer = BytesIO()
        document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=55, leftMargin=55, topMargin=55, bottomMargin=55)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("EmailTitle", parent=styles["Title"], fontSize=16, spaceAfter=12)
        body_style = ParagraphStyle("EmailBody", parent=styles["BodyText"], fontSize=10, leading=15, spaceAfter=10)

        story = []
        title = "JOB APPLICATION EMAIL"
        if job_title:
            title += f" - {job_title}"
        if company_name:
            title += f" | {company_name}"
        story.append(Paragraph(escape(title), title_style))
        story.append(Spacer(1, 8))

        for paragraph in email_text.split("\n\n"):
            p = paragraph.strip()
            if not p:
                continue
            safe = escape(p).replace("\n", "<br/>")
            story.append(Paragraph(safe, body_style))

        document.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception:
        return None


# =========================================================
# AI RESUME TAILORING
# =========================================================

def build_tailored_summary(resume_text, job_description):
    ats_data = analyze_ats_keywords(resume_text, job_description)
    matching_skills = ats_data["matching"][:6]
    education_data = extract_education_details(resume_text)
    experience_data = extract_section(resume_text, ["Experience", "Work Experience", "Internship", "Internships"])

    if matching_skills:
        skill_text = ", ".join(matching_skills)
        summary = (f"Motivated and detail-oriented professional with a strong foundation in {skill_text}. "
                   "Experienced in applying technical and analytical knowledge through academic and practical projects. "
                   "Strong problem-solving ability with a passion for delivering measurable impact.")
    else:
        summary = ("Motivated and detail-oriented professional with a strong technical foundation and willingness to learn. "
                   "Experienced in applying academic knowledge through practical projects and problem-solving activities.")

    if education_data:
        summary += f" Academic background includes {', '.join(education_data[:2])}."
    if experience_data:
        summary += " Practical experience is also reflected in the candidate's resume."
    return summary


def get_tailoring_skill_recommendations(resume_text, job_description):
    ats_data = analyze_ats_keywords(resume_text, job_description)
    return ats_data["matching"], ats_data["missing"]


def get_tailoring_project_recommendations(resume_text, job_description):
    projects = extract_section(resume_text, ["Projects", "Project"])
    if not projects:
        return ["Add a relevant project only if you have actually completed one."]
    job_lower = job_description.lower()
    recommendations = []
    keywords = [
        "python", "sql", "machine learning", "deep learning", "data analysis", "data analytics",
        "power bi", "tableau", "pandas", "numpy", "tensorflow", "pytorch", "nlp",
        "computer vision", "api", "docker", "aws", "azure", "google cloud"
    ]
    for project in projects:
        project_lower = project.lower()
        matched_terms = [t for t in keywords if t in job_lower and t in project_lower]
        if matched_terms:
            project_name = project.strip()[:137] + ("..." if len(project.strip()) > 140 else "")
            recommendations.append(f"Highlight {', '.join(matched_terms)} in project: {project_name}")
    if not recommendations:
        recommendations.append("Prioritize the existing project most closely related to job description responsibilities.")
    return recommendations


def generate_tailoring_recommendations(resume_text, job_description, matching_skills, missing_skills):
    recommendations = []
    if missing_skills:
        recommendations.append("Add missing job keywords only when you genuinely have related knowledge.")
    if len(matching_skills) < 4:
        recommendations.append("Strengthen Skills section with relevant skills you actually know.")
    if "summary" not in resume_text.lower():
        recommendations.append("Add a concise professional summary tailored to target role.")
    if "experience" not in resume_text.lower():
        recommendations.append("Include internships or practical experience with measurable outcomes.")
    if "project" not in resume_text.lower():
        recommendations.append("Add relevant projects demonstrating skills required by target role.")
    if not re.search(r"\b\d+(?:\.\d+)?\s*%", resume_text):
        recommendations.append("Add measurable results (percentages, metrics, records) where truthful.")
    recommendations.append("Use job description terminology naturally in Summary, Skills, and Projects.")
    return recommendations


def create_restored_tailored_resume_pdf(resume_text, tailored_summary, matching_skills, projects, certifications):
    try:
        from io import BytesIO
        from xml.sax.saxutils import escape
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

        buffer = BytesIO()
        document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("TailoredTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=18, spaceAfter=14)
        heading_style = ParagraphStyle("TailoredHeading", parent=styles["Heading2"], fontSize=12, spaceBefore=9, spaceAfter=5)
        body_style = ParagraphStyle("TailoredBody", parent=styles["BodyText"], fontSize=9, leading=13, spaceAfter=4)

        story = []
        candidate_name = extract_candidate_name_from_resume(resume_text)
        story.append(Paragraph(escape(candidate_name if candidate_name else "TAILORED RESUME"), title_style))

        email = extract_email(resume_text)
        phone = extract_phone(resume_text)
        story.append(Paragraph("CONTACT INFORMATION", heading_style))
        story.append(Paragraph(f"Email: {escape(str(email))}<br/>Phone: {escape(str(phone))}", body_style))

        story.append(Paragraph("PROFESSIONAL SUMMARY", heading_style))
        story.append(Paragraph(escape(tailored_summary), body_style))

        story.append(Paragraph("RELEVANT TECHNICAL SKILLS", heading_style))
        story.append(Paragraph(escape(", ".join(matching_skills) if matching_skills else "See original resume"), body_style))

        education = extract_education_details(resume_text)
        story.append(Paragraph("EDUCATION", heading_style))
        for item in (education if education else ["See original resume"]):
            story.append(Paragraph("• " + escape(str(item)), body_style))

        story.append(Paragraph("PROJECTS", heading_style))
        for project in (projects if projects else ["See original resume"]):
            story.append(Paragraph("• " + escape(str(project)), body_style))

        if certifications:
            story.append(Paragraph("CERTIFICATIONS", heading_style))
            for cert in certifications:
                story.append(Paragraph("• " + escape(str(cert)), body_style))

        document.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception:
        return None


# =========================================================
# STEP 16 - SEMI-AUTOMATIC JOB APPLICATION ASSISTANT
# =========================================================

def step16_get_job(index):
    apps = load_applications()
    if not apps or index < 0 or index >= len(apps):
        return None
    item = apps[index]
    defaults = {
        "title": "", "company": "", "location": "", "score": 0,
        "application_url": "", "status": "Saved", "priority": "Medium",
        "applied_date": "", "follow_up_date": "", "notes": "",
        "contact_name": "", "contact_email": "", "salary": "",
        "source": "", "job_description": ""
    }
    for key, value in defaults.items():
        item.setdefault(key, value)
    return item


def step16_checklist(application, job_description, resume_text):
    return [
        ("Resume uploaded", bool(resume_text.strip())),
        ("Job description available", bool(job_description.strip())),
        ("Job title confirmed", bool(application.get("title"))),
        ("Company confirmed", bool(application.get("company"))),
        ("Application URL available", bool(application.get("application_url"))),
    ]


def step16_prepare_package(
    resume_text, job_description, application,
    candidate_name, hiring_manager, tone
):
    ats = analyze_ats_keywords(resume_text, job_description)
    keyword_score = (
        round(len(ats["matching"]) / len(ats["all"]) * 100)
        if ats["all"] else 0
    )
    title_score = calculate_title_relevance_score(resume_text, job_description)

    semantic_score = None
    try:
        semantic_score = calculate_semantic_similarity(resume_text, job_description)
    except Exception:
        pass

    if semantic_score is not None:
        final_score = calculate_combined_semantic_score(semantic_score, keyword_score, title_score)
    else:
        final_score = round(keyword_score * 0.75 + title_score * 0.25)

    summary = build_tailored_summary(resume_text, job_description)
    matching, missing = get_tailoring_skill_recommendations(resume_text, job_description)
    projects = extract_section(resume_text, ["Projects", "Project"])

    cover_letter, _, _ = generate_cover_letter(
        candidate_name=candidate_name,
        job_title=application.get("title", ""),
        company_name=application.get("company", ""),
        hiring_manager=hiring_manager,
        resume_text=resume_text,
        job_description=job_description,
        tone=tone,
        length="Medium"
    )

    email, subject, _, _, _ = generate_application_email(
        candidate_name=candidate_name,
        job_title=application.get("title", ""),
        company_name=application.get("company", ""),
        hiring_manager=hiring_manager,
        resume_text=resume_text,
        job_description=job_description,
        tone=tone,
        email_length="Medium",
        include_subject=True
    )

    return {
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "title_score": title_score,
        "final_score": final_score,
        "matching": matching,
        "missing": missing,
        "summary": summary,
        "projects": projects[:2],
        "cover_letter": cover_letter,
        "email": email,
        "subject": subject,
    }


# =========================================================
# STEP 17 - APPLICATION ANALYTICS
# =========================================================

def step17_safe_score(value):
    try:
        return max(0, min(100, float(value)))
    except (TypeError, ValueError):
        return 0.0


def step17_rate(numerator, denominator):
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def step17_month(value):
    if not value:
        return ""
    value = str(value)
    return value[:7] if len(value) >= 7 else ""


def step17_analytics(applications):
    total = len(applications)
    status_counts = {
        "Saved": 0, "Applied": 0, "Assessment": 0, "Interview": 0,
        "Offer": 0, "Selected": 0, "Rejected": 0, "Withdrawn": 0
    }
    priority_counts = {"Low": 0, "Medium": 0, "High": 0}
    source_counts = {}
    company_counts = {}
    monthly_counts = {}
    scores = []

    for item in applications:
        status = item.get("status", "Saved")
        if status not in status_counts:
            status = "Saved"
        status_counts[status] += 1

        priority = item.get("priority", "Medium")
        if priority not in priority_counts:
            priority = "Medium"
        priority_counts[priority] += 1

        source = str(item.get("source", "")).strip() or "Unknown"
        source_counts[source] = source_counts.get(source, 0) + 1

        company = str(item.get("company", "")).strip() or "Unknown"
        company_counts[company] = company_counts.get(company, 0) + 1

        score = step17_safe_score(item.get("score", 0))
        if score > 0:
            scores.append(score)

        month = step17_month(item.get("applied_date", ""))
        if month:
            monthly_counts[month] = monthly_counts.get(month, 0) + 1

    applied = status_counts["Applied"]
    assessment = status_counts["Assessment"]
    interview = status_counts["Interview"]
    offers = status_counts["Offer"]
    selected = status_counts["Selected"]
    rejected = status_counts["Rejected"]

    submitted = applied + assessment + interview + offers + selected + rejected
    response_count = assessment + interview + offers + selected + rejected
    positive_outcomes = interview + offers + selected
    average_score = round(sum(scores) / len(scores), 1) if scores else 0

    return {
        "total": total,
        "status_counts": status_counts,
        "priority_counts": priority_counts,
        "source_counts": source_counts,
        "company_counts": company_counts,
        "monthly_counts": monthly_counts,
        "average_score": average_score,
        "submitted": submitted,
        "response_count": response_count,
        "positive_outcomes": positive_outcomes,
        "response_rate": step17_rate(response_count, submitted),
        "interview_rate": step17_rate(interview, submitted),
        "offer_rate": step17_rate(offers + selected, submitted),
    }
