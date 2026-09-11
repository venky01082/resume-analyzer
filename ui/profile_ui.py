import streamlit as st
from database.repository import (
    get_user_profile,
    update_user_profile,
    get_user_preferences,
    update_user_preferences,
)
from database.models import WORK_MODE_OPTIONS


def render_profile():
    """
    Renders comprehensive candidate profile and career preferences workspace.
    Supports all 18 professional attributes, database persistence, and profile strength scoring.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">👤</div>
            <div>
                <h1 class="app-title">Candidate Profile & Career Preferences</h1>
                <p class="app-subtitle">Manage your personal details, qualifications, and preferences that power AI job matching & recommendations.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    username = st.session_state.get("auth_username", "")
    if not username:
        st.warning("Please log in to manage your profile.")
        return

    profile = get_user_profile(username)
    preferences = get_user_preferences(username)

    # 1. Profile Completeness Evaluation
    audit_fields = [
        profile.get("full_name"),
        profile.get("email"),
        profile.get("professional_title"),
        profile.get("target_roles"),
        profile.get("location"),
        profile.get("technical_skills") or profile.get("skills"),
        profile.get("education"),
        profile.get("experience"),
        profile.get("linkedin"),
        profile.get("certifications"),
        profile.get("work_authorization"),
    ]
    completed_count = sum(1 for f in audit_fields if bool(str(f or "").strip()))
    pct = round(completed_count / len(audit_fields) * 100)

    col_gauge, col_info = st.columns([1, 3])
    with col_gauge:
        st.markdown(f"""
        <div class="saas-card" style="text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase;">Profile Strength</div>
            <div class="score-circle" style="width: 80px; height: 80px; margin: 10px auto;">
                <div class="score-circle-num" style="font-size: 1.5rem;">{pct}%</div>
            </div>
            <div style="font-size: 11px; color: {'#10b981' if pct >= 80 else '#f59e0b'}; font-weight: 700;">
                {'● Excellent Fit' if pct >= 80 else ('● Moderate' if pct >= 50 else '● Incomplete')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        st.markdown(f"""
        <div class="saas-card">
            <div class="saas-card-header">Account Overview</div>
            <div style="font-size: 14.5px; color: #0f172a; margin-bottom: 4px;">
                <strong>Username:</strong> <span style="color: #4f46e5;">{username}</span>
            </div>
            <div style="font-size: 14px; color: #334155; margin-bottom: 6px;">
                <strong>Title:</strong> {profile.get('professional_title') or 'Professional'} &nbsp;|&nbsp; 
                <strong>Target:</strong> {profile.get('target_roles') or 'Open to opportunities'}
            </div>
            <p style="font-size: 12px; color: #64748b; margin: 0;">
                Your profile information is strictly isolated to your account and automatically optimizes your AI job recommendations, match scores, cover letters, and email outreach.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 2. Comprehensive Profile Form
    with st.form("comprehensive_profile_form"):
        st.markdown("#### 1️⃣ Basic Contact & Identity")
        c1, c2, c3 = st.columns(3)
        with c1:
            full_name = st.text_input("Full Name", value=profile.get("full_name", ""))
            prof_title = st.text_input("Professional Title", value=profile.get("professional_title", ""), placeholder="e.g. Senior Data Analyst / Python Engineer")
        with c2:
            email = st.text_input("Email Address", value=profile.get("email", ""))
            phone = st.text_input("Phone Number", value=profile.get("phone", ""))
        with c3:
            location = st.text_input("Current Location / City", value=profile.get("location", ""), placeholder="e.g. Bengaluru, India")
            work_auth = st.text_input("Work Authorization", value=profile.get("work_authorization", ""), placeholder="e.g. Citizen, Permanent Resident, Visa")

        st.markdown("<hr style='margin: 12px 0; border: none; border-top: 1px solid #e2e8f0;' />", unsafe_allow_html=True)

        st.markdown("#### 2️⃣ Career & Work Preferences")
        c4, c5, c6 = st.columns(3)
        with c4:
            target_roles = st.text_input(
                "Target Job Roles (comma-separated)",
                value=profile.get("target_roles", ""),
                placeholder="e.g. Data Analyst, Business Intelligence, Python Dev"
            )
            pref_locations = st.text_input(
                "Preferred Locations",
                value=profile.get("preferred_locations", "") or preferences.get("preferred_locations", "India"),
                placeholder="e.g. Bengaluru, Hyderabad, Remote"
            )
        with c5:
            current_mode = profile.get("work_mode_preference") or preferences.get("work_preference", "Any")
            mode_idx = WORK_MODE_OPTIONS.index(current_mode) if current_mode in WORK_MODE_OPTIONS else 0
            work_mode = st.selectbox("Work Mode Preference", WORK_MODE_OPTIONS, index=mode_idx)

            expected_sal = st.text_input(
                "Expected Salary Range",
                value=profile.get("expected_salary", ""),
                placeholder="e.g. ₹8,00,000 - ₹12,00,000 / $90,000"
            )
        with c6:
            notice = st.text_input(
                "Notice Period",
                value=profile.get("notice_period", ""),
                placeholder="e.g. Immediate, 15 Days, 1 Month"
            )
            pref_industries = st.text_input(
                "Preferred Industries",
                value=profile.get("preferred_industries", ""),
                placeholder="e.g. Fintech, Healthcare, SaaS, E-commerce"
            )

        st.markdown("<hr style='margin: 12px 0; border: none; border-top: 1px solid #e2e8f0;' />", unsafe_allow_html=True)

        st.markdown("#### 3️⃣ Skills & Experience")
        c7, c8 = st.columns(2)
        with c7:
            years_exp_val = float(profile.get("years_of_experience", 0.0) or 0.0)
            years_exp = st.number_input("Years of Professional Experience", min_value=0.0, max_value=40.0, value=years_exp_val, step=0.5)
            tech_skills = st.text_area(
                "Technical Skills (Languages, Frameworks, Cloud, Databases)",
                value=profile.get("technical_skills") or profile.get("skills", ""),
                placeholder="Python, SQL, PostgreSQL, Docker, AWS, Power BI, Git...",
                height=90
            )
            soft_skills = st.text_area(
                "Soft Skills & Core Competencies",
                value=profile.get("soft_skills", ""),
                placeholder="Cross-functional leadership, Agile, Problem solving, Technical communication...",
                height=90
            )
        with c8:
            certifications = st.text_area(
                "Certifications & Credentials",
                value=profile.get("certifications", ""),
                placeholder="AWS Certified Solutions Architect, Google Data Analytics Professional...",
                height=80
            )
            education = st.text_area(
                "Education Details",
                value=profile.get("education", ""),
                placeholder="Bachelor of Technology in Computer Science, 2024...",
                height=80
            )
            experience = st.text_area(
                "Work & Project Experience Summary",
                value=profile.get("experience", ""),
                placeholder="Summary of previous roles, key responsibilities, and major project accomplishments...",
                height=90
            )

        st.markdown("<hr style='margin: 12px 0; border: none; border-top: 1px solid #e2e8f0;' />", unsafe_allow_html=True)

        st.markdown("#### 4️⃣ Professional Portfolios & Links")
        c9, c10, c11 = st.columns(3)
        with c9:
            linkedin = st.text_input("LinkedIn Profile URL", value=profile.get("linkedin", ""), placeholder="https://linkedin.com/in/username")
        with c10:
            github = st.text_input("GitHub Profile URL", value=profile.get("github", ""), placeholder="https://github.com/username")
        with c11:
            portfolio = st.text_input("Portfolio / Website URL", value=profile.get("portfolio", ""), placeholder="https://yourportfolio.dev")

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        if st.form_submit_button("💾 Save Candidate Profile", type="primary", use_container_width=True):
            updated_profile = {
                "full_name": full_name.strip(),
                "professional_title": prof_title.strip(),
                "email": email.strip(),
                "phone": phone.strip(),
                "location": location.strip(),
                "work_authorization": work_auth.strip(),
                "target_roles": target_roles.strip(),
                "preferred_locations": pref_locations.strip(),
                "work_mode_preference": work_mode,
                "expected_salary": expected_sal.strip(),
                "notice_period": notice.strip(),
                "preferred_industries": pref_industries.strip(),
                "years_of_experience": float(years_exp),
                "skills": tech_skills.strip(),
                "technical_skills": tech_skills.strip(),
                "soft_skills": soft_skills.strip(),
                "certifications": certifications.strip(),
                "education": education.strip(),
                "experience": experience.strip(),
                "linkedin": linkedin.strip(),
                "github": github.strip(),
                "portfolio": portfolio.strip(),
            }
            ok_prof = update_user_profile(username, updated_profile)

            updated_prefs = {
                "preferred_roles": target_roles.strip(),
                "preferred_locations": pref_locations.strip(),
                "work_preference": work_mode,
            }
            ok_prefs = update_user_preferences(username, updated_prefs)

            if ok_prof:
                st.success("✅ Profile and career preferences successfully updated in the database!")
                st.rerun()
            else:
                st.error("Failed to save profile changes. Please try again.")
