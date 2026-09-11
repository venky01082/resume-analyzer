"""
AI Job Application Assistant
Main Application Entrypoint & Modular SaaS Dashboard Router
"""

import streamlit as st

# 1. Page Configuration MUST be the first Streamlit command
st.set_page_config(
    page_title="AI Job Application Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Apply Custom AI SaaS Styling
from ui.styles import apply_custom_styles
apply_custom_styles()

# 3. Core Business Logic & Authentication Imports
from core_logic import (
    auth_login,
    auth_create_user,
    migrate_application_file,
)

# 4. Initialize Database Files & Migration
migrate_application_file()

# 5. Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "auth_username" not in st.session_state:
    st.session_state.auth_username = ""

if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "resume_skills" not in st.session_state:
    st.session_state.resume_skills = []

if "resume_score" not in st.session_state:
    st.session_state.resume_score = 0


# =========================================================
# LOGIN / REGISTRATION SCREEN (IF UNAUTHENTICATED)
# =========================================================
if not st.session_state.authenticated:
    st.markdown("""
    <div style="max-width: 520px; margin: 40px auto 20px auto; text-align: center;">
        <div style="font-size: 42px; margin-bottom: 8px;">🤖</div>
        <h1 style="font-size: 26px; font-weight: 800; color: #0f172a; margin-bottom: 6px;">AI Job Application Assistant</h1>
        <p style="font-size: 14px; color: #64748b; margin-bottom: 24px;">Your AI-powered copilot for resumes, ATS scoring, and tracking applications.</p>
    </div>
    """, unsafe_allow_html=True)

    center_col1, center_col2, center_col3 = st.columns([1, 2, 1])

    with center_col2:
        st.markdown('<div class="saas-card" style="padding: 2rem;">', unsafe_allow_html=True)
        login_tab, reg_tab = st.tabs(["🔑 Sign In", "📝 Create Account"])

        # Tab 1: Sign In
        with login_tab:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            login_user = st.text_input("Username", key="auth_login_username", placeholder="Enter your username")
            login_pass = st.text_input("Password", type="password", key="auth_login_password", placeholder="Enter your password")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("🔑 Sign In to Workspace", type="primary", use_container_width=True, key="btn_login_submit"):
                if not login_user.strip() or not login_pass:
                    st.warning("Please enter both username and password.")
                elif auth_login(login_user, login_pass):
                    st.session_state.authenticated = True
                    st.session_state.auth_username = login_user.strip().lower()
                    st.success("✅ Login successful! Loading dashboard...")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")

        # Tab 2: Create Account
        with reg_tab:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            reg_user = st.text_input("Choose Username", key="auth_reg_username", placeholder="Min 3 characters")
            reg_pass = st.text_input("Create Password", type="password", key="auth_reg_password", placeholder="Min 6 characters")
            reg_conf = st.text_input("Confirm Password", type="password", key="auth_reg_confirm", placeholder="Repeat password")
            reg_name = st.text_input("Full Name", key="auth_reg_fullname", placeholder="e.g. Alex Johnson")
            reg_email = st.text_input("Email Address", key="auth_reg_email", placeholder="alex@example.com")
            reg_roles = st.text_input("Preferred Roles", key="auth_reg_roles", placeholder="e.g. Data Analyst, ML Intern")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("📝 Register Account", type="primary", use_container_width=True, key="btn_reg_submit"):
                if reg_pass != reg_conf:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = auth_create_user(
                        username=reg_user,
                        password=reg_pass,
                        full_name=reg_name,
                        email=reg_email,
                        target_roles=reg_roles
                    )
                    if ok:
                        st.session_state.authenticated = True
                        st.session_state.auth_username = reg_user.strip().lower()
                        st.success("✅ Account created successfully! Launching workspace...")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()


# =========================================================
# AUTHENTICATED APPLICATION SHELL & ROUTER
# =========================================================

# Render Sidebar Navigation
from ui.sidebar import render_sidebar
current_page = render_sidebar()

# Route to Selected Dashboard View
if current_page == "dashboard":
    from ui.dashboard_ui import render_dashboard
    render_dashboard()

elif current_page == "resume_analyzer":
    from ui.resume_ui import render_resume_analyzer
    render_resume_analyzer()

elif current_page == "ats_analyzer":
    from ui.ats_ui import render_ats_analyzer
    render_ats_analyzer()

elif current_page == "my_resumes":
    from ui.my_resumes_ui import render_my_resumes
    render_my_resumes()

elif current_page == "job_search":
    from ui.jobs_ui import render_job_search
    render_job_search()

elif current_page == "saved_jobs":
    from ui.saved_jobs_ui import render_saved_jobs
    render_saved_jobs()

elif current_page == "job_matching":
    from ui.matching_ui import render_job_matching
    render_job_matching()

elif current_page == "resume_tailoring":
    from ui.tailoring_ui import render_resume_tailoring
    render_resume_tailoring()

elif current_page == "cover_letter":
    from ui.cover_letter_ui import render_cover_letter
    render_cover_letter()

elif current_page == "application_email":
    from ui.email_ui import render_application_email
    render_application_email()

elif current_page == "mock_interview":
    from ui.interview_ui import render_mock_interview
    render_mock_interview()

elif current_page == "application_tracker":
    from ui.tracker_ui import render_application_tracker
    render_application_tracker()

elif current_page == "followups":
    from ui.followup_ui import render_followups
    render_followups()

elif current_page == "analytics":
    from ui.analytics_ui import render_analytics
    render_analytics()

elif current_page == "application_assistant":
    from ui.assistant_ui import render_application_assistant
    render_application_assistant()

elif current_page == "profile":
    from ui.profile_ui import render_profile
    render_profile()

elif current_page == "settings":
    from ui.settings_ui import render_settings
    render_settings()

else:
    from ui.dashboard_ui import render_dashboard
    render_dashboard()

