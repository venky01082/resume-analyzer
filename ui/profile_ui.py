import streamlit as st
from core_logic import (
    auth_get_profile,
    auth_update_profile,
)


def render_profile():
    """
    Renders user profile management page with completeness meter,
    career preferences, professional links, and users.json persistence.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">👤</div>
            <div>
                <h1 class="app-title">Candidate Profile & Preferences</h1>
                <p class="app-subtitle">Manage your personal and career details used across recommendations and generators.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    username = st.session_state.get("auth_username", "")
    profile = auth_get_profile(username) if username else {}

    # Completeness calculation
    check_fields = [
        profile.get("full_name"),
        profile.get("email"),
        profile.get("location"),
        profile.get("target_roles"),
        profile.get("skills"),
        profile.get("education"),
        profile.get("experience"),
    ]
    completed_fields = sum(1 for f in check_fields if bool(str(f or "").strip()))
    pct = round(completed_fields / len(check_fields) * 100)

    col_gauge, col_header = st.columns([1, 3])
    with col_gauge:
        st.markdown(f"""
        <div class="saas-card" style="text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase;">Profile Strength</div>
            <div class="score-circle" style="width: 80px; height: 80px; margin: 10px auto;">
                <div class="score-circle-num" style="font-size: 1.5rem;">{pct}%</div>
            </div>
            <div style="font-size: 11px; color: {'#10b981' if pct == 100 else '#f59e0b'}; font-weight: 700;">
                {'● Fully Complete' if pct == 100 else '● In Progress'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_header:
        st.markdown(f"""
        <div class="saas-card">
            <div class="saas-card-header">Account Details</div>
            <div style="font-size: 14px; color: #1e293b; margin-bottom: 4px;"><strong>Username:</strong> {username}</div>
            <div style="font-size: 14px; color: #1e293b; margin-bottom: 8px;"><strong>Full Name:</strong> {profile.get('full_name') or 'Not provided'}</div>
            <p style="font-size: 12px; color: #64748b; margin: 0;">
                Keeping your profile complete enhances auto-filled cover letters, emails, and job matching scores.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Edit Form
    with st.form("profile_edit_form"):
        st.markdown("### ✏️ Edit Candidate Information")

        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name", value=profile.get("full_name", ""))
            email = st.text_input("Email Address", value=profile.get("email", ""))
            phone = st.text_input("Phone Number", value=profile.get("phone", ""))
            location = st.text_input("Location / City", value=profile.get("location", ""))
            roles = st.text_input("Preferred Job Roles", value=profile.get("target_roles", ""), placeholder="e.g. Data Analyst, ML Intern, AI Engineer")
        with c2:
            linkedin = st.text_input("LinkedIn Profile URL", value=profile.get("linkedin", ""), placeholder="https://linkedin.com/in/username")
            github = st.text_input("GitHub Profile URL", value=profile.get("github", ""), placeholder="https://github.com/username")
            portfolio = st.text_input("Portfolio / Website URL", value=profile.get("portfolio", ""), placeholder="https://yourportfolio.dev")
            education = st.text_area("Education Details", value=profile.get("education", ""), placeholder="Degree, Major, University, Graduation Year...", height=95)

        skills = st.text_area("Technical & Analytical Skills", value=profile.get("skills", ""), placeholder="Python, SQL, Machine Learning, Power BI, Statistics...", height=95)
        experience = st.text_area("Experience Summary", value=profile.get("experience", ""), placeholder="Internships, projects, work experience...", height=95)

        if st.form_submit_button("💾 Save Profile Changes", type="primary"):
            ok = auth_update_profile(
                username=username,
                full_name=name,
                email=email,
                phone=phone,
                location=location,
                target_roles=roles,
                skills=skills,
                experience=experience,
                education=education,
                linkedin=linkedin,
                github=github,
                portfolio=portfolio
            )
            if ok:
                st.success("✅ Profile changes saved successfully to users.json!")
                st.rerun()
            else:
                st.error("Failed to update profile.")
