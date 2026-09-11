import streamlit as st
from core_logic import auth_get_profile

NAV_SECTIONS = [
    ("OVERVIEW", [
        ("🏠 Dashboard", "dashboard"),
    ]),
    ("RESUME WORKSPACE", [
        ("📄 Resume Analyzer", "resume_analyzer"),
        ("🎯 ATS Analyzer", "ats_analyzer"),
        ("📁 My Resumes", "my_resumes"),
    ]),
    ("JOB DISCOVERY", [
        ("🔎 Job Search", "job_search"),
        ("⭐ Saved Jobs", "saved_jobs"),
        ("🧠 Job Matching", "job_matching"),
    ]),
    ("AI APPLICATION TOOLS", [
        ("✨ Resume Tailoring", "resume_tailoring"),
        ("✍️ Cover Letter", "cover_letter"),
        ("📧 Application Email", "application_email"),
    ]),
    ("TRACKING & WORKFLOW", [
        ("📌 Application Tracker", "application_tracker"),
        ("⏰ Follow-Up Center", "followups"),
        ("🤖 Application Assistant", "application_assistant"),
    ]),
    ("INSIGHTS & ACCOUNT", [
        ("📊 Analytics", "analytics"),
        ("👤 Profile", "profile"),
        ("⚙️ Settings", "settings"),
    ]),
]


def render_sidebar():
    """
    Renders modern SaaS sidebar navigation with user info, status badge,
    categorized menu sections, and page router controls.
    Returns the currently selected page key.
    """
    with st.sidebar:
        # App Branding
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; padding: 6px 0;">
            <div style="font-size: 28px; line-height: 1;">🤖</div>
            <div>
                <div style="font-size: 16px; font-weight: 800; color: #0f172a; line-height: 1.2;">JobAssistant AI</div>
                <div style="font-size: 11px; font-weight: 500; color: #64748b;">Smart Career Platform</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # User Profile Status Card
        username = st.session_state.get("auth_username", "")
        profile = auth_get_profile(username) if username else {}
        display_name = profile.get("full_name") or username.capitalize() or "User"

        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 32px; height: 32px; background: #e0e7ff; color: #4338ca; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px;">
                        {display_name[0].upper()}
                    </div>
                    <div>
                        <div style="font-size: 13.5px; font-weight: 700; color: #0f172a; max-width: 190px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{display_name}</div>
                        <div style="font-size: 11px; color: #10b981; font-weight: 600;">● Online</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Quick Resume Status Indicator
        has_resume = bool(st.session_state.get("resume_text", "").strip())
        if has_resume:
            skills_count = len(st.session_state.get("resume_skills", []))
            score_val = st.session_state.get("resume_score", 0)
            st.markdown(f"""
            <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 8px 12px; margin-bottom: 14px; font-size: 12px; color: #065f46;">
                <div style="font-weight: 700; display: flex; align-items: center; justify-content: space-between;">
                    <span>📄 Resume Loaded</span>
                    <span style="background: #10b981; color: white; padding: 1px 6px; border-radius: 99px; font-size: 10px;">{score_val}/100</span>
                </div>
                <div style="font-size: 11px; color: #047857; margin-top: 2px;">{skills_count} skills identified</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #fffbeb; border: 1px solid #fef3c7; border-radius: 8px; padding: 8px 12px; margin-bottom: 14px; font-size: 12px; color: #92400e;">
                <div style="font-weight: 700;">⚠️ No Resume Loaded</div>
                <div style="font-size: 11px; color: #b45309; margin-top: 2px;">Upload in Analyzer to unlock full AI</div>
            </div>
            """, unsafe_allow_html=True)

        current_page_key = st.session_state.get("current_page", "dashboard")

        # Render Modern SaaS Categorized Navigation
        for section_title, items in NAV_SECTIONS:
            st.markdown(f"<div style='font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #94a3b8; margin: 12px 0 6px 4px;'>{section_title}</div>", unsafe_allow_html=True)
            for label, page_key in items:
                is_active = (current_page_key == page_key)
                if st.button(
                    label,
                    key=f"nav_btn_{page_key}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    if st.session_state.get("current_page") != page_key:
                        st.session_state.current_page = page_key
                        st.rerun()

        st.markdown("<hr style='margin: 16px 0; border: none; border-top: 1px solid #e2e8f0;' />", unsafe_allow_html=True)

        # Logout & Session Clear
        st.markdown("<div class='sidebar-logout-wrapper'>", unsafe_allow_html=True)
        if st.button("🚪  Log Out", key="sidebar_logout_btn", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.auth_username = ""
            st.session_state.resume_text = ""
            st.session_state.resume_skills = []
            st.session_state.resume_score = 0
            st.session_state.current_page = "dashboard"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    return st.session_state.current_page

