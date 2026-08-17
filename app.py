import streamlit as st
import re
from datetime import datetime, date

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


st.set_page_config(
    page_title="AI Job Application Assistant",
    page_icon="🤖",
    layout="wide"
)

# =========================================================
# STEP 18 - USER LOGIN / PROFILE
# =========================================================
#
# Local authentication and profile management for the
# Streamlit application.
#
# Features:
#   - Register account
#   - Login / logout
#   - Password hashing with PBKDF2-HMAC-SHA256
#   - User profile
#   - Skills / preferred roles / location
#   - Resume preferences
#   - Profile persistence in users.json
#
# Note:
# This local version is intended for a college/demo project.
# For production deployment, use a proper authentication
# provider and a database.
# =========================================================

import os
import json
import base64
import hashlib
import hmac
import secrets

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
        json.dump(
            users,
            file,
            indent=4,
            ensure_ascii=False
        )


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
        salt = base64.b64decode(
            salt_b64.encode("utf-8")
        )

        expected = base64.b64decode(
            hash_b64.encode("utf-8")
        )

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            200_000
        )

        return hmac.compare_digest(
            actual,
            expected
        )

    except Exception:
        return False


def auth_create_user(
    username,
    password,
    full_name="",
    email="",
    phone="",
    location="",
    target_roles="",
    skills="",
    experience="",
    education="",
    linkedin="",
    github="",
    portfolio=""
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

    salt, password_hash = auth_hash_password(
        password
    )

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

    return users[username].get(
        "profile",
        {}
    )


def auth_update_profile(
    username,
    full_name,
    email,
    phone,
    location,
    target_roles,
    skills,
    experience,
    education,
    linkedin,
    github,
    portfolio
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
# SESSION STATE
# =========================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "auth_username" not in st.session_state:
    st.session_state.auth_username = ""


# =========================================================
# LOGIN / REGISTER SCREEN
# =========================================================

if not st.session_state.authenticated:

    st.title("🔐 AI Job Application Assistant")

    st.write(
        "Create an account or login to manage your resume, "
        "profile and job-application workflow."
    )

    login_tab, register_tab = st.tabs(
        [
            "🔑 Login",
            "📝 Create Account"
        ]
    )

    with login_tab:

        login_username = st.text_input(
            "Username",
            key="auth_login_username"
        )

        login_password = st.text_input(
            "Password",
            type="password",
            key="auth_login_password"
        )

        if st.button(
            "🔑 Login",
            type="primary",
            key="auth_login_button"
        ):

            if auth_login(
                login_username,
                login_password
            ):

                st.session_state.authenticated = True
                st.session_state.auth_username = (
                    login_username.strip().lower()
                )

                st.success(
                    "✅ Login successful."
                )

                st.rerun()

            else:

                st.error(
                    "❌ Invalid username or password."
                )

    with register_tab:

        reg_username = st.text_input(
            "Choose Username",
            key="auth_reg_username"
        )

        reg_password = st.text_input(
            "Create Password",
            type="password",
            key="auth_reg_password"
        )

        reg_confirm = st.text_input(
            "Confirm Password",
            type="password",
            key="auth_reg_confirm"
        )

        st.subheader(
            "👤 Basic Profile"
        )

        reg_name = st.text_input(
            "Full Name",
            key="auth_reg_name"
        )

        reg_email = st.text_input(
            "Email",
            key="auth_reg_email"
        )

        reg_location = st.text_input(
            "Location",
            key="auth_reg_location"
        )

        reg_roles = st.text_input(
            "Preferred Job Roles",
            placeholder="Data Analyst, ML Engineer, AI Intern",
            key="auth_reg_roles"
        )

        reg_skills = st.text_input(
            "Skills",
            placeholder="Python, SQL, Machine Learning",
            key="auth_reg_skills"
        )

        if st.button(
            "📝 Create Account",
            type="primary",
            key="auth_register_button"
        ):

            if reg_password != reg_confirm:

                st.error(
                    "Passwords do not match."
                )

            else:

                created, message = auth_create_user(
                    username=reg_username,
                    password=reg_password,
                    full_name=reg_name,
                    email=reg_email,
                    location=reg_location,
                    target_roles=reg_roles,
                    skills=reg_skills
                )

                if created:

                    st.success(
                        message
                        + " You can now login."
                    )

                else:

                    st.error(
                        message
                    )

    st.stop()


# =========================================================
# LOGGED-IN HEADER
# =========================================================

logged_in_username = (
    st.session_state.auth_username
)

logged_in_profile = auth_get_profile(
    logged_in_username
)

with st.sidebar:

    st.success(
        "🟢 Logged in"
    )

    st.write(
        f"**User:** {logged_in_username}"
    )

    if logged_in_profile.get(
        "full_name"
    ):

        st.write(
            f"👤 {logged_in_profile['full_name']}"
        )

    if st.button(
        "🚪 Logout",
        key="auth_logout_button"
    ):

        st.session_state.authenticated = False
        st.session_state.auth_username = ""

        # Clear temporary AI-generated application data.
        for key in [
            "step16_package",
            "step16_job_description",
            "step16_summary",
            "step16_cover",
            "step16_email"
        ]:

            if key in st.session_state:
                del st.session_state[key]

        st.rerun()


# =========================================================
# STEP 18 - USER PROFILE
# =========================================================

st.divider()

st.header(
    "👤 User Profile"
)

st.write(
    "Manage the information used across your job-search "
    "workflow."
)

profile = auth_get_profile(
    logged_in_username
)

profile_col1, profile_col2 = st.columns(2)

with profile_col1:

    profile_name = st.text_input(
        "Full Name",
        value=profile.get(
            "full_name",
            ""
        ),
        key="profile_full_name"
    )

    profile_email = st.text_input(
        "Email",
        value=profile.get(
            "email",
            ""
        ),
        key="profile_email"
    )

    profile_phone = st.text_input(
        "Phone",
        value=profile.get(
            "phone",
            ""
        ),
        key="profile_phone"
    )

    profile_location = st.text_input(
        "Location",
        value=profile.get(
            "location",
            ""
        ),
        key="profile_location"
    )

    profile_roles = st.text_input(
        "Preferred Job Roles",
        value=profile.get(
            "target_roles",
            ""
        ),
        placeholder="Data Analyst, AI/ML Engineer, AI Intern",
        key="profile_target_roles"
    )

with profile_col2:

    profile_skills = st.text_area(
        "Skills",
        value=profile.get(
            "skills",
            ""
        ),
        placeholder="Python, SQL, Pandas, Machine Learning...",
        key="profile_skills"
    )

    profile_experience = st.text_area(
        "Experience",
        value=profile.get(
            "experience",
            ""
        ),
        placeholder="Internships, work experience, freelance work...",
        key="profile_experience"
    )

    profile_education = st.text_area(
        "Education",
        value=profile.get(
            "education",
            ""
        ),
        placeholder="B.Tech in AI & Data Science...",
        key="profile_education"
    )

st.subheader(
    "🔗 Professional Links"
)

link_col1, link_col2, link_col3 = st.columns(3)

with link_col1:

    profile_linkedin = st.text_input(
        "LinkedIn",
        value=profile.get(
            "linkedin",
            ""
        ),
        key="profile_linkedin"
    )

with link_col2:

    profile_github = st.text_input(
        "GitHub",
        value=profile.get(
            "github",
            ""
        ),
        key="profile_github"
    )

with link_col3:

    profile_portfolio = st.text_input(
        "Portfolio",
        value=profile.get(
            "portfolio",
            ""
        ),
        key="profile_portfolio"
    )

if st.button(
    "💾 Save Profile",
    type="primary",
    key="save_user_profile"
):

    updated = auth_update_profile(
        username=logged_in_username,
        full_name=profile_name,
        email=profile_email,
        phone=profile_phone,
        location=profile_location,
        target_roles=profile_roles,
        skills=profile_skills,
        experience=profile_experience,
        education=profile_education,
        linkedin=profile_linkedin,
        github=profile_github,
        portfolio=profile_portfolio
    )

    if updated:

        st.success(
            "✅ Profile saved successfully."
        )

        st.rerun()

    else:

        st.error(
            "Unable to save profile."
        )


# =========================================================
# PROFILE SUMMARY
# =========================================================

with st.expander(
    "📋 View Profile Summary"
):

    summary_col1, summary_col2 = st.columns(2)

    with summary_col1:

        st.write(
            f"**👤 Name:** "
            f"{profile_name or 'Not added'}"
        )

        st.write(
            f"**📧 Email:** "
            f"{profile_email or 'Not added'}"
        )

        st.write(
            f"**📱 Phone:** "
            f"{profile_phone or 'Not added'}"
        )

        st.write(
            f"**📍 Location:** "
            f"{profile_location or 'Not added'}"
        )

    with summary_col2:

        st.write(
            f"**💼 Target Roles:** "
            f"{profile_roles or 'Not added'}"
        )

        st.write(
            f"**💻 Skills:** "
            f"{profile_skills or 'Not added'}"
        )

        st.write(
            f"**🎓 Education:** "
            f"{profile_education or 'Not added'}"
        )

# =========================================================
# PROFILE COMPLETENESS
# =========================================================

profile_fields = [
    profile_name,
    profile_email,
    profile_location,
    profile_roles,
    profile_skills,
    profile_education
]

profile_completed = sum(
    bool(str(value).strip())
    for value in profile_fields
)

profile_percentage = round(
    profile_completed
    / len(profile_fields)
    * 100
)

st.subheader(
    "📊 Profile Completeness"
)

st.progress(
    profile_percentage / 100
)

st.write(
    f"**{profile_percentage}% complete**"
)

if profile_percentage < 100:

    st.info(
        "💡 Complete your profile to make the job "
        "recommendation and application workflow more useful."
    )


st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")

st.markdown("""
<style>
.main-title{font-size:40px;font-weight:700;text-align:center}
.subtitle{text-align:center;font-size:18px;margin-bottom:25px}
</style>
""", unsafe_allow_html=True)


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


def show_job(item, index):
    job = item["job"]
    score = item["score"]
    matching = item["matching"]
    missing = item["missing"]
    with st.container(border=True):
        st.subheader(f"{index}. {job.get('title', 'Unknown Job')}")
        st.write(f"🏢 **Company:** {job.get('company', 'Unknown')}")
        st.write(f"📍 **Location:** {job.get('location', 'Unknown')}")
        job_type = job.get("type") or job.get("contract_type") or job.get("contract_time")
        if job_type:
            st.write(f"💼 **Type:** {job_type}")
        if score >= 80:
            st.success(f"🎯 Match Score: {score}%")
        elif score >= 60:
            st.warning(f"🎯 Match Score: {score}%")
        else:
            st.error(f"🎯 Match Score: {score}%")
        st.progress(max(0, min(score, 100)) / 100)
        if matching:
            st.write("✅ **Matching Skills:** " + ", ".join(matching))
        if missing:
            st.write("❌ **Missing Skills:** " + ", ".join(missing))
        lo, hi = job.get("salary_min"), job.get("salary_max")
        if lo is not None or hi is not None:
            st.write(f"💰 **Salary:** {lo or 'N/A'} - {hi or 'N/A'}")
        description = job.get("description", "")
        if description:
            with st.expander("📋 View Job Description"):
                st.write(description)
        url = job.get("application_url") or job.get("redirect_url") or ""
        if url:
            st.link_button("🔗 View / Apply", url)

        # =========================================
        # SAVE RECOMMENDED JOB
        # =========================================

        if st.button(
            "⭐ Save Job",
            key=f"save_recommended_job_{index}"
        ):

            saved = add_application(
                title=job.get(
                    "title",
                    "Unknown Job"
                ),
                company=job.get(
                    "company",
                    "Unknown Company"
                ),
                location=job.get(
                    "location",
                    "Unknown"
                ),
                score=score,
                application_url=url,
                status="Saved"
            )

            if saved:
                st.success(
                    "⭐ Job saved successfully!"
                )
            else:
                st.info(
                    "This job is already saved."
                )


st.markdown('<div class="main-title">📄 AI Resume Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-powered Resume Analysis, Job Matching and Real Job Search</div>', unsafe_allow_html=True)

st.header("📤 Upload Resume")
uploaded_file = st.file_uploader("Choose your Resume PDF", type=["pdf"])

if not uploaded_file:
    st.info("👆 Upload a PDF resume to start the analyzer.")
    st.markdown("""
    ### 🚀 Features
    - 📄 PDF resume parsing
    - 👤 Personal information extraction
    - 💻 Technical skill extraction
    - 🎓 Education, projects and experience extraction
    - 📜 Certification extraction
    - ⭐ Resume scoring
    - ⚠️ Missing skill detection
    - 💡 Resume improvement suggestions
    - 🎯 Job description matching
    - 💼 Local job recommendations
    - 🌐 Real job search
    - 🔗 Application links
    """)
    st.stop()

st.success("✅ Resume uploaded successfully!")

try:
    text = extract_text(uploaded_file)
except Exception as error:
    st.error(f"Unable to read PDF: {error}")
    st.stop()

if not text.strip():
    st.error("Unable to extract text from this PDF. Please upload a text-based PDF.")
    st.stop()

name = extract_name(text)
email = extract_email(text)
phone = extract_phone(text)
skills = extract_skills(text)
education = extract_education_details(text)
projects = extract_projects(text)
experience = extract_experience(text)
certifications = extract_section(text, ["Certifications", "Certificates"])

st.header("👤 Personal Information")
c1, c2 = st.columns(2)
with c1:
    st.write("👤 **Name:**", name)
    st.write("📧 **Email:**", email)
with c2:
    st.write("📱 **Phone:**", phone)

st.header("💻 Technical Skills")
if skills:
    cols = st.columns(3)
    for i, skill in enumerate(skills):
        with cols[i % 3]:
            st.success("✓ " + skill)
else:
    st.warning("No technical skills detected.")

st.header("🎓 Education")
if education:
    for item in education:
        st.write("•", item)
else:
    st.info("No education section detected.")

st.header("📁 Projects")
if projects:
    for item in projects:
        st.write("•", item)
else:
    st.info("No project section detected.")

st.header("💼 Experience")
if experience:
    for item in experience:
        st.write("•", item)
else:
    st.info("No experience section detected.")

st.header("📜 Certifications")
if certifications:
    for item in certifications:
        st.write("•", item)
else:
    st.info("No certification section detected.")

st.header("⭐ Resume Score")
score = resume_score(text, skills, education, projects, experience, certifications)
sc1, sc2 = st.columns(2)
with sc1:
    st.metric("Overall Resume Score", f"{score}/100")
with sc2:
    if score >= 80:
        st.success("Excellent Resume")
    elif score >= 60:
        st.warning("Good Resume - Needs Improvement")
    else:
        st.error("Resume Needs Improvement")
st.progress(score / 100)

st.header("⚠️ Recommended Skills")
missing = missing_skills(skills)
if missing:
    cols = st.columns(2)
    for i, skill in enumerate(missing[:10]):
        with cols[i % 2]:
            st.warning("• " + skill)
else:
    st.success("🎉 No major recommended skills are missing.")

st.header("💡 Resume Improvement Suggestions")
for item in suggestions(score, skills, projects, experience, certifications):
    st.info("💡 " + item)

with st.expander("🔍 View Extracted Resume Text"):
    st.text_area("Resume Content", text, height=400)

# =========================================================
# JOB DESCRIPTION ANALYZER
# =========================================================

st.header("🎯 Job Description Analyzer")
st.write("Paste a job description below to compare it with your resume.")
job_description = st.text_area(
    "Paste Job Description",
    height=300,
    placeholder="""Data Analyst Intern

Requirements:
Python
SQL
Power BI
Excel
Machine Learning
Statistics
Pandas
NumPy"""
)

if st.button("🔍 Analyze Job Match", type="primary", key="analyze_job"):
    if not job_description.strip():
        st.warning("Please paste a job description first.")
    else:
        job_skills = extract_job_skills(job_description)
        matching_skills, missing_job_skills = compare_skills(skills, job_skills)
        match_score = calculate_match_score(matching_skills, job_skills)
        recommendation = generate_recommendation(match_score)

        st.header("🎯 Job Match Result")
        r1, r2 = st.columns(2)
        with r1:
            st.metric("Resume → Job Match", f"{match_score}%")
        with r2:
            if match_score >= 80:
                st.success("Excellent Match")
            elif match_score >= 60:
                st.warning("Good Match")
            else:
                st.error("Low Match")
        st.progress(match_score / 100)

        st.subheader("✅ Matching Skills")
        if matching_skills:
            for skill in matching_skills:
                st.success("✓ " + skill)
        else:
            st.warning("No matching skills found.")

        st.subheader("❌ Missing Job Skills")
        if missing_job_skills:
            for skill in missing_job_skills:
                st.error("✗ " + skill)
        else:
            st.success("🎉 All detected job skills are present!")

        st.subheader("📋 Detected Job Skills")
        if job_skills:
            for skill in job_skills:
                st.write("•", skill)
        else:
            st.warning("No technical skills detected.")

        st.subheader("💡 Recommendation")
        st.info(recommendation)

# =========================================================
# LOCAL JOB DATABASE
# =========================================================

st.header("💼 Recommended Jobs")
st.write("Jobs from your local demo database ranked according to your resume.")

try:
    jobs = load_jobs()
    recommendations = recommend_jobs(skills, jobs)
    min_score = st.slider("Minimum Match Score", 0, 100, 40, 5, key="local_job_min_score")
    filtered = [x for x in recommendations if x["score"] >= min_score]
    if filtered:
        for i, item in enumerate(filtered, 1):
            show_job(item, i)
    else:
        st.warning("No local jobs found above the selected match score.")
except FileNotFoundError:
    st.error("jobs.json was not found. Make sure it is inside the project folder.")
except Exception as error:
    st.error(f"Unable to load local jobs: {error}")

# =========================================================
# REAL JOB SEARCH
# =========================================================

st.header("🌐 Search Real Jobs")
st.write("Search current job listings and match them with your resume.")

search_col1, search_col2 = st.columns(2)

with search_col1:
    search_keyword = st.text_input("🔎 Job Role", value="Data Analyst")

with search_col2:
    search_location = st.text_input("📍 Location", value="India")

number_of_jobs = st.slider(
    "Number of Jobs",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
    key="real_job_count"
)

if st.button("🌐 Search Real Jobs", type="primary", key="real_job_search"):

    if not search_keyword.strip():
        st.warning("Please enter a job role.")
    else:
        try:
            with st.spinner("Searching real job listings..."):
                real_jobs = get_real_jobs(
                    search_keyword,
                    search_location,
                    number_of_jobs
                )

            if not real_jobs:
                st.warning("No jobs found. Try another job role or location.")
            else:
                st.success(f"Found {len(real_jobs)} jobs.")

                # Match every real job against the uploaded resume.
                matched_jobs = []

                for job in real_jobs:
                    job_text = (
                        job.get("title", "")
                        + " "
                        + job.get("description", "")
                    )
                    job_skills = extract_job_skills(job_text)
                    matching_skills, missing_skills = compare_skills(
                        skills,
                        job_skills
                    )
                    match_score = calculate_match_score(
                        matching_skills,
                        job_skills
                    )
                    matched_jobs.append({
                        "job": job,
                        "score": match_score,
                        "matching": matching_skills,
                        "missing": missing_skills
                    })

                # Highest match first.
                matched_jobs.sort(
                    key=lambda item: item["score"],
                    reverse=True
                )

                st.subheader("🎯 Best Matching Jobs")

                for index, item in enumerate(matched_jobs, start=1):
                    job = item["job"]
                    score_value = item["score"]
                    matching = item["matching"]
                    missing_job = item["missing"]

                    with st.container(border=True):
                        st.subheader(
                            f"{index}. {job.get('title', 'Unknown Job')}"
                        )

                        st.write(
                            f"🏢 **Company:** {job.get('company', 'Unknown')}"
                        )

                        st.write(
                            f"📍 **Location:** {job.get('location', 'India')}"
                        )

                        contract_type = job.get("contract_type", "")
                        if contract_type:
                            st.write(f"💼 **Type:** {contract_type}")

                        if score_value >= 80:
                            st.success(f"🎯 Match: {score_value}%")
                        elif score_value >= 60:
                            st.warning(f"🎯 Match: {score_value}%")
                        else:
                            st.error(f"🎯 Match: {score_value}%")

                        st.progress(max(0, min(score_value, 100)) / 100)

                        if matching:
                            st.write(
                                "✅ **Matching:** " + ", ".join(matching)
                            )

                        if missing_job:
                            st.write(
                                "❌ **Missing:** " + ", ".join(missing_job)
                            )

                        salary_min = job.get("salary_min")
                        salary_max = job.get("salary_max")
                        if salary_min is not None or salary_max is not None:
                            st.write(
                                f"💰 **Salary:** {salary_min or 'N/A'} - "
                                f"{salary_max or 'N/A'}"
                            )

                        description = job.get("description", "")
                        if description:
                            with st.expander("📋 View Job Description"):
                                st.write(description)

                        application_url = job.get("application_url", "")
                        if application_url:
                            st.link_button("🔗 View / Apply", application_url)

                        # =========================================
                        # SAVE REAL JOB
                        # =========================================

                        if st.button(
                            "⭐ Save Job",
                            key=f"save_real_job_{index}"
                        ):

                            saved = add_application(
                                title=job.get(
                                    "title",
                                    "Unknown Job"
                                ),
                                company=job.get(
                                    "company",
                                    "Unknown Company"
                                ),
                                location=job.get(
                                    "location",
                                    "Unknown"
                                ),
                                score=score_value,
                                application_url=application_url,
                                status="Saved"
                            )

                            if saved:
                                st.success(
                                    "⭐ Job saved successfully!"
                                )
                            else:
                                st.info(
                                    "This job is already saved."
                                )

        except Exception as error:
            st.error(f"Unable to search jobs: {error}")


# =========================================================
# STEP 15 - ADVANCED APPLICATION TRACKER + FOLLOW-UP SYSTEM
# =========================================================

migrate_application_file()
st.header("📋 Advanced Application Tracker")
st.write("Manage saved jobs, status, priority, dates, contacts, notes and follow-ups.")

applications = load_applications()
counts = get_status_counts(applications)
overdue = get_overdue_follow_ups(applications)
today_followups = get_today_follow_ups(applications)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("📋 Total", len(applications))
m2.metric("📤 Applied", counts.get("Applied", 0))
m3.metric("🎤 Interviews", counts.get("Interview", 0))
m4.metric("🎉 Offers", counts.get("Offer", 0) + counts.get("Selected", 0))
m5.metric("⏰ Overdue", len(overdue))

st.subheader("📊 Application Pipeline")
pipe = st.columns(8)
for col, (label, status) in zip(pipe, [
    ("⭐ Saved", "Saved"), ("📤 Applied", "Applied"),
    ("📝 Assessment", "Assessment"), ("🎤 Interview", "Interview"),
    ("💼 Offer", "Offer"), ("🎉 Selected", "Selected"),
    ("❌ Rejected", "Rejected"), ("🚫 Withdrawn", "Withdrawn")
]):
    col.metric(label, counts.get(status, 0))

st.subheader("⏰ Follow-Up Center")
if overdue:
    st.error(f"🔴 {len(overdue)} overdue follow-up(s).")
    for item in overdue:
        a = item["application"]
        st.warning(
            f"**{a.get('title', 'Unknown Job')}** at "
            f"**{a.get('company', 'Unknown Company')}** — due "
            f"{a.get('follow_up_date', '')}"
        )
elif today_followups:
    st.warning(f"🟡 {len(today_followups)} follow-up(s) due today.")
else:
    st.success("🟢 No overdue follow-ups.")

future = [x for x in get_follow_up_items(applications, True) if x["state"] == "upcoming"][:10]
if future:
    with st.expander("📅 Upcoming Follow-Ups"):
        for item in future:
            a = item["application"]
            st.write(
                f"• **{a.get('title', 'Unknown Job')}** — "
                f"{a.get('company', 'Unknown Company')} — "
                f"{a.get('follow_up_date', '')}"
            )

with st.expander("➕ Add Application Manually"):
    c1, c2 = st.columns(2)
    with c1:
        manual_title = st.text_input("💼 Job Title", key="manual15_title")
        manual_company = st.text_input("🏢 Company", key="manual15_company")
        manual_location = st.text_input("📍 Location", key="manual15_location")
        manual_url = st.text_input("🔗 Application URL", key="manual15_url")
    with c2:
        manual_status = st.selectbox("📌 Status", STATUS_OPTIONS, key="manual15_status")
        manual_priority = st.selectbox("🚨 Priority", PRIORITY_OPTIONS, index=1, key="manual15_priority")
        manual_score = st.number_input("🎯 Match Score", 0, 100, 0, key="manual15_score")
        manual_source = st.text_input("🌐 Source", key="manual15_source")
    manual_notes = st.text_area("📝 Notes", key="manual15_notes")

    if st.button("➕ Add Application", type="primary", key="manual15_add"):
        if not manual_title.strip() or not manual_company.strip():
            st.warning("Job title and company are required.")
        elif add_application(
            manual_title.strip(), manual_company.strip(), manual_location.strip(),
            manual_score, manual_url.strip(), manual_status, manual_priority,
            notes=manual_notes.strip(), source=manual_source.strip()
        ):
            st.success("✅ Application added.")
            st.rerun()
        else:
            st.info("This application already exists.")

st.subheader("🔎 Filter Applications")
f1, f2, f3 = st.columns(3)
status_filter = f1.selectbox("Status", ["All"] + STATUS_OPTIONS, key="tracker15_status")
priority_filter = f2.selectbox("Priority", ["All"] + PRIORITY_OPTIONS, key="tracker15_priority")
search_filter = f3.text_input("Search", key="tracker15_search")

filtered = []
for idx, item in enumerate(applications):
    searchable = " ".join([
        str(item.get("title", "")),
        str(item.get("company", "")),
        str(item.get("location", ""))
    ]).lower()
    if status_filter != "All" and item.get("status", "Saved") != status_filter:
        continue
    if priority_filter != "All" and item.get("priority", "Medium") != priority_filter:
        continue
    if search_filter.strip() and search_filter.strip().lower() not in searchable:
        continue
    filtered.append((idx, item))

st.write(f"Showing **{len(filtered)}** of **{len(applications)}** applications.")

if not filtered:
    st.info("No applications match your filters.")
else:
    for idx, item in filtered:
        with st.container(border=True):
            st.subheader(f"💼 {item.get('title', 'Unknown Job')}")
            a1, a2, a3 = st.columns(3)
            a1.write(f"🏢 **Company:** {item.get('company', 'Unknown')}")
            a2.write(f"📍 **Location:** {item.get('location', 'N/A')}")
            a3.write(f"🎯 **Match:** {item.get('score', 0)}%")

            b1, b2 = st.columns(2)
            current_status = item.get("status", "Saved")
            current_priority = item.get("priority", "Medium")
            new_status = b1.selectbox(
                "📌 Status", STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(current_status)
                if current_status in STATUS_OPTIONS else 0,
                key=f"tracker15_status_{idx}"
            )
            new_priority = b2.selectbox(
                "🚨 Priority", PRIORITY_OPTIONS,
                index=PRIORITY_OPTIONS.index(current_priority)
                if current_priority in PRIORITY_OPTIONS else 1,
                key=f"tracker15_priority_{idx}"
            )

            c1, c2 = st.columns(2)
            old_applied = item.get("applied_date", "")
            old_followup = item.get("follow_up_date", "")
            try:
                applied_default = date.fromisoformat(old_applied) if old_applied else None
            except ValueError:
                applied_default = None
            try:
                follow_default = date.fromisoformat(old_followup) if old_followup else None
            except ValueError:
                follow_default = None

            new_applied = c1.date_input(
                "📤 Applied Date", value=applied_default,
                key=f"tracker15_applied_{idx}"
            )
            new_followup = c2.date_input(
                "⏰ Follow-Up Date", value=follow_default,
                key=f"tracker15_followup_{idx}"
            )

            c1, c2 = st.columns(2)
            new_contact = c1.text_input(
                "👤 Contact Name", value=item.get("contact_name", ""),
                key=f"tracker15_contact_{idx}"
            )
            new_email = c2.text_input(
                "📧 Contact Email", value=item.get("contact_email", ""),
                key=f"tracker15_email_{idx}"
            )

            c1, c2 = st.columns(2)
            new_salary = c1.text_input(
                "💰 Salary / Compensation", value=item.get("salary", ""),
                key=f"tracker15_salary_{idx}"
            )
            new_source = c2.text_input(
                "🌐 Source", value=item.get("source", ""),
                key=f"tracker15_source_{idx}"
            )

            new_notes = st.text_area(
                "📝 Notes", value=item.get("notes", ""),
                key=f"tracker15_notes_{idx}"
            )

            x1, x2, x3 = st.columns(3)
            if x1.button("💾 Save Changes", key=f"tracker15_save_{idx}"):
                ok = update_application(
                    idx, status=new_status, priority=new_priority,
                    applied_date=new_applied.isoformat() if new_applied else "",
                    follow_up_date=new_followup.isoformat() if new_followup else "",
                    notes=new_notes, contact_name=new_contact,
                    contact_email=new_email, salary=new_salary,
                    source=new_source
                )
                if ok:
                    st.success("✅ Application updated.")
                    st.rerun()
                else:
                    st.error("Unable to update application.")

            url = item.get("application_url", "")
            if url:
                x2.link_button("🔗 Open Job", url)

            if x3.button("🗑️ Delete", key=f"tracker15_delete_{idx}"):
                if delete_application(idx):
                    st.success("Application deleted.")
                    st.rerun()

            follow_value = item.get("follow_up_date", "")
            if follow_value:
                try:
                    follow_date = date.fromisoformat(follow_value)
                    if follow_date < date.today():
                        st.error(f"🔴 Follow-up overdue: {follow_value}")
                    elif follow_date == date.today():
                        st.warning("🟡 Follow-up is due today.")
                    else:
                        st.info(f"📅 Follow-up scheduled for {follow_value}")
                except ValueError:
                    st.warning("Follow-up date is invalid.")

st.subheader("📤 Export Tracker")
if applications:
    import csv
    from io import StringIO
    buffer = StringIO()
    fields = [
        "title", "company", "location", "score", "status", "priority",
        "applied_date", "follow_up_date", "contact_name", "contact_email",
        "salary", "source", "notes", "application_url", "last_updated"
    ]
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    for item in applications:
        writer.writerow({field: item.get(field, "") for field in fields})
    st.download_button(
        "⬇️ Download Application Tracker CSV",
        data=buffer.getvalue(),
        file_name="application_tracker.csv",
        mime="text/csv",
        key="tracker15_csv"
    )
else:
    st.info("Add an application to export the tracker.")

# =========================================================
# STEP 11 - ADVANCED ATS ANALYZER
# =========================================================

def normalize_ats_text(value):
    """Normalize text for reliable ATS matching."""
    value = value.lower()
    value = re.sub(r"[\u2010-\u2015]", "-", value)
    value = re.sub(r"[^a-z0-9+#.\-/ ]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def contains_ats_term(text, term):
    """Match a term while allowing common punctuation/spacing."""
    normalized_text = normalize_ats_text(text)
    normalized_term = normalize_ats_text(term)

    if normalized_term in normalized_text:
        return True

    # Common abbreviation/variation support.
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
    """Extract supported technical, role and workplace keywords."""
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
    """Detect common job-role words from the job description."""
    roles = [
        "Data Analyst",
        "Data Scientist",
        "Machine Learning Engineer",
        "AI Engineer",
        "AI/ML Engineer",
        "Software Engineer",
        "Software Developer",
        "Python Developer",
        "Java Developer",
        "Full Stack Developer",
        "Backend Developer",
        "Frontend Developer",
        "Web Developer",
        "Business Analyst",
        "Data Engineer",
        "Cloud Engineer",
        "DevOps Engineer",
        "MLOps Engineer",
        "AI Intern",
        "ML Intern",
        "Data Analyst Intern",
        "Data Science Intern",
        "Software Developer Intern",
        "Software Engineer Intern"
    ]

    return [
        role
        for role in roles
        if contains_ats_term(job_text, role)
    ]


def analyze_ats_keywords(resume_text, job_text):
    """Compare job keywords against the actual resume."""
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

        keyword_score = round(
            len(matching) / len(all_keywords) * 30
        )

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
    """Calculate the technical skill score out of 20."""
    ats_data = analyze_ats_keywords(
        resume_text,
        job_text
    )

    groups = ats_data["groups"]

    total = 0
    matched = 0

    for terms in groups.values():

        for term in terms:

            total += 1

            if contains_ats_term(
                resume_text,
                term
            ):

                matched += 1

    score = (
        round(matched / total * 20)
        if total
        else 0
    )

    return {
        "score": min(score, 20),
        "matched": matched,
        "required": total
    }


def analyze_experience(resume_text, experience):
    """Score experience evidence out of 15."""
    lower = resume_text.lower()

    experience_section = bool(experience)

    role_words = [
        "intern",
        "internship",
        "experience",
        "developer",
        "engineer",
        "analyst",
        "trainee",
        "work experience",
        "professional experience"
    ]

    role_evidence = sum(
        1
        for word in role_words
        if word in lower
    )

    date_pattern = r"\b(?:19|20)\d{2}\b"
    date_count = len(
        re.findall(
            date_pattern,
            resume_text
        )
    )

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

    if re.search(
        r"\b\d+(?:\.\d+)?\s*%",
        resume_text
    ):
        score += 2

    if re.search(
        r"\b(?:20|[1-9])\+?\b",
        resume_text
    ):
        score += 1

    return {
        "score": min(score, 15),
        "feedback": "Experience evidence was detected.",
        "date_count": date_count
    }


def analyze_projects(resume_text, projects):
    """Score projects out of 10."""
    if not projects:

        return {
            "score": 0,
            "feedback": "No project section was detected."
        }

    score = min(
        len(projects) * 3,
        6
    )

    project_text = " ".join(projects)

    technical_words = [
        "python", "sql", "machine learning",
        "deep learning", "api", "dashboard",
        "tensorflow", "pytorch", "power bi",
        "data", "model", "github", "deployed"
    ]

    technical_hits = sum(
        1
        for word in technical_words
        if word in project_text.lower()
    )

    score += min(
        technical_hits,
        2
    )

    if re.search(
        r"\b\d+(?:\.\d+)?\s*%",
        project_text
    ):
        score += 2

    return {
        "score": min(score, 10),
        "feedback": (
            "Projects were detected. Add technologies "
            "and measurable results to strengthen them."
        )
    }


def analyze_achievements(resume_text):
    """Score measurable achievements out of 10."""
    percentage_matches = re.findall(
        r"\b\d+(?:\.\d+)?\s*%",
        resume_text
    )

    metric_patterns = [
        r"\b\d+\+?\s*(?:users|customers|records|projects|models|days|months|years)\b",
        r"\b\d+(?:\.\d+)?\s*(?:x|times)\b",
        r"\b(?:increased|improved|reduced|decreased|saved|achieved|boosted)\b"
    ]

    metric_hits = 0

    for pattern in metric_patterns:

        metric_hits += len(
            re.findall(
                pattern,
                resume_text,
                flags=re.IGNORECASE
            )
        )

    score = min(
        len(percentage_matches) * 2
        + min(metric_hits, 6),
        10
    )

    return {
        "score": score,
        "percentages": len(percentage_matches),
        "metrics": metric_hits
    }


def analyze_action_verbs(resume_text):
    """Score strong resume action verbs out of 5."""
    action_verbs = [
        "developed", "designed", "implemented",
        "built", "created", "analyzed",
        "optimized", "automated", "improved",
        "deployed", "managed", "led",
        "tested", "predicted", "processed",
        "integrated", "engineered", "configured",
        "trained", "evaluated", "delivered"
    ]

    lower = resume_text.lower()

    found = [
        verb
        for verb in action_verbs
        if re.search(
            r"\b" + re.escape(verb) + r"\b",
            lower
        )
    ]

    score = min(
        round(len(found) / 5),
        5
    )

    weak_phrases = [
        "worked on",
        "responsible for",
        "helped with",
        "was involved in",
        "did"
    ]

    weak_found = [
        phrase
        for phrase in weak_phrases
        if phrase in lower
    ]

    return {
        "score": score,
        "found": found,
        "weak": weak_found
    }


def analyze_structure(
    resume_text,
    education,
    projects,
    experience,
    certifications
):
    """Score resume structure out of 5."""
    lower = resume_text.lower()

    section_checks = {
        "Contact": (
            "@" in resume_text
            or bool(
                re.search(
                    r"\b[6-9]\d{9}\b",
                    resume_text
                )
            )
        ),
        "Skills": "skill" in lower,
        "Education": bool(education) or "education" in lower,
        "Projects": bool(projects) or "project" in lower,
        "Experience": bool(experience) or "experience" in lower,
        "Certifications": bool(certifications) or "certification" in lower
    }

    found = [
        name
        for name, present in section_checks.items()
        if present
    ]

    # Six checks, normalized to five marks.
    score = round(
        len(found) / len(section_checks) * 5
    )

    return {
        "score": min(score, 5),
        "found": found,
        "missing": [
            name
            for name, present in section_checks.items()
            if not present
        ]
    }


def analyze_resume_length(resume_text):
    """Provide length guidance without harshly penalizing freshers."""
    words = len(
        re.findall(
            r"\b[\w+#.-]+\b",
            resume_text
        )
    )

    if words < 250:

        message = (
            "Resume is very short. Add relevant projects, "
            "skills and achievements."
        )

        status = "Needs Improvement"

    elif words <= 900:

        message = (
            "Resume length is generally reasonable."
        )

        status = "Good"

    else:

        message = (
            "Resume may be too long. Remove repetitive "
            "or low-value content."
        )

        status = "Review"

    return {
        "words": words,
        "message": message,
        "status": status
    }


def analyze_keyword_stuffing(resume_text):
    """Detect unusually repeated technical keywords."""
    technical_terms = [
        "python", "java", "sql", "machine learning",
        "deep learning", "power bi", "excel",
        "pandas", "numpy", "tensorflow", "pytorch",
        "aws", "azure", "docker", "git"
    ]

    lower = resume_text.lower()

    counts = {}

    for term in technical_terms:

        counts[term] = len(
            re.findall(
                r"(?<!\w)"
                + re.escape(term)
                + r"(?!\w)",
                lower
            )
        )

    repeated = {
        term: count
        for term, count in counts.items()
        if count >= 6
    }

    return repeated


def analyze_job_title(resume_text, job_text):
    """Compare detected job roles with resume terminology."""
    roles = extract_job_role_keywords(job_text)

    if not roles:

        return {
            "score": 5,
            "roles": [],
            "message": (
                "No clear job title was detected; "
                "keyword analysis was used instead."
            )
        }

    matched_roles = [
        role
        for role in roles
        if contains_ats_term(
            resume_text,
            role
        )
    ]

    if matched_roles:

        score = 5

    elif any(
        term in normalize_ats_text(resume_text)
        for term in [
            "data", "analyst", "machine learning",
            "software", "developer", "engineer",
            "artificial intelligence"
        ]
    ):

        score = 3

    else:

        score = 1

    return {
        "score": score,
        "roles": roles,
        "matched": matched_roles,
        "message": (
            "Job title terminology is aligned."
            if matched_roles
            else
            "Consider using the target role title "
            "naturally in your summary when accurate."
        )
    }


def generate_advanced_ats_recommendations(
    keyword_data,
    experience_data,
    project_data,
    achievement_data,
    action_data,
    structure_data,
    length_data,
    repeated_keywords,
    title_data
):
    """Create actionable ATS recommendations."""
    recommendations = []

    if keyword_data["missing"]:

        recommendations.append(
            "Add missing job keywords only when you "
            "genuinely have the related knowledge or experience."
        )

    if keyword_data["score"] < 24:

        recommendations.append(
            "Tailor your Skills, Projects and Summary "
            "to the target job description."
        )

    if experience_data["score"] < 10:

        recommendations.append(
            "Strengthen experience bullets with your role, "
            "technology used and measurable outcomes."
        )

    if project_data["score"] < 7:

        recommendations.append(
            "Add project technologies, your contribution "
            "and measurable results."
        )

    if achievement_data["score"] < 6:

        recommendations.append(
            "Add measurable achievements such as accuracy, "
            "performance improvement, users, records or time saved."
        )

    if action_data["score"] < 3:

        recommendations.append(
            "Start resume bullets with strong action verbs "
            "such as Developed, Implemented, Analyzed or Optimized."
        )

    if action_data["weak"]:

        recommendations.append(
            "Replace weak phrases such as "
            + ", ".join(action_data["weak"])
            + " with specific action verbs."
        )

    if structure_data["missing"]:

        recommendations.append(
            "Consider adding these sections if relevant: "
            + ", ".join(structure_data["missing"])
            + "."
        )

    if length_data["words"] > 900:

        recommendations.append(
            "Reduce repetitive content and keep only "
            "job-relevant information."
        )

    if length_data["words"] < 250:

        recommendations.append(
            "Add stronger project, skills and achievement details."
        )

    if repeated_keywords:

        repeated_text = ", ".join(
            f"{key} ({value}x)"
            for key, value in repeated_keywords.items()
        )

        recommendations.append(
            "Avoid excessive keyword repetition: "
            + repeated_text
            + "."
        )

    if title_data["score"] < 4:

        recommendations.append(
            "Use the target job title naturally in your "
            "professional summary when truthful."
        )

    if not recommendations:

        recommendations.append(
            "Your resume has good ATS coverage. "
            "Continue tailoring it to each specific job."
        )

    return recommendations


def calculate_advanced_ats_score(
    keyword_score,
    skill_score,
    experience_score,
    project_score,
    achievement_score,
    education_score,
    action_score,
    structure_score,
    title_score
):
    """
    Calculate the final ATS score.

    We use:
    Keywords 30
    Skills 20
    Experience 15
    Projects 10
    Achievements 10
    Education 5
    Action verbs 5
    Structure 5

    Job-title relevance is shown separately so the
    final score remains exactly 100 points.
    """

    # Education is already represented as a 5-point score.
    total = (
        keyword_score
        + skill_score
        + experience_score
        + project_score
        + achievement_score
        + education_score
        + action_score
        + structure_score
    )

    return min(
        max(round(total), 0),
        100
    )


# =========================================================
# ADVANCED ATS ANALYZER UI
# =========================================================

st.divider()

st.header(
    "🤖 Advanced ATS Analyzer"
)

st.write(
    "Get a detailed 100-point ATS analysis by comparing "
    "your uploaded resume with a target job description."
)

advanced_job_description = st.text_area(
    "🎯 Paste Target Job Description",
    height=300,
    placeholder=(
        "Paste the complete job description here..."
    ),
    key="advanced_ats_job_description"
)

if st.button(
    "🚀 Run Advanced ATS Analysis",
    type="primary",
    key="run_advanced_ats"
):

    if not advanced_job_description.strip():

        st.warning(
            "Please paste a job description first."
        )

    else:

        # =================================================
        # RUN ALL ANALYZERS
        # =================================================

        keyword_data = analyze_ats_keywords(
            text,
            advanced_job_description
        )

        skill_data = analyze_skill_categories(
            text,
            advanced_job_description
        )

        experience_data = analyze_experience(
            text,
            experience
        )

        project_data = analyze_projects(
            text,
            projects
        )

        achievement_data = analyze_achievements(
            text
        )

        action_data = analyze_action_verbs(
            text
        )

        structure_data = analyze_structure(
            text,
            education,
            projects,
            experience,
            certifications
        )

        length_data = analyze_resume_length(
            text
        )

        repeated_keywords = analyze_keyword_stuffing(
            text
        )

        title_data = analyze_job_title(
            text,
            advanced_job_description
        )

        # Education gets 5 marks.
        education_score = 5 if education else 0

        final_ats_score = calculate_advanced_ats_score(
            keyword_data["score"],
            skill_data["score"],
            experience_data["score"],
            project_data["score"],
            achievement_data["score"],
            education_score,
            action_data["score"],
            structure_data["score"],
            title_data["score"]
        )

        recommendations = (
            generate_advanced_ats_recommendations(
                keyword_data,
                experience_data,
                project_data,
                achievement_data,
                action_data,
                structure_data,
                length_data,
                repeated_keywords,
                title_data
            )
        )

        # =================================================
        # MAIN SCORE
        # =================================================

        st.subheader(
            "⭐ Advanced ATS Score"
        )

        score_col1, score_col2 = st.columns(2)

        with score_col1:

            st.metric(
                "ATS Score",
                f"{final_ats_score}/100"
            )

        with score_col2:

            if final_ats_score >= 85:

                st.success(
                    "🟢 Excellent ATS Readiness"
                )

            elif final_ats_score >= 70:

                st.warning(
                    "🟡 Good ATS Readiness"
                )

            elif final_ats_score >= 50:

                st.warning(
                    "🟠 Needs Improvement"
                )

            else:

                st.error(
                    "🔴 Low ATS Readiness"
                )

        st.progress(
            final_ats_score / 100
        )

        # =================================================
        # SCORE BREAKDOWN
        # =================================================

        st.subheader(
            "📊 ATS Score Breakdown"
        )

        score_rows = [
            ("🎯 Job Keywords", keyword_data["score"], 30),
            ("💻 Technical Skills", skill_data["score"], 20),
            ("💼 Experience", experience_data["score"], 15),
            ("📁 Projects", project_data["score"], 10),
            ("📈 Achievements", achievement_data["score"], 10),
            ("🎓 Education", education_score, 5),
            ("✍️ Action Verbs", action_data["score"], 5),
            ("📄 Structure", structure_data["score"], 5),
        ]

        for label, earned, maximum in score_rows:

            row_col1, row_col2 = st.columns([4, 1])

            with row_col1:

                st.write(
                    f"**{label}**"
                )

            with row_col2:

                st.write(
                    f"**{earned}/{maximum}**"
                )

            st.progress(
                earned / maximum
            )

        # =================================================
        # JOB TITLE
        # =================================================

        st.subheader(
            "🎯 Job Title Relevance"
        )

        if title_data["roles"]:

            st.write(
                "**Detected Target Role(s):** "
                + ", ".join(title_data["roles"])
            )

            if title_data.get("matched"):

                st.success(
                    "Matched role: "
                    + ", ".join(title_data["matched"])
                )

            else:

                st.warning(
                    title_data["message"]
                )

        else:

            st.info(
                title_data["message"]
            )

        # =================================================
        # KEYWORD ANALYSIS
        # =================================================

        st.subheader(
            "🔑 Keyword Analysis"
        )

        k1, k2, k3 = st.columns(3)

        with k1:

            st.metric(
                "Required Keywords",
                len(keyword_data["all"])
            )

        with k2:

            st.metric(
                "Matching Keywords",
                len(keyword_data["matching"])
            )

        with k3:

            st.metric(
                "Missing Keywords",
                len(keyword_data["missing"])
            )

        if keyword_data["matching"]:

            with st.expander(
                "✅ Matching Keywords",
                expanded=True
            ):

                st.write(
                    ", ".join(
                        keyword_data["matching"]
                    )
                )

        if keyword_data["missing"]:

            with st.expander(
                "❌ Missing Keywords",
                expanded=True
            ):

                for keyword in keyword_data["missing"]:

                    st.warning(
                        "➕ " + keyword
                    )

        # =================================================
        # SKILL CATEGORY ANALYSIS
        # =================================================

        st.subheader(
            "💻 Technical Skill Analysis"
        )

        if keyword_data["groups"]:

            for category, terms in (
                keyword_data["groups"].items()
            ):

                with st.expander(
                    f"📌 {category}"
                ):

                    for term in terms:

                        if contains_ats_term(
                            text,
                            term
                        ):

                            st.success(
                                "✅ " + term
                            )

                        else:

                            st.error(
                                "❌ " + term
                            )

        else:

            st.info(
                "No supported technical skill keywords "
                "were detected in the job description."
            )

        # =================================================
        # EXPERIENCE
        # =================================================

        st.subheader(
            "💼 Experience Analysis"
        )

        st.metric(
            "Experience Score",
            f"{experience_data['score']}/15"
        )

        st.info(
            experience_data["feedback"]
        )

        if experience_data["date_count"] < 2:

            st.warning(
                "Add clear dates for roles, internships or "
                "experience where applicable."
            )

        # =================================================
        # PROJECTS
        # =================================================

        st.subheader(
            "📁 Project Analysis"
        )

        st.metric(
            "Project Score",
            f"{project_data['score']}/10"
        )

        st.info(
            project_data["feedback"]
        )

        # =================================================
        # ACHIEVEMENTS
        # =================================================

        st.subheader(
            "📈 Achievement Analysis"
        )

        a1, a2, a3 = st.columns(3)

        with a1:

            st.metric(
                "Achievement Score",
                f"{achievement_data['score']}/10"
            )

        with a2:

            st.metric(
                "Percentages Found",
                achievement_data["percentages"]
            )

        with a3:

            st.metric(
                "Metric Evidence",
                achievement_data["metrics"]
            )

        if achievement_data["score"] < 6:

            st.warning(
                "Your resume has limited measurable "
                "achievement evidence."
            )

        else:

            st.success(
                "Good measurable achievement evidence detected."
            )

        # =================================================
        # ACTION VERBS
        # =================================================

        st.subheader(
            "✍️ Action Verb Analysis"
        )

        st.metric(
            "Action Verb Score",
            f"{action_data['score']}/5"
        )

        if action_data["found"]:

            st.write(
                "**Strong verbs found:** "
                + ", ".join(
                    action_data["found"]
                )
            )

        if action_data["weak"]:

            st.warning(
                "Weak phrases detected: "
                + ", ".join(
                    action_data["weak"]
                )
            )

        # =================================================
        # STRUCTURE
        # =================================================

        st.subheader(
            "📄 Resume Structure"
        )

        structure_col1, structure_col2 = st.columns(2)

        with structure_col1:

            st.metric(
                "Structure Score",
                f"{structure_data['score']}/5"
            )

        with structure_col2:

            st.write(
                "Detected: "
                + (
                    ", ".join(
                        structure_data["found"]
                    )
                    if structure_data["found"]
                    else "None"
                )
            )

        if structure_data["missing"]:

            st.warning(
                "Sections not detected: "
                + ", ".join(
                    structure_data["missing"]
                )
            )

        # =================================================
        # LENGTH
        # =================================================

        st.subheader(
            "📏 Resume Length"
        )

        length_col1, length_col2 = st.columns(2)

        with length_col1:

            st.metric(
                "Word Count",
                length_data["words"]
            )

        with length_col2:

            st.write(
                f"**Status:** {length_data['status']}"
            )

        st.info(
            length_data["message"]
        )

        # =================================================
        # KEYWORD STUFFING
        # =================================================

        st.subheader(
            "🔁 Keyword Repetition"
        )

        if repeated_keywords:

            for keyword, count in (
                repeated_keywords.items()
            ):

                st.warning(
                    f"⚠️ {keyword.title()} appears "
                    f"{count} times."
                )

            st.info(
                "Use important keywords naturally. "
                "Do not repeat keywords just to increase "
                "the ATS score."
            )

        else:

            st.success(
                "No excessive repetition detected."
            )

        # =================================================
        # RECOMMENDATIONS
        # =================================================

        st.subheader(
            "💡 ATS Improvement Recommendations"
        )

        for number, recommendation in enumerate(
            recommendations,
            start=1
        ):

            st.info(
                f"**{number}.** {recommendation}"
            )

        # =================================================
        # ATS REPORT DOWNLOAD
        # =================================================

        report = []

        report.append(
            "ADVANCED ATS ANALYSIS REPORT"
        )

        report.append(
            "=" * 45
        )

        report.append(
            f"Overall ATS Score: {final_ats_score}/100"
        )

        report.append("")

        report.append(
            "SCORE BREAKDOWN"
        )

        for label, earned, maximum in score_rows:

            report.append(
                f"{label}: {earned}/{maximum}"
            )

        report.append("")

        report.append(
            "MATCHING KEYWORDS"
        )

        report.extend(
            [
                f"- {item}"
                for item in keyword_data["matching"]
            ]
            or ["- None"]
        )

        report.append("")

        report.append(
            "MISSING KEYWORDS"
        )

        report.extend(
            [
                f"- {item}"
                for item in keyword_data["missing"]
            ]
            or ["- None"]
        )

        report.append("")

        report.append(
            "RECOMMENDATIONS"
        )

        report.extend(
            [
                f"- {item}"
                for item in recommendations
            ]
        )

        report_text = "\n".join(
            report
        )

        st.download_button(
            "⬇️ Download ATS Report",
            data=report_text,
            file_name="advanced_ats_report.txt",
            mime="text/plain",
            key="download_advanced_ats_report"
        )


# =========================================================
# STEP 12 - SEMANTIC AI JOB MATCHING
# =========================================================
#
# This module uses Sentence Transformers to compare the
# meaning of a resume and a job description instead of
# relying only on exact keyword matches.
#
# Model:
# all-MiniLM-L6-v2
#
# Matching score:
#   70% semantic similarity
#   20% keyword overlap
#   10% job-title relevance
#
# If sentence-transformers is not installed, the UI shows
# a clear installation message instead of crashing the app.
# =========================================================

@st.cache_resource(show_spinner=False)
def load_semantic_model():
    """
    Load the Sentence Transformer model once and cache it.
    The first run may download the model from Hugging Face.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        "all-MiniLM-L6-v2"
    )


def calculate_semantic_similarity(
    resume_text,
    job_description
):
    """
    Calculate cosine similarity between the resume and
    job description embeddings.

    Returns a percentage from 0 to 100.
    """

    model = load_semantic_model()

    resume_embedding = model.encode(
        resume_text,
        normalize_embeddings=True
    )

    job_embedding = model.encode(
        job_description,
        normalize_embeddings=True
    )

    similarity = float(
        resume_embedding @ job_embedding
    )

    # Cosine similarity can theoretically be negative.
    similarity = max(
        0.0,
        min(similarity, 1.0)
    )

    return round(
        similarity * 100,
        2
    )


def calculate_semantic_keyword_score(
    resume_text,
    job_description
):
    """
    Calculate keyword overlap as a supporting signal.

    This is deliberately secondary to semantic similarity.
    """

    job_data = analyze_ats_keywords(
        resume_text,
        job_description
    )

    total = len(
        job_data["all"]
    )

    matched = len(
        job_data["matching"]
    )

    if total == 0:
        return 0

    return round(
        matched / total * 100,
        2
    )


def calculate_title_relevance_score(
    resume_text,
    job_description
):
    """
    Convert the existing job-title analyzer to a percentage.
    """

    title_data = analyze_job_title(
        resume_text,
        job_description
    )

    return round(
        title_data["score"] / 5 * 100,
        2
    )


def calculate_combined_semantic_score(
    semantic_score,
    keyword_score,
    title_score
):
    """
    Final semantic job-match score.

    Semantic similarity has the largest weight because it
    captures meaning rather than only exact words.
    """

    final_score = (
        semantic_score * 0.70
        + keyword_score * 0.20
        + title_score * 0.10
    )

    return round(
        max(0, min(final_score, 100)),
        2
    )


def get_semantic_match_label(score):
    """Return a human-readable interpretation."""
    if score >= 85:
        return (
            "🟢 Excellent Semantic Match",
            "The resume is highly relevant to this job."
        )

    if score >= 70:
        return (
            "🟢 Strong Semantic Match",
            "The resume is strongly related to the job."
        )

    if score >= 55:
        return (
            "🟡 Moderate Semantic Match",
            "The resume has useful overlap but can be tailored."
        )

    if score >= 40:
        return (
            "🟠 Weak Semantic Match",
            "Several important requirements may be missing."
        )

    return (
        "🔴 Low Semantic Match",
        "The resume is not strongly aligned with this job."
    )


def build_semantic_match_explanation(
    semantic_score,
    keyword_score,
    title_score,
    keyword_data
):
    """
    Generate a simple explanation of why the score was
    high or low.
    """

    explanation = []

    if semantic_score >= 75:

        explanation.append(
            "The resume and job description have strong "
            "semantic similarity."
        )

    elif semantic_score >= 55:

        explanation.append(
            "The resume and job description have moderate "
            "semantic similarity."
        )

    else:

        explanation.append(
            "The resume and job description have limited "
            "semantic similarity."
        )

    if keyword_score >= 70:

        explanation.append(
            "Most detected job keywords are already present "
            "in the resume."
        )

    elif keyword_score >= 40:

        explanation.append(
            "Some important job keywords are present, but "
            "several are missing."
        )

    else:

        explanation.append(
            "Many detected job keywords are missing from the resume."
        )

    if title_score >= 80:

        explanation.append(
            "The target job title is well aligned with the resume."
        )

    elif title_score >= 50:

        explanation.append(
            "The resume contains related role terminology."
        )

    else:

        explanation.append(
            "The resume does not strongly reflect the target role."
        )

    if keyword_data["missing"]:

        explanation.append(
            "Important missing keywords include: "
            + ", ".join(
                keyword_data["missing"][:8]
            )
            + "."
        )

    return explanation


# =========================================================
# STEP 12 UI
# =========================================================

st.divider()

st.header(
    "🧠 Semantic AI Job Matching"
)

st.write(
    "Compare your resume and a target job by meaning, "
    "not only by exact keywords. Sentence Transformers "
    "creates embeddings for both texts and calculates "
    "their semantic similarity."
)

st.info(
    "💡 The first analysis may take longer because the "
    "AI embedding model may need to be downloaded and loaded."
)

semantic_job_description = st.text_area(
    "🎯 Paste Job Description for Semantic Matching",
    height=300,
    placeholder=(
        "Paste the complete job description here..."
    ),
    key="semantic_job_description"
)

if st.button(
    "🧠 Calculate Semantic Match",
    type="primary",
    key="calculate_semantic_match"
):

    if not semantic_job_description.strip():

        st.warning(
            "Please paste a job description first."
        )

    else:

        try:

            with st.spinner(
                "🧠 Creating AI embeddings and comparing your resume..."
            ):

                semantic_score = (
                    calculate_semantic_similarity(
                        text,
                        semantic_job_description
                    )
                )

                semantic_keyword_score = (
                    calculate_semantic_keyword_score(
                        text,
                        semantic_job_description
                    )
                )

                semantic_title_score = (
                    calculate_title_relevance_score(
                        text,
                        semantic_job_description
                    )
                )

                semantic_final_score = (
                    calculate_combined_semantic_score(
                        semantic_score,
                        semantic_keyword_score,
                        semantic_title_score
                    )
                )

                semantic_keyword_data = (
                    analyze_ats_keywords(
                        text,
                        semantic_job_description
                    )
                )

                semantic_explanation = (
                    build_semantic_match_explanation(
                        semantic_score,
                        semantic_keyword_score,
                        semantic_title_score,
                        semantic_keyword_data
                    )
                )

            # =================================================
            # MAIN SCORE
            # =================================================

            st.subheader(
                "🎯 Semantic Job Match"
            )

            main1, main2 = st.columns(2)

            with main1:

                st.metric(
                    "Final AI Match",
                    f"{semantic_final_score}%"
                )

            with main2:

                label, message = (
                    get_semantic_match_label(
                        semantic_final_score
                    )
                )

                st.success(
                    label
                )

            st.progress(
                semantic_final_score / 100
            )

            st.write(
                message
            )

            # =================================================
            # SCORE COMPONENTS
            # =================================================

            st.subheader(
                "📊 Match Components"
            )

            component_data = [
                (
                    "🧠 Semantic Similarity",
                    semantic_score,
                    "70%"
                ),
                (
                    "🔑 Keyword Overlap",
                    semantic_keyword_score,
                    "20%"
                ),
                (
                    "🎯 Job Title Relevance",
                    semantic_title_score,
                    "10%"
                )
            ]

            for component, value, weight in component_data:

                c1, c2 = st.columns([4, 1])

                with c1:

                    st.write(
                        f"**{component}** "
                        f"(Weight: {weight})"
                    )

                with c2:

                    st.write(
                        f"**{value}%**"
                    )

                st.progress(
                    value / 100
                )

            # =================================================
            # WHY THIS MATCH
            # =================================================

            st.subheader(
                "🔍 Why This Score?"
            )

            for explanation in semantic_explanation:

                st.info(
                    "• " + explanation
                )

            # =================================================
            # MATCHING KEYWORDS
            # =================================================

            st.subheader(
                "✅ Matching Job Keywords"
            )

            if semantic_keyword_data["matching"]:

                st.success(
                    ", ".join(
                        semantic_keyword_data["matching"]
                    )
                )

            else:

                st.warning(
                    "No supported matching keywords detected."
                )

            # =================================================
            # MISSING KEYWORDS
            # =================================================

            st.subheader(
                "❌ Missing Job Keywords"
            )

            if semantic_keyword_data["missing"]:

                for keyword in (
                    semantic_keyword_data["missing"]
                ):

                    st.warning(
                        "➕ " + keyword
                    )

            else:

                st.success(
                    "No detected job keywords are missing."
                )

            # =================================================
            # RECOMMENDATION
            # =================================================

            st.subheader(
                "💡 Recommendation"
            )

            if semantic_final_score >= 85:

                st.success(
                    "Your resume is highly relevant. "
                    "You can apply, but still verify that "
                    "all required skills are genuinely present."
                )

            elif semantic_final_score >= 70:

                st.success(
                    "Your resume is a strong match. "
                    "Tailor the summary and project bullets "
                    "to the specific job before applying."
                )

            elif semantic_final_score >= 55:

                st.warning(
                    "Your resume has moderate relevance. "
                    "Improve the missing keywords and "
                    "job-specific project evidence."
                )

            else:

                st.error(
                    "This is a weak match. Consider targeting "
                    "a more suitable role or improving your "
                    "skills and project evidence first."
                )

            # =================================================
            # DOWNLOAD SEMANTIC MATCH REPORT
            # =================================================

            semantic_report = []

            semantic_report.append(
                "SEMANTIC AI JOB MATCH REPORT"
            )

            semantic_report.append(
                "=" * 45
            )

            semantic_report.append(
                f"Final AI Match: {semantic_final_score}%"
            )

            semantic_report.append(
                f"Semantic Similarity: {semantic_score}%"
            )

            semantic_report.append(
                f"Keyword Overlap: {semantic_keyword_score}%"
            )

            semantic_report.append(
                f"Job Title Relevance: {semantic_title_score}%"
            )

            semantic_report.append("")

            semantic_report.append(
                "MATCHING KEYWORDS:"
            )

            semantic_report.extend(
                [
                    f"- {item}"
                    for item in semantic_keyword_data["matching"]
                ]
                or ["- None"]
            )

            semantic_report.append("")

            semantic_report.append(
                "MISSING KEYWORDS:"
            )

            semantic_report.extend(
                [
                    f"- {item}"
                    for item in semantic_keyword_data["missing"]
                ]
                or ["- None"]
            )

            semantic_report.append("")

            semantic_report.append(
                "EXPLANATION:"
            )

            semantic_report.extend(
                [
                    f"- {item}"
                    for item in semantic_explanation
                ]
            )

            semantic_report_text = "\n".join(
                semantic_report
            )

            st.download_button(
                "⬇️ Download Semantic Match Report",
                data=semantic_report_text,
                file_name="semantic_job_match_report.txt",
                mime="text/plain",
                key="download_semantic_match_report"
            )

        except ImportError:

            st.error(
                "❌ Sentence Transformers is not installed."
            )

            st.code(
                "pip install sentence-transformers scikit-learn"
            )

            st.info(
                "After installation, restart Streamlit "
                "and run the analysis again."
            )

        except Exception as error:

            st.error(
                f"Unable to calculate semantic match: {error}"
            )

            st.info(
                "If this is the first run, make sure your "
                "computer has internet access so the embedding "
                "model can be downloaded."
            )


# =========================================================
# STEP 13 - AI COVER LETTER GENERATOR
# =========================================================
#
# Generates a personalized cover letter from:
#   1. Uploaded resume
#   2. Target job description
#   3. Candidate/job details
#
# It uses the existing ATS keyword analyzer and project/
# education extraction already present in this application.
#
# This version works without an external AI API key.
# It uses intelligent template selection and job-specific
# content. A true LLM provider can be integrated later.
# =========================================================


def clean_cover_letter_value(value):
    """Clean user-entered values before inserting them."""
    value = str(value or "").strip()
    value = re.sub(r"\s+", " ", value)
    return value


def extract_candidate_name_from_resume(resume_text):
    """
    Try to find a likely candidate name from the first few
    non-empty lines. The user can always override it.
    """
    lines = [
        line.strip()
        for line in resume_text.splitlines()
        if line.strip()
    ]

    for line in lines[:8]:

        clean = re.sub(
            r"[^A-Za-z .'-]",
            "",
            line
        ).strip()

        words = clean.split()

        if (
            2 <= len(words) <= 4
            and
            not any(
                char.isdigit()
                for char in line
            )
            and
            "@" not in line
            and
            len(clean) <= 60
        ):

            blocked = {
                "resume",
                "curriculum vitae",
                "cv",
                "profile",
                "objective",
                "summary",
                "skills",
                "education"
            }

            if clean.lower() not in blocked:
                return clean

    return ""


def extract_cover_letter_job_title(job_text):
    """Find a likely job title from the first part of the JD."""
    roles = extract_job_role_keywords(job_text)

    if roles:
        return roles[0]

    lines = [
        line.strip()
        for line in job_text.splitlines()
        if line.strip()
    ]

    for line in lines[:10]:

        if 3 <= len(line) <= 100:

            lower = line.lower()

            if any(
                word in lower
                for word in [
                    "analyst",
                    "developer",
                    "engineer",
                    "intern",
                    "scientist",
                    "manager",
                    "designer",
                    "consultant",
                    "specialist"
                ]
            ):

                return line

    return "the position"


def extract_cover_letter_company(job_text):
    """
    Look for simple 'Company:' or 'Organization:' patterns.
    The UI also lets the user override this.
    """

    patterns = [
        r"company\s*[:\-]\s*([^\n]+)",
        r"organization\s*[:\-]\s*([^\n]+)",
        r"employer\s*[:\-]\s*([^\n]+)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            job_text,
            flags=re.IGNORECASE
        )

        if match:

            return clean_cover_letter_value(
                match.group(1)
            )

    return ""


def select_cover_letter_skills(
    resume_text,
    job_text,
    maximum=6
):
    """Return job skills that are actually present in the resume."""
    job_data = analyze_ats_keywords(
        resume_text,
        job_text
    )

    matching = job_data["matching"]

    return matching[:maximum]


def select_cover_letter_projects(
    resume_text,
    projects,
    job_text,
    maximum=2
):
    """
    Select project lines that contain words relevant to the
    target job. If no strong relevance is detected, use the
    first available projects rather than inventing projects.
    """

    if not projects:
        return []

    job_lower = job_text.lower()

    relevant = []

    for project in projects:

        project_lower = project.lower()

        score = 0

        for term in [
            "python",
            "sql",
            "machine learning",
            "deep learning",
            "data",
            "analytics",
            "power bi",
            "tableau",
            "tensorflow",
            "pytorch",
            "nlp",
            "computer vision",
            "api",
            "cloud",
            "docker",
            "aws",
            "azure",
            "google cloud"
        ]:

            if term in job_lower and term in project_lower:
                score += 1

        relevant.append(
            (score, project)
        )

    relevant.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        project
        for score, project in relevant[:maximum]
    ]


def generate_cover_letter(
    candidate_name,
    job_title,
    company_name,
    hiring_manager,
    resume_text,
    job_description,
    tone,
    length
):
    """
    Generate a personalized cover letter using only
    information detected from the resume and JD.
    """

    candidate_name = clean_cover_letter_value(
        candidate_name
    )

    job_title = clean_cover_letter_value(
        job_title
    ) or "the position"

    company_name = clean_cover_letter_value(
        company_name
    )

    hiring_manager = clean_cover_letter_value(
        hiring_manager
    )

    matching_skills = select_cover_letter_skills(
        resume_text,
        job_description,
        maximum=6
    )

    job_data = analyze_ats_keywords(
        resume_text,
        job_description
    )

    projects = extract_section(
        resume_text,
        ["Projects", "Project"]
    )

    selected_projects = select_cover_letter_projects(
        resume_text,
        projects,
        job_description,
        maximum=2
    )

    education = extract_education_details(
        resume_text
    )

    experience = extract_section(
        resume_text,
        [
            "Experience",
            "Work Experience",
            "Internship",
            "Internships"
        ]
    )

    greeting = (
        f"Dear {hiring_manager},"
        if hiring_manager
        else "Dear Hiring Manager,"
    )

    if company_name:

        opening = (
            f"I am writing to express my interest in the "
            f"{job_title} position at {company_name}. "
            f"My academic background and practical experience "
            f"have prepared me to contribute effectively to this role."
        )

    else:

        opening = (
            f"I am writing to express my interest in the "
            f"{job_title} position. My academic background "
            f"and practical experience have prepared me to "
            f"contribute effectively to this opportunity."
        )

    if matching_skills:

        skill_text = ", ".join(
            matching_skills
        )

        skills_paragraph = (
            f"Through my academic and project experience, "
            f"I have developed practical knowledge of "
            f"{skill_text}. These skills align well with "
            f"the requirements described for this position, "
            f"and I am particularly interested in applying "
            f"them to real-world problems."
        )

    else:

        skills_paragraph = (
            "My academic and project experience has helped "
            "me build a strong technical foundation, analytical "
            "thinking and problem-solving ability. I am eager "
            "to apply these skills to the responsibilities of "
            "this position."
        )

    if selected_projects:

        project_names = []

        for project in selected_projects:

            project_clean = clean_cover_letter_value(
                project
            )

            if len(project_clean) > 180:

                project_clean = (
                    project_clean[:177]
                    + "..."
                )

            project_names.append(
                project_clean
            )

        projects_paragraph = (
            "My project experience includes "
            + "; ".join(project_names)
            + ". These projects strengthened my ability "
            "to translate technical concepts into practical "
            "solutions."
        )

    else:

        projects_paragraph = (
            "My academic work has given me opportunities "
            "to apply technical concepts through practical "
            "problem-solving and project-based learning."
        )

    if experience:

        experience_paragraph = (
            "I have also developed practical experience "
            "through the work and experience described in "
            "my resume, where I focused on applying technical "
            "knowledge and completing assigned objectives."
        )

    elif education:

        experience_paragraph = (
            "As a student, I have developed my technical "
            "foundation through coursework, projects and "
            "continuous learning. I am motivated to bring "
            "this learning mindset to a professional environment."
        )

    else:

        experience_paragraph = (
            "I am a motivated learner with a strong interest "
            "in developing practical solutions and growing "
            "through real-world professional experience."
        )

    if tone == "Professional":

        closing_paragraph = (
            "I would welcome the opportunity to discuss how "
            "my background and skills could contribute to "
            "your team. Thank you for considering my application."
        )

    elif tone == "Confident":

        closing_paragraph = (
            "I am confident that my technical foundation, "
            "project experience and willingness to learn would "
            "allow me to contribute positively to your team. "
            "Thank you for considering my application."
        )

    else:

        closing_paragraph = (
            "I would be grateful for the opportunity to discuss "
            "my background and learn more about the role. "
            "Thank you for your time and consideration."
        )

    if length == "Short":

        paragraphs = [
            opening,
            skills_paragraph,
            closing_paragraph
        ]

    elif length == "Long":

        missing = job_data["missing"][:4]

        keyword_sentence = ""

        if missing:

            keyword_sentence = (
                "I am also actively strengthening my knowledge "
                "in areas relevant to the role, including "
                + ", ".join(missing)
                + ", where appropriate."
            )

        paragraphs = [
            opening,
            skills_paragraph,
            projects_paragraph,
            experience_paragraph,
            keyword_sentence,
            closing_paragraph
        ]

        paragraphs = [
            paragraph
            for paragraph in paragraphs
            if paragraph.strip()
        ]

    else:

        paragraphs = [
            opening,
            skills_paragraph,
            projects_paragraph,
            experience_paragraph,
            closing_paragraph
        ]

    signature_name = (
        candidate_name
        if candidate_name
        else "Your Name"
    )

    letter = (
        greeting
        + "\n\n"
        + "\n\n".join(paragraphs)
        + "\n\nSincerely,\n"
        + signature_name
    )

    return letter, matching_skills, selected_projects


def create_cover_letter_pdf(
    cover_letter_text,
    candidate_name,
    job_title,
    company_name
):
    """Create a clean A4 PDF from the generated cover letter."""

    from io import BytesIO
    from xml.sax.saxutils import escape

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle
    )
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=55,
        leftMargin=55,
        topMargin=55,
        bottomMargin=55
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CoverLetterTitle",
        parent=styles["Title"],
        alignment=TA_LEFT,
        fontSize=16,
        spaceAfter=12
    )

    body_style = ParagraphStyle(
        "CoverLetterBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        spaceAfter=10
    )

    story = []

    title = "COVER LETTER"

    if job_title:

        title += (
            f" - {job_title}"
        )

    if company_name:

        title += (
            f" | {company_name}"
        )

    story.append(
        Paragraph(
            escape(title),
            title_style
        )
    )

    story.append(
        Spacer(1, 8)
    )

    paragraphs = cover_letter_text.split(
        "\n\n"
    )

    for paragraph in paragraphs:

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        safe_paragraph = escape(
            paragraph
        ).replace(
            "\n",
            "<br/>"
        )

        story.append(
            Paragraph(
                safe_paragraph,
                body_style
            )
        )

    document.build(
        story
    )

    buffer.seek(0)

    return buffer.getvalue()


# =========================================================
# STEP 13 UI - AI COVER LETTER GENERATOR
# =========================================================

st.divider()

st.header(
    "✉️ AI Cover Letter Generator"
)

st.write(
    "Generate a personalized cover letter using your "
    "uploaded resume and a specific job description."
)

if not uploaded_file:

    st.info(
        "📄 Upload your resume above before generating "
        "a cover letter."
    )

else:

    # -----------------------------------------------------
    # Candidate details
    # -----------------------------------------------------

    detected_name = (
        extract_candidate_name_from_resume(
            text
        )
    )

    detected_title = (
        extract_cover_letter_job_title(
            semantic_job_description
            if "semantic_job_description" in locals()
            else ""
        )
    )

    detected_company = (
        extract_cover_letter_company(
            semantic_job_description
            if "semantic_job_description" in locals()
            else ""
        )
    )

    cover_col1, cover_col2 = st.columns(2)

    with cover_col1:

        cover_candidate_name = st.text_input(
            "👤 Candidate Name",
            value=detected_name,
            key="cover_candidate_name"
        )

    with cover_col2:

        cover_job_title = st.text_input(
            "💼 Job Title",
            value=detected_title,
            key="cover_job_title"
        )

    cover_col3, cover_col4 = st.columns(2)

    with cover_col3:

        cover_company = st.text_input(
            "🏢 Company Name",
            value=detected_company,
            key="cover_company_name"
        )

    with cover_col4:

        cover_hiring_manager = st.text_input(
            "👔 Hiring Manager (optional)",
            placeholder="Hiring Manager",
            key="cover_hiring_manager"
        )

    cover_job_description = st.text_area(
        "🎯 Job Description",
        height=280,
        placeholder=(
            "Paste the complete job description here..."
        ),
        key="cover_letter_job_description"
    )

    cover_col5, cover_col6 = st.columns(2)

    with cover_col5:

        cover_tone = st.selectbox(
            "✍️ Tone",
            [
                "Professional",
                "Confident",
                "Friendly"
            ],
            key="cover_letter_tone"
        )

    with cover_col6:

        cover_length = st.selectbox(
            "📏 Length",
            [
                "Short",
                "Medium",
                "Long"
            ],
            index=1,
            key="cover_letter_length"
        )

    if st.button(
        "✉️ Generate Cover Letter",
        type="primary",
        key="generate_cover_letter"
    ):

        if not cover_job_description.strip():

            st.warning(
                "Please paste the job description first."
            )

        else:

            with st.spinner(
                "✉️ Generating personalized cover letter..."
            ):

                (
                    generated_cover_letter,
                    cover_matching_skills,
                    cover_projects
                ) = generate_cover_letter(
                    candidate_name=cover_candidate_name,
                    job_title=cover_job_title,
                    company_name=cover_company,
                    hiring_manager=cover_hiring_manager,
                    resume_text=text,
                    job_description=cover_job_description,
                    tone=cover_tone,
                    length=cover_length
                )

            st.success(
                "✅ Cover letter generated successfully!"
            )

            st.subheader(
                "📝 Generated Cover Letter"
            )

            st.text_area(
                "Review and edit before sending",
                generated_cover_letter,
                height=500,
                key="generated_cover_letter_text"
            )

            # -------------------------------------------------
            # Evidence used
            # -------------------------------------------------

            st.subheader(
                "🔎 Information Used"
            )

            if cover_matching_skills:

                st.write(
                    "**Matching skills:** "
                    + ", ".join(
                        cover_matching_skills
                    )
                )

            else:

                st.info(
                    "No supported job-specific skills were "
                    "detected in both the resume and job description."
                )

            if cover_projects:

                st.write(
                    "**Relevant resume projects:**"
                )

                for project in cover_projects:

                    st.write(
                        "• " + project
                    )

            # -------------------------------------------------
            # Download text
            # -------------------------------------------------

            st.download_button(
                "⬇️ Download Cover Letter (.txt)",
                data=generated_cover_letter,
                file_name="cover_letter.txt",
                mime="text/plain",
                key="download_cover_letter_txt"
            )

            # -------------------------------------------------
            # Generate PDF
            # -------------------------------------------------

            try:

                cover_pdf = create_cover_letter_pdf(
                    cover_letter_text=generated_cover_letter,
                    candidate_name=cover_candidate_name,
                    job_title=cover_job_title,
                    company_name=cover_company
                )

                st.download_button(
                    "📄 Download Cover Letter PDF",
                    data=cover_pdf,
                    file_name="cover_letter.pdf",
                    mime="application/pdf",
                    key="download_cover_letter_pdf"
                )

            except ImportError:

                st.warning(
                    "PDF generation requires ReportLab. "
                    "Run: pip install reportlab"
                )

            except Exception as error:

                st.error(
                    f"Unable to create cover letter PDF: {error}"
                )

            # -------------------------------------------------
            # Responsible-use notice
            # -------------------------------------------------

            st.caption(
                "⚠️ Review the generated letter before sending. "
                "Only keep claims that are true and supported by "
                "your resume or actual experience."
            )


# =========================================================
# STEP 14 - AI APPLICATION EMAIL GENERATOR
# =========================================================
#
# Creates a concise, personalized job-application email
# from the candidate's resume and a target job description.
#
# It reuses verified information from the resume and the
# job analysis. It does not invent experience or skills.
# =========================================================


def generate_application_email(
    candidate_name,
    job_title,
    company_name,
    hiring_manager,
    resume_text,
    job_description,
    tone,
    email_length,
    include_subject=True
):
    """
    Generate a professional application email.

    The email is grounded in:
      - resume information
      - matching job skills
      - selected resume projects
      - detected education/experience
    """

    candidate_name = clean_cover_letter_value(
        candidate_name
    )

    job_title = clean_cover_letter_value(
        job_title
    ) or "the position"

    company_name = clean_cover_letter_value(
        company_name
    )

    hiring_manager = clean_cover_letter_value(
        hiring_manager
    )

    matching_skills = select_cover_letter_skills(
        resume_text,
        job_description,
        maximum=5
    )

    projects = extract_section(
        resume_text,
        [
            "Projects",
            "Project"
        ]
    )

    selected_projects = select_cover_letter_projects(
        resume_text,
        projects,
        job_description,
        maximum=1
    )

    education = extract_education_details(
        resume_text
    )

    experience = extract_section(
        resume_text,
        [
            "Experience",
            "Work Experience",
            "Internship",
            "Internships"
        ]
    )

    email_data = analyze_ats_keywords(
        resume_text,
        job_description
    )

    # -----------------------------------------------------
    # Subject
    # -----------------------------------------------------

    subject = (
        f"Application for {job_title}"
    )

    if company_name:

        subject += (
            f" - {company_name}"
        )

    # -----------------------------------------------------
    # Greeting
    # -----------------------------------------------------

    if hiring_manager:

        greeting = (
            f"Dear {hiring_manager},"
        )

    else:

        greeting = (
            "Dear Hiring Manager,"
        )

    # -----------------------------------------------------
    # Opening
    # -----------------------------------------------------

    if company_name:

        opening = (
            f"I am writing to apply for the {job_title} "
            f"position at {company_name}."
        )

    else:

        opening = (
            f"I am writing to apply for the {job_title} "
            f"position."
        )

    # -----------------------------------------------------
    # Candidate background
    # -----------------------------------------------------

    if education:

        education_line = (
            "My academic background has given me a strong "
            "foundation in the technical and analytical skills "
            "relevant to this opportunity."
        )

    else:

        education_line = (
            "My background has helped me develop a practical "
            "technical foundation relevant to this opportunity."
        )

    # -----------------------------------------------------
    # Skills
    # -----------------------------------------------------

    if matching_skills:

        skills_line = (
            "My relevant skills include "
            + ", ".join(
                matching_skills
            )
            + "."
        )

    else:

        skills_line = (
            "I have developed relevant technical and "
            "problem-solving skills through my academic "
            "and practical work."
        )

    # -----------------------------------------------------
    # Project
    # -----------------------------------------------------

    if selected_projects:

        project = clean_cover_letter_value(
            selected_projects[0]
        )

        if len(project) > 220:

            project = (
                project[:217]
                + "..."
            )

        project_line = (
            "One relevant project from my resume is "
            + project
            + "."
        )

    else:

        project_line = (
            "My project-based work has helped me apply "
            "technical concepts to practical problems."
        )

    # -----------------------------------------------------
    # Experience
    # -----------------------------------------------------

    if experience:

        experience_line = (
            "My practical experience has also strengthened "
            "my ability to work on technical tasks, solve "
            "problems and deliver project objectives."
        )

    else:

        experience_line = (
            "I am particularly interested in gaining "
            "professional experience and contributing to "
            "real-world projects in this role."
        )

    # -----------------------------------------------------
    # Tone-specific closing
    # -----------------------------------------------------

    if tone == "Professional":

        closing = (
            "I would appreciate the opportunity to discuss "
            "how my background and skills could contribute "
            "to your team."
        )

    elif tone == "Confident":

        closing = (
            "I am confident that my technical foundation, "
            "project experience and willingness to learn "
            "would allow me to contribute positively to "
            "your team."
        )

    else:

        closing = (
            "I would be happy to discuss the role and how "
            "my background could be a good fit for your team."
        )

    # -----------------------------------------------------
    # Length control
    # -----------------------------------------------------

    if email_length == "Short":

        body_paragraphs = [
            opening,
            skills_line,
            closing
        ]

    elif email_length == "Detailed":

        body_paragraphs = [
            opening,
            education_line,
            skills_line,
            project_line,
            experience_line,
            closing
        ]

    else:

        body_paragraphs = [
            opening,
            education_line,
            skills_line,
            project_line,
            closing
        ]

    # Remove empty paragraphs.
    body_paragraphs = [
        paragraph
        for paragraph in body_paragraphs
        if paragraph.strip()
    ]

    signature_name = (
        candidate_name
        if candidate_name
        else "Your Name"
    )

    email_body = (
        greeting
        + "\n\n"
        + "\n\n".join(
            body_paragraphs
        )
        + "\n\nBest regards,\n"
        + signature_name
    )

    # -----------------------------------------------------
    # Full email
    # -----------------------------------------------------

    if include_subject:

        full_email = (
            "Subject: "
            + subject
            + "\n\n"
            + email_body
        )

    else:

        full_email = email_body

    return (
        full_email,
        subject,
        matching_skills,
        selected_projects,
        email_data
    )


def create_application_email_pdf(
    email_text,
    job_title,
    company_name
):
    """Create a simple PDF copy of the application email."""

    from io import BytesIO
    from xml.sax.saxutils import escape

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle
    )
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=55,
        leftMargin=55,
        topMargin=55,
        bottomMargin=55
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ApplicationEmailTitle",
        parent=styles["Title"],
        fontSize=16,
        spaceAfter=12
    )

    body_style = ParagraphStyle(
        "ApplicationEmailBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        spaceAfter=10
    )

    story = []

    title = "JOB APPLICATION EMAIL"

    if job_title:

        title += (
            f" - {job_title}"
        )

    if company_name:

        title += (
            f" | {company_name}"
        )

    story.append(
        Paragraph(
            escape(title),
            title_style
        )
    )

    story.append(
        Spacer(1, 8)
    )

    for paragraph in email_text.split(
        "\n\n"
    ):

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        safe_text = escape(
            paragraph
        ).replace(
            "\n",
            "<br/>"
        )

        story.append(
            Paragraph(
                safe_text,
                body_style
            )
        )

    document.build(
        story
    )

    buffer.seek(0)

    return buffer.getvalue()


# =========================================================
# STEP 14 UI - APPLICATION EMAIL GENERATOR
# =========================================================

st.divider()

st.header(
    "📧 AI Application Email Generator"
)

st.write(
    "Generate a professional, job-specific application "
    "email using your resume and the target job description."
)

if not uploaded_file:

    st.info(
        "📄 Upload your resume above before generating "
        "an application email."
    )

else:

    detected_email_name = (
        extract_candidate_name_from_resume(
            text
        )
    )

    email_job_description = st.text_area(
        "🎯 Job Description",
        height=280,
        placeholder=(
            "Paste the complete job description here..."
        ),
        key="application_email_job_description"
    )

    email_col1, email_col2 = st.columns(2)

    with email_col1:

        application_candidate_name = st.text_input(
            "👤 Candidate Name",
            value=detected_email_name,
            key="application_email_candidate_name"
        )

    with email_col2:

        application_job_title = st.text_input(
            "💼 Job Title",
            placeholder="Example: Data Analyst Intern",
            key="application_email_job_title"
        )

    email_col3, email_col4 = st.columns(2)

    with email_col3:

        application_company = st.text_input(
            "🏢 Company Name",
            placeholder="Example: ABC Technologies",
            key="application_email_company"
        )

    with email_col4:

        application_hiring_manager = st.text_input(
            "👔 Hiring Manager (optional)",
            placeholder="Hiring Manager",
            key="application_email_manager"
        )

    email_col5, email_col6 = st.columns(2)

    with email_col5:

        application_email_tone = st.selectbox(
            "✍️ Tone",
            [
                "Professional",
                "Confident",
                "Friendly"
            ],
            key="application_email_tone"
        )

    with email_col6:

        application_email_length = st.selectbox(
            "📏 Email Length",
            [
                "Short",
                "Medium",
                "Detailed"
            ],
            index=1,
            key="application_email_length"
        )

    include_subject = st.checkbox(
        "Include email subject",
        value=True,
        key="application_email_include_subject"
    )

    if st.button(
        "📧 Generate Application Email",
        type="primary",
        key="generate_application_email"
    ):

        if not email_job_description.strip():

            st.warning(
                "Please paste the job description first."
            )

        else:

            if not application_job_title.strip():

                application_job_title = (
                    extract_cover_letter_job_title(
                        email_job_description
                    )
                )

            if not application_company.strip():

                application_company = (
                    extract_cover_letter_company(
                        email_job_description
                    )
                )

            with st.spinner(
                "📧 Generating job-specific application email..."
            ):

                (
                    generated_application_email,
                    generated_email_subject,
                    email_matching_skills,
                    email_projects,
                    email_ats_data
                ) = generate_application_email(
                    candidate_name=application_candidate_name,
                    job_title=application_job_title,
                    company_name=application_company,
                    hiring_manager=application_hiring_manager,
                    resume_text=text,
                    job_description=email_job_description,
                    tone=application_email_tone,
                    email_length=application_email_length,
                    include_subject=include_subject
                )

            st.success(
                "✅ Application email generated successfully!"
            )

            st.subheader(
                "📝 Generated Application Email"
            )

            st.text_area(
                "Review and edit before sending",
                generated_application_email,
                height=450,
                key="generated_application_email_text"
            )

            # =================================================
            # EMAIL SUBJECT
            # =================================================

            st.subheader(
                "📌 Suggested Subject"
            )

            st.code(
                generated_email_subject,
                language=None
            )

            # =================================================
            # EVIDENCE USED
            # =================================================

            st.subheader(
                "🔎 Information Used"
            )

            if email_matching_skills:

                st.write(
                    "**Matching skills from your resume:** "
                    + ", ".join(
                        email_matching_skills
                    )
                )

            else:

                st.info(
                    "No supported job-specific skills were "
                    "detected in both the resume and job description."
                )

            if email_projects:

                st.write(
                    "**Relevant project information used:**"
                )

                for project in email_projects:

                    st.write(
                        "• " + project
                    )

            # =================================================
            # MISSING SKILLS
            # =================================================

            if email_ats_data["missing"]:

                with st.expander(
                    "❌ Missing Job Keywords"
                ):

                    st.write(
                        ", ".join(
                            email_ats_data["missing"]
                        )
                    )

                    st.caption(
                        "Missing keywords are shown for tailoring "
                        "guidance and are not claimed as skills in "
                        "the generated email."
                    )

            # =================================================
            # DOWNLOAD TXT
            # =================================================

            st.download_button(
                "⬇️ Download Application Email (.txt)",
                data=generated_application_email,
                file_name="job_application_email.txt",
                mime="text/plain",
                key="download_application_email_txt"
            )

            # =================================================
            # COPY-FRIENDLY EMAIL
            # =================================================

            st.subheader(
                "📋 Copy Email"
            )

            st.code(
                generated_application_email,
                language=None
            )

            # =================================================
            # PDF
            # =================================================

            try:

                application_email_pdf = (
                    create_application_email_pdf(
                        email_text=generated_application_email,
                        job_title=application_job_title,
                        company_name=application_company
                    )
                )

                st.download_button(
                    "📄 Download Application Email PDF",
                    data=application_email_pdf,
                    file_name="job_application_email.pdf",
                    mime="application/pdf",
                    key="download_application_email_pdf"
                )

            except ImportError:

                st.warning(
                    "PDF generation requires ReportLab. "
                    "Run: pip install reportlab"
                )

            except Exception as error:

                st.error(
                    f"Unable to create email PDF: {error}"
                )

            # =================================================
            # RESPONSIBLE USE
            # =================================================

            st.caption(
                "⚠️ Review the email before sending. Verify the "
                "company, job title, recipient and every claim. "
                "Do not send the same generic email to every employer."
            )


# =========================================================
# RESTORED FEATURE - AI RESUME TAILORING
# =========================================================
#
# This section restores the AI Resume Tailoring feature
# that was missing from the current Step 14 app.
#
# It uses:
#   - Uploaded resume text
#   - Target job description
#   - Existing ATS keyword analyzer
#   - Existing project/education extraction
#
# It does not invent skills or experience.
# =========================================================


def build_tailored_summary(
    resume_text,
    job_description
):
    """
    Build a job-specific professional summary using
    skills that are actually present in the resume.
    """

    ats_data = analyze_ats_keywords(
        resume_text,
        job_description
    )

    matching_skills = ats_data["matching"][:6]

    education_data = extract_education_details(
        resume_text
    )

    experience_data = extract_section(
        resume_text,
        [
            "Experience",
            "Work Experience",
            "Internship",
            "Internships"
        ]
    )

    if matching_skills:

        skill_text = ", ".join(
            matching_skills
        )

        summary = (
            "Motivated and detail-oriented professional "
            "with a strong foundation in "
            + skill_text
            + ". "
            "Experienced in applying technical and analytical "
            "knowledge through academic and practical projects. "
            "Strong problem-solving ability with an interest "
            "in applying these skills to real-world business "
            "and technical challenges."
        )

    else:

        summary = (
            "Motivated and detail-oriented professional with "
            "a strong technical foundation and a willingness "
            "to learn. Experienced in applying academic "
            "knowledge through practical projects and "
            "problem-solving activities. Seeking an opportunity "
            "to contribute to real-world projects while "
            "continuing to develop technical expertise."
        )

    if education_data:

        summary += (
            " Academic background includes "
            + ", ".join(
                education_data[:2]
            )
            + "."
        )

    if experience_data:

        summary += (
            " Practical experience is also reflected "
            "in the candidate's resume."
        )

    return summary


def get_tailoring_skill_recommendations(
    resume_text,
    job_description
):
    """
    Separate skills already present from missing skills.
    Missing skills are recommendations only and are never
    presented as skills the candidate already has.
    """

    ats_data = analyze_ats_keywords(
        resume_text,
        job_description
    )

    return (
        ats_data["matching"],
        ats_data["missing"]
    )


def get_tailoring_project_recommendations(
    resume_text,
    job_description
):
    """
    Recommend ways to tailor existing projects without
    inventing new project experience.
    """

    projects = extract_section(
        resume_text,
        [
            "Projects",
            "Project"
        ]
    )

    if not projects:

        return [
            "Add a relevant project only if you have "
            "actually completed one."
        ]

    job_lower = job_description.lower()

    recommendations = []

    for project in projects:

        project_lower = project.lower()

        matched_terms = []

        for term in [
            "python",
            "sql",
            "machine learning",
            "deep learning",
            "data analysis",
            "data analytics",
            "power bi",
            "tableau",
            "pandas",
            "numpy",
            "tensorflow",
            "pytorch",
            "nlp",
            "computer vision",
            "api",
            "docker",
            "aws",
            "azure",
            "google cloud",
            "gcp"
        ]:

            if (
                term in job_lower
                and
                term in project_lower
            ):

                matched_terms.append(
                    term
                )

        if matched_terms:

            project_name = project.strip()

            if len(project_name) > 140:

                project_name = (
                    project_name[:137]
                    + "..."
                )

            recommendations.append(
                f"Highlight {', '.join(matched_terms)} "
                f"in the project: {project_name}"
            )

    if not recommendations:

        recommendations.append(
            "Prioritize the existing project that is most "
            "closely related to the responsibilities in the job description."
        )

    return recommendations


def generate_tailoring_recommendations(
    resume_text,
    job_description,
    matching_skills,
    missing_skills
):
    """Generate practical, truthful tailoring recommendations."""

    recommendations = []

    if missing_skills:

        recommendations.append(
            "Add missing job keywords only when you genuinely "
            "have the related knowledge or experience."
        )

    if len(matching_skills) < 4:

        recommendations.append(
            "Strengthen the Skills section with relevant skills "
            "you actually know and can discuss in an interview."
        )

    if "summary" not in resume_text.lower():

        recommendations.append(
            "Add a concise professional summary tailored to "
            "the target role."
        )

    if "experience" not in resume_text.lower():

        recommendations.append(
            "If you have internships, freelance work or practical "
            "experience, include it with measurable outcomes."
        )

    if "project" not in resume_text.lower():

        recommendations.append(
            "Add relevant projects that demonstrate the skills "
            "required by the target role."
        )

    if not re.search(
        r"\b\d+(?:\.\d+)?\s*%",
        resume_text
    ):

        recommendations.append(
            "Where truthful, add measurable results such as "
            "accuracy, performance improvement, users, records "
            "processed or time saved."
        )

    recommendations.append(
        "Use the job description's terminology naturally in "
        "your Summary, Skills and Project sections."
    )

    recommendations.append(
        "Do not add a skill, certification, experience or "
        "achievement that you do not actually have."
    )

    return recommendations


def create_restored_tailored_resume_pdf(
    resume_text,
    tailored_summary,
    matching_skills,
    projects,
    certifications
):
    """
    Create an ATS-friendly tailored resume PDF using only
    information already present in the resume.
    """

    from io import BytesIO
    from xml.sax.saxutils import escape

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle
    )
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TailoredResumeTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=14
    )

    heading_style = ParagraphStyle(
        "TailoredResumeHeading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=9,
        spaceAfter=5
    )

    body_style = ParagraphStyle(
        "TailoredResumeBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        spaceAfter=4
    )

    story = []

    # -----------------------------------------------------
    # Name / title
    # -----------------------------------------------------

    candidate_name = (
        extract_candidate_name_from_resume(
            resume_text
        )
        if "extract_candidate_name_from_resume"
        in globals()
        else ""
    )

    if candidate_name:

        story.append(
            Paragraph(
                escape(candidate_name),
                title_style
            )
        )

    else:

        story.append(
            Paragraph(
                "TAILORED RESUME",
                title_style
            )
        )

    # -----------------------------------------------------
    # Contact
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "CONTACT INFORMATION",
            heading_style
        )
    )

    email = extract_email(
        resume_text
    )

    phone = extract_phone(
        resume_text
    )

    story.append(
        Paragraph(
            f"Email: {escape(str(email))}<br/>"
            f"Phone: {escape(str(phone))}",
            body_style
        )
    )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "PROFESSIONAL SUMMARY",
            heading_style
        )
    )

    story.append(
        Paragraph(
            escape(tailored_summary),
            body_style
        )
    )

    # -----------------------------------------------------
    # Skills
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "RELEVANT TECHNICAL SKILLS",
            heading_style
        )
    )

    if matching_skills:

        story.append(
            Paragraph(
                escape(
                    ", ".join(
                        matching_skills
                    )
                ),
                body_style
            )
        )

    else:

        story.append(
            Paragraph(
                "See original resume for technical skills.",
                body_style
            )
        )

    # -----------------------------------------------------
    # Education
    # -----------------------------------------------------

    education = extract_education_details(
        resume_text
    )

    story.append(
        Paragraph(
            "EDUCATION",
            heading_style
        )
    )

    if education:

        for item in education:

            story.append(
                Paragraph(
                    "• "
                    + escape(str(item)),
                    body_style
                )
            )

    else:

        story.append(
            Paragraph(
                "Education details available in original resume.",
                body_style
            )
        )

    # -----------------------------------------------------
    # Projects
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "PROJECTS",
            heading_style
        )
    )

    if projects:

        for project in projects:

            story.append(
                Paragraph(
                    "• "
                    + escape(str(project)),
                    body_style
                )
            )

    else:

        story.append(
            Paragraph(
                "Projects available in original resume.",
                body_style
            )
        )

    # -----------------------------------------------------
    # Certifications
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "CERTIFICATIONS",
            heading_style
        )
    )

    if certifications:

        for certification in certifications:

            story.append(
                Paragraph(
                    "• "
                    + escape(str(certification)),
                    body_style
                )
            )

    else:

        story.append(
            Paragraph(
                "Certifications available in original resume.",
                body_style
            )
        )

    document.build(
        story
    )

    buffer.seek(0)

    return buffer.getvalue()


# =========================================================
# RESTORED AI RESUME TAILORING UI
# =========================================================

st.divider()

st.header(
    "🤖 AI Resume Tailoring"
)

st.write(
    "Tailor your resume to a specific job description by "
    "identifying matching skills, missing keywords and "
    "job-specific improvements."
)

if not uploaded_file:

    st.info(
        "📄 Upload your resume above before using "
        "AI Resume Tailoring."
    )

else:

    tailoring_job_description_restored = st.text_area(
        "🎯 Target Job Description",
        height=300,
        placeholder=(
            "Paste the complete job description here..."
        ),
        key="restored_tailoring_job_description"
    )

    tailoring_col1, tailoring_col2 = st.columns(2)

    with tailoring_col1:

        tailoring_role = st.text_input(
            "💼 Target Job Title (optional)",
            placeholder="Example: Data Analyst Intern",
            key="restored_tailoring_role"
        )

    with tailoring_col2:

        tailoring_company = st.text_input(
            "🏢 Company (optional)",
            placeholder="Example: ABC Technologies",
            key="restored_tailoring_company"
        )

    if st.button(
        "🤖 Analyze & Tailor Resume",
        type="primary",
        key="restored_analyze_tailoring"
    ):

        if not tailoring_job_description_restored.strip():

            st.warning(
                "Please paste a job description first."
            )

        else:

            with st.spinner(
                "🤖 Analyzing your resume and tailoring it..."
            ):

                (
                    tailoring_matching,
                    tailoring_missing
                ) = get_tailoring_skill_recommendations(
                    text,
                    tailoring_job_description_restored
                )

                tailored_summary = build_tailored_summary(
                    text,
                    tailoring_job_description_restored
                )

                project_recommendations = (
                    get_tailoring_project_recommendations(
                        text,
                        tailoring_job_description_restored
                    )
                )

                tailoring_recommendations = (
                    generate_tailoring_recommendations(
                        text,
                        tailoring_job_description_restored,
                        tailoring_matching,
                        tailoring_missing
                    )
                )

                tailoring_ats_data = (
                    analyze_ats_keywords(
                        text,
                        tailoring_job_description_restored
                    )
                )

                if tailoring_ats_data["all"]:

                    tailoring_match_score = round(
                        len(tailoring_matching)
                        /
                        len(tailoring_ats_data["all"])
                        * 100
                    )

                else:

                    tailoring_match_score = 0

            st.success(
                "✅ Resume tailoring analysis completed!"
            )

            # =================================================
            # MATCH SCORE
            # =================================================

            st.subheader(
                "🎯 Job Match"
            )

            st.metric(
                "Keyword Match",
                f"{tailoring_match_score}%"
            )

            st.progress(
                tailoring_match_score / 100
            )

            # =================================================
            # TAILORED SUMMARY
            # =================================================

            st.subheader(
                "✨ Tailored Professional Summary"
            )

            st.text_area(
                "Review and edit your summary",
                tailored_summary,
                height=200,
                key="restored_tailored_summary"
            )

            # =================================================
            # MATCHING SKILLS
            # =================================================

            st.subheader(
                "✅ Matching Skills"
            )

            if tailoring_matching:

                st.success(
                    ", ".join(
                        tailoring_matching
                    )
                )

            else:

                st.info(
                    "No supported matching skills detected."
                )

            # =================================================
            # MISSING SKILLS
            # =================================================

            st.subheader(
                "❌ Missing Job Keywords"
            )

            if tailoring_missing:

                for skill in tailoring_missing:

                    st.warning(
                        "➕ " + skill
                    )

                st.caption(
                    "Only add these skills if you genuinely "
                    "have the required knowledge or experience."
                )

            else:

                st.success(
                    "No detected job keywords are missing."
                )

            # =================================================
            # PROJECT RECOMMENDATIONS
            # =================================================

            st.subheader(
                "📁 Project Tailoring Recommendations"
            )

            for recommendation in (
                project_recommendations
            ):

                st.info(
                    "📌 " + recommendation
                )

            # =================================================
            # IMPROVEMENTS
            # =================================================

            st.subheader(
                "💡 Resume Improvements"
            )

            for number, recommendation in enumerate(
                tailoring_recommendations,
                start=1
            ):

                st.write(
                    f"**{number}.** {recommendation}"
                )

            # =================================================
            # PDF GENERATION
            # =================================================

            st.subheader(
                "📄 Generate Tailored Resume PDF"
            )

            st.write(
                "Generate an ATS-friendly PDF containing "
                "your verified resume information and the "
                "tailored summary."
            )

            tailoring_projects_for_pdf = extract_section(
                text,
                [
                    "Projects",
                    "Project"
                ]
            )

            tailoring_certifications_for_pdf = extract_section(
                text,
                [
                    "Certifications",
                    "Certificates"
                ]
            )

            try:

                tailored_pdf = (
                    create_restored_tailored_resume_pdf(
                        resume_text=text,
                        tailored_summary=tailored_summary,
                        matching_skills=tailoring_matching,
                        projects=tailoring_projects_for_pdf,
                        certifications=(
                            tailoring_certifications_for_pdf
                        )
                    )
                )

                st.download_button(
                    "⬇️ Download Tailored Resume PDF",
                    data=tailored_pdf,
                    file_name="tailored_resume.pdf",
                    mime="application/pdf",
                    key="restored_download_tailored_pdf"
                )

            except ImportError:

                st.warning(
                    "PDF generation requires ReportLab. "
                    "Run: pip install reportlab"
                )

            except Exception as error:

                st.error(
                    f"Unable to generate tailored PDF: {error}"
                )

            # =================================================
            # TAILORING REPORT
            # =================================================

            tailoring_report = []

            tailoring_report.append(
                "AI RESUME TAILORING REPORT"
            )

            tailoring_report.append(
                "=" * 45
            )

            tailoring_report.append(
                f"Keyword Match: {tailoring_match_score}%"
            )

            tailoring_report.append("")

            tailoring_report.append(
                "MATCHING SKILLS:"
            )

            tailoring_report.extend(
                [
                    f"- {skill}"
                    for skill in tailoring_matching
                ]
                or ["- None"]
            )

            tailoring_report.append("")

            tailoring_report.append(
                "MISSING KEYWORDS:"
            )

            tailoring_report.extend(
                [
                    f"- {skill}"
                    for skill in tailoring_missing
                ]
                or ["- None"]
            )

            tailoring_report.append("")

            tailoring_report.append(
                "TAILORED SUMMARY:"
            )

            tailoring_report.append(
                tailored_summary
            )

            tailoring_report.append("")

            tailoring_report.append(
                "PROJECT RECOMMENDATIONS:"
            )

            tailoring_report.extend(
                [
                    f"- {item}"
                    for item in project_recommendations
                ]
            )

            tailoring_report.append("")

            tailoring_report.append(
                "RESUME IMPROVEMENTS:"
            )

            tailoring_report.extend(
                [
                    f"- {item}"
                    for item in tailoring_recommendations
                ]
            )

            tailoring_report_text = "\n".join(
                tailoring_report
            )

            st.download_button(
                "⬇️ Download Tailoring Report",
                data=tailoring_report_text,
                file_name="ai_resume_tailoring_report.txt",
                mime="text/plain",
                key="restored_download_tailoring_report"
            )

            st.caption(
                "⚠️ Review the tailored resume before applying. "
                "Only keep information that is true and supported "
                "by your actual experience."
            )

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
    title_score = calculate_title_relevance_score(
        resume_text, job_description
    )

    semantic_score = None
    try:
        semantic_score = calculate_semantic_similarity(
            resume_text, job_description
        )
    except Exception:
        pass

    if semantic_score is not None:
        final_score = calculate_combined_semantic_score(
            semantic_score, keyword_score, title_score
        )
    else:
        final_score = round(
            keyword_score * 0.75 + title_score * 0.25
        )

    summary = build_tailored_summary(
        resume_text, job_description
    )

    matching, missing = get_tailoring_skill_recommendations(
        resume_text, job_description
    )

    projects = extract_section(
        resume_text, ["Projects", "Project"]
    )

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


def step16_package_text(application, package):
    lines = [
        "SEMI-AUTOMATIC JOB APPLICATION PACKAGE",
        "=" * 55,
        f"Job: {application.get('title', '')}",
        f"Company: {application.get('company', '')}",
        f"Location: {application.get('location', '')}",
        f"Match Score: {package.get('final_score', 0)}%",
        "",
        "MATCHING SKILLS",
        "-" * 30,
    ]
    lines += [f"- {x}" for x in package["matching"]] or ["- None"]
    lines += ["", "MISSING KEYWORDS", "-" * 30]
    lines += [f"- {x}" for x in package["missing"]] or ["- None"]
    lines += ["", "TAILORED SUMMARY", "-" * 30, package["summary"]]
    lines += ["", "COVER LETTER", "-" * 30, package["cover_letter"]]
    lines += ["", "APPLICATION EMAIL", "-" * 30, package["email"]]
    return "\n".join(lines)


# =========================================================
# STEP 16 UI
# =========================================================

st.divider()
st.header("🚀 Semi-Automatic Job Application Assistant")
st.write(
    "Select a saved job and prepare the complete application "
    "package before submitting it yourself."
)
st.info(
    "🛡️ The assistant prepares documents and opens the application "
    "page. It does not automatically submit forms, bypass CAPTCHAs, "
    "or bypass employer login/security."
)

step16_apps = load_applications()

if not step16_apps:
    st.warning(
        "No saved jobs found. Save a job in the Application Tracker first."
    )
else:
    labels = [
        f"{i + 1}. {a.get('title', 'Unknown Job')} — "
        f"{a.get('company', 'Unknown Company')}"
        for i, a in enumerate(step16_apps)
    ]

    selected_label = st.selectbox(
        "💼 Select Saved Job",
        labels,
        key="step16_job_select"
    )
    selected_index = labels.index(selected_label)
    selected_job = step16_get_job(selected_index)

    st.subheader("📌 Selected Job")
    c1, c2, c3 = st.columns(3)
    c1.write(f"**💼 Job:** {selected_job.get('title', '')}")
    c2.write(f"**🏢 Company:** {selected_job.get('company', '')}")
    c3.write(f"**🎯 Saved Match:** {selected_job.get('score', 0)}%")

    job_description = st.text_area(
        "🎯 Job Description",
        value=selected_job.get("job_description", ""),
        height=280,
        placeholder="Paste the job description if it was not saved.",
        key="step16_job_description"
    )

    candidate_name = st.text_input(
        "👤 Candidate Name",
        value=(
            extract_candidate_name_from_resume(text)
            if "extract_candidate_name_from_resume" in globals()
            else ""
        ),
        key="step16_candidate_name"
    )

    hiring_manager = st.text_input(
        "👔 Hiring Manager (optional)",
        value=selected_job.get("contact_name", ""),
        key="step16_hiring_manager"
    )

    tone = st.selectbox(
        "✍️ Tone",
        ["Professional", "Confident", "Friendly"],
        key="step16_tone"
    )

    st.subheader("✅ Application Readiness Checklist")
    checklist = step16_checklist(
        selected_job, job_description, text
    )
    completed = sum(done for _, done in checklist)

    for label, done in checklist:
        if done:
            st.success("✅ " + label)
        else:
            st.warning("⚠️ " + label)

    readiness = round(completed / len(checklist) * 100)
    st.progress(readiness / 100)
    st.write(f"**Readiness: {readiness}%**")

    if st.button(
        "🚀 Prepare Complete Application Package",
        type="primary",
        key="step16_prepare"
    ):
        if not job_description.strip():
            st.warning("Please add the job description first.")
        else:
            with st.spinner(
                "🚀 Preparing ATS analysis, tailored resume content, "
                "cover letter and application email..."
            ):
                package = step16_prepare_package(
                    text, job_description, selected_job,
                    candidate_name, hiring_manager, tone
                )

            st.session_state["step16_package"] = package
            st.success("✅ Complete application package prepared!")

            try:
                apps = load_applications()
                if 0 <= selected_index < len(apps):
                    apps[selected_index]["job_description"] = job_description
                    apps[selected_index]["last_updated"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    save_applications(apps)
            except Exception:
                pass

    package = st.session_state.get("step16_package")

    if package:
        st.divider()
        st.subheader("🎯 Application Match Analysis")

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("🎯 Final Match", f"{package['final_score']}%")
        s2.metric(
            "🧠 Semantic",
            f"{package['semantic_score'] or 0}%"
        )
        s3.metric("🔑 Keywords", f"{package['keyword_score']}%")
        s4.metric("💼 Title", f"{package['title_score']}%")

        st.progress(package["final_score"] / 100)

        st.subheader("🤖 Tailored Resume Summary")
        st.text_area(
            "Review and edit",
            package["summary"],
            height=180,
            key="step16_summary"
        )

        a, b = st.columns(2)
        with a:
            st.subheader("✅ Matching Skills")
            st.success(
                ", ".join(package["matching"])
                if package["matching"]
                else "None detected"
            )
        with b:
            st.subheader("❌ Missing Keywords")
            if package["missing"]:
                st.warning(", ".join(package["missing"]))
                st.caption(
                    "Only add a missing skill if you genuinely have it."
                )
            else:
                st.success("No detected missing keywords.")

        st.subheader("📁 Relevant Projects")
        for project in package["projects"]:
            st.write("• " + project)
        if not package["projects"]:
            st.info("No project section detected.")

        st.subheader("✉️ Cover Letter")
        st.text_area(
            "Review and edit",
            package["cover_letter"],
            height=400,
            key="step16_cover"
        )

        st.subheader("📧 Application Email")
        st.code(package["subject"], language=None)
        st.text_area(
            "Review and edit",
            package["email"],
            height=350,
            key="step16_email"
        )

        st.download_button(
            "⬇️ Download Complete Application Package",
            data=step16_package_text(selected_job, package),
            file_name="application_package.txt",
            mime="text/plain",
            key="step16_download"
        )

        st.subheader("🚀 Final Application Step")
        url = selected_job.get("application_url", "")

        if url:
            st.link_button(
                "🔗 Open Job Application Page",
                url
            )
            st.caption(
                "Review the employer form, attachments and answers "
                "before submitting."
            )
        else:
            st.warning(
                "No application URL is saved for this job."
            )

        st.subheader("📤 Application Tracking")
        st.write(
            "Only click this after you have actually submitted "
            "the application on the employer's site."
        )

        if st.button(
            "✅ Mark as Applied",
            key="step16_mark_applied"
        ):
            if update_application_status(
                selected_index, "Applied"
            ):
                st.success("Application marked as Applied.")
                st.rerun()
            else:
                st.error("Unable to update application status.")

        st.info(
            "💡 After applying, set a follow-up date in Step 15."
        )
        st.caption(
            "⚠️ Verify every generated claim and document before sending."
        )

# =========================================================
# STEP 17 - APPLICATION ANALYTICS DASHBOARD
# =========================================================
#
# Analyze application history from applications.json.
#
# Features:
#   - KPI dashboard
#   - Application funnel
#   - Status distribution
#   - Priority distribution
#   - Match-score analysis
#   - Application source analysis
#   - Company analysis
#   - Monthly application trend
#   - Interview / offer / selection rates
#   - Follow-up performance
#   - Actionable recommendations
#   - CSV export
#
# Uses only data already stored by the application tracker.
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
        "Saved": 0,
        "Applied": 0,
        "Assessment": 0,
        "Interview": 0,
        "Offer": 0,
        "Selected": 0,
        "Rejected": 0,
        "Withdrawn": 0
    }

    priority_counts = {
        "Low": 0,
        "Medium": 0,
        "High": 0
    }

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

        month = step17_month(
            item.get("applied_date", "")
        )
        if month:
            monthly_counts[month] = monthly_counts.get(month, 0) + 1

    applied = status_counts["Applied"]
    assessment = status_counts["Assessment"]
    interview = status_counts["Interview"]
    offers = status_counts["Offer"]
    selected = status_counts["Selected"]
    rejected = status_counts["Rejected"]

    submitted = (
        applied
        + assessment
        + interview
        + offers
        + selected
        + rejected
    )

    response_count = (
        assessment
        + interview
        + offers
        + selected
        + rejected
    )

    positive_outcomes = (
        interview
        + offers
        + selected
    )

    average_score = (
        round(sum(scores) / len(scores), 1)
        if scores else 0
    )

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
        "response_rate": step17_rate(
            response_count,
            submitted
        ),
        "interview_rate": step17_rate(
            interview,
            submitted
        ),
        "offer_rate": step17_rate(
            offers + selected,
            submitted
        ),
        "selection_rate": step17_rate(
            selected,
            submitted
        ),
        "rejection_rate": step17_rate(
            rejected,
            submitted
        ),
        "positive_rate": step17_rate(
            positive_outcomes,
            submitted
        )
    }


def step17_recommendations(data):
    recommendations = []

    if data["total"] == 0:
        return [
            "Add applications to the tracker to generate analytics."
        ]

    if data["average_score"] < 60:
        recommendations.append(
            "Your average resume/job match is below 60%. "
            "Use AI Resume Tailoring before applying."
        )
    elif data["average_score"] < 75:
        recommendations.append(
            "Your average match is moderate. Tailor your resume "
            "more closely to each job description."
        )
    else:
        recommendations.append(
            "Your average match score is strong. Continue tailoring "
            "each application rather than using one generic resume."
        )

    if data["submitted"] == 0:
        recommendations.append(
            "No submitted applications are recorded yet. "
            "Mark applications as Applied after you submit them."
        )
    elif data["interview_rate"] < 10:
        recommendations.append(
            "Your interview conversion is low. Review your resume, "
            "project evidence, keywords and application targeting."
        )
    else:
        recommendations.append(
            "Your interview conversion shows that your targeting "
            "is generating relevant opportunities."
        )

    if data["rejection_rate"] >= 50:
        recommendations.append(
            "A high rejection rate is visible. Check role fit, "
            "required skills and resume tailoring before applying."
        )

    if data["priority_counts"].get("High", 0) == 0:
        recommendations.append(
            "Consider marking your most important opportunities "
            "as High priority for easier follow-up."
        )

    if not data["source_counts"]:
        recommendations.append(
            "Record the source of each job to compare which job "
            "platforms produce better results."
        )

    return recommendations


def step17_export_csv(applications):
    import csv
    from io import StringIO

    output = StringIO()

    fields = [
        "title",
        "company",
        "location",
        "score",
        "status",
        "priority",
        "applied_date",
        "follow_up_date",
        "contact_name",
        "contact_email",
        "salary",
        "source",
        "notes",
        "application_url",
        "last_updated"
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fields
    )

    writer.writeheader()

    for item in applications:
        writer.writerow({
            field: item.get(
                field,
                ""
            )
            for field in fields
        })

    return output.getvalue()


# =========================================================
# STEP 17 UI
# =========================================================

st.divider()

st.header(
    "📊 Application Analytics Dashboard"
)

st.write(
    "Analyze your application activity, match scores, "
    "conversion rates, sources and outcomes."
)

step17_apps = load_applications()

if not step17_apps:

    st.info(
        "📋 No application data is available yet. "
        "Add jobs in the Application Tracker to see analytics."
    )

else:

    step17_data = step17_analytics(
        step17_apps
    )

    # =====================================================
    # KPI CARDS
    # =====================================================

    st.subheader(
        "📈 Key Performance Indicators"
    )

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric(
        "📋 Total Jobs",
        step17_data["total"]
    )

    k2.metric(
        "📤 Submitted",
        step17_data["submitted"]
    )

    k3.metric(
        "🎯 Avg Match",
        f"{step17_data['average_score']}%"
    )

    k4.metric(
        "🎤 Interview Rate",
        f"{step17_data['interview_rate']}%"
    )

    k5.metric(
        "🎉 Offer Rate",
        f"{step17_data['offer_rate']}%"
    )

    # =====================================================
    # CONVERSION METRICS
    # =====================================================

    st.subheader(
        "🔄 Application Conversion"
    )

    r1, r2, r3, r4 = st.columns(4)

    r1.metric(
        "📨 Response Rate",
        f"{step17_data['response_rate']}%"
    )

    r2.metric(
        "🎤 Interview Rate",
        f"{step17_data['interview_rate']}%"
    )

    r3.metric(
        "💼 Offer Rate",
        f"{step17_data['offer_rate']}%"
    )

    r4.metric(
        "❌ Rejection Rate",
        f"{step17_data['rejection_rate']}%"
    )

    st.progress(
        min(
            step17_data["positive_rate"] / 100,
            1.0
        )
    )

    st.caption(
        f"Positive outcome rate: "
        f"{step17_data['positive_rate']}%"
    )

    # =====================================================
    # STATUS DISTRIBUTION
    # =====================================================

    st.subheader(
        "📊 Application Status Distribution"
    )

    status_data = step17_data[
        "status_counts"
    ]

    status_rows = []

    for status, count in status_data.items():

        status_rows.append({
            "Status": status,
            "Applications": count,
            "Percentage": (
                step17_rate(
                    count,
                    step17_data["total"]
                )
            )
        })

    st.dataframe(
        status_rows,
        use_container_width=True,
        hide_index=True
    )

    # =====================================================
    # VISUAL STATUS BAR CHART
    # =====================================================

    try:

        import pandas as pd

        status_df = pd.DataFrame(
            status_rows
        )

        st.bar_chart(
            status_df.set_index(
                "Status"
            )["Applications"]
        )

    except Exception:

        pass

    # =====================================================
    # MATCH SCORE ANALYSIS
    # =====================================================

    st.subheader(
        "🎯 Match Score Analysis"
    )

    match_col1, match_col2, match_col3 = st.columns(3)

    high_matches = 0
    medium_matches = 0
    low_matches = 0

    for item in step17_apps:

        score = step17_safe_score(
            item.get("score", 0)
        )

        if score >= 80:

            high_matches += 1

        elif score >= 60:

            medium_matches += 1

        else:

            low_matches += 1

    match_col1.metric(
        "🟢 Strong (80–100)",
        high_matches
    )

    match_col2.metric(
        "🟡 Moderate (60–79)",
        medium_matches
    )

    match_col3.metric(
        "🔴 Low (<60)",
        low_matches
    )

    match_distribution = [
        {
            "Match Range": "80–100",
            "Applications": high_matches
        },
        {
            "Match Range": "60–79",
            "Applications": medium_matches
        },
        {
            "Match Range": "0–59",
            "Applications": low_matches
        }
    ]

    st.dataframe(
        match_distribution,
        use_container_width=True,
        hide_index=True
    )

    # =====================================================
    # SOURCE ANALYSIS
    # =====================================================

    st.subheader(
        "🌐 Job Source Analysis"
    )

    source_rows = [
        {
            "Source": source,
            "Applications": count
        }
        for source, count in sorted(
            step17_data["source_counts"].items(),
            key=lambda x: x[1],
            reverse=True
        )
    ]

    if source_rows:

        st.dataframe(
            source_rows,
            use_container_width=True,
            hide_index=True
        )

        try:

            source_df = pd.DataFrame(
                source_rows
            )

            st.bar_chart(
                source_df.set_index(
                    "Source"
                )["Applications"]
            )

        except Exception:

            pass

    else:

        st.info(
            "Add a source such as LinkedIn, company website "
            "or job portal when saving applications."
        )

    # =====================================================
    # COMPANY ANALYSIS
    # =====================================================

    st.subheader(
        "🏢 Company Analysis"
    )

    company_rows = [
        {
            "Company": company,
            "Applications": count
        }
        for company, count in sorted(
            step17_data["company_counts"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:15]
    ]

    st.dataframe(
        company_rows,
        use_container_width=True,
        hide_index=True
    )

    # =====================================================
    # MONTHLY TREND
    # =====================================================

    st.subheader(
        "📅 Monthly Application Trend"
    )

    monthly_rows = [
        {
            "Month": month,
            "Applications": count
        }
        for month, count in sorted(
            step17_data["monthly_counts"].items()
        )
    ]

    if monthly_rows:

        st.dataframe(
            monthly_rows,
            use_container_width=True,
            hide_index=True
        )

        try:

            monthly_df = pd.DataFrame(
                monthly_rows
            )

            st.line_chart(
                monthly_df.set_index(
                    "Month"
                )["Applications"]
            )

        except Exception:

            pass

    else:

        st.info(
            "Monthly trends appear after applications have "
            "an Applied Date."
        )

    # =====================================================
    # PRIORITY ANALYSIS
    # =====================================================

    st.subheader(
        "🚨 Priority Distribution"
    )

    priority_rows = [
        {
            "Priority": priority,
            "Applications": count
        }
        for priority, count in (
            step17_data["priority_counts"].items()
        )
    ]

    st.dataframe(
        priority_rows,
        use_container_width=True,
        hide_index=True
    )

    # =====================================================
    # RECOMMENDATIONS
    # =====================================================

    st.subheader(
        "💡 AI-Assisted Recommendations"
    )

    recommendations = step17_recommendations(
        step17_data
    )

    for recommendation in recommendations:

        st.info(
            "💡 " + recommendation
        )

    # =====================================================
    # RECENT APPLICATIONS
    # =====================================================

    st.subheader(
        "🕒 Recent Applications"
    )

    recent_apps = sorted(
        step17_apps,
        key=lambda item: str(
            item.get(
                "last_updated",
                ""
            )
        ),
        reverse=True
    )[:10]

    recent_rows = []

    for item in recent_apps:

        recent_rows.append({
            "Job": item.get(
                "title",
                ""
            ),
            "Company": item.get(
                "company",
                ""
            ),
            "Match": f"{step17_safe_score(item.get('score', 0)):.0f}%",
            "Status": item.get(
                "status",
                "Saved"
            ),
            "Priority": item.get(
                "priority",
                "Medium"
            ),
            "Updated": item.get(
                "last_updated",
                ""
            )
        })

    st.dataframe(
        recent_rows,
        use_container_width=True,
        hide_index=True
    )

    # =====================================================
    # EXPORT
    # =====================================================

    st.subheader(
        "📤 Export Analytics Data"
    )

    analytics_csv = step17_export_csv(
        step17_apps
    )

    st.download_button(
        "⬇️ Download Application Data CSV",
        data=analytics_csv,
        file_name="application_analytics_data.csv",
        mime="text/csv",
        key="step17_export_csv"
    )

    # =====================================================
    # DATA QUALITY NOTICE
    # =====================================================

    st.caption(
        "ℹ️ Analytics are calculated from the information "
        "stored in your Application Tracker. For accurate "
        "conversion rates, update the application status "
        "after each real-world outcome."
    )
