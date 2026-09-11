import streamlit as st
from core_logic import (
    load_jobs,
    recommend_jobs,
    auth_get_profile,
    add_application,
)
from database.applications import (
    get_applications,
    get_status_counts,
    get_overdue_follow_ups,
    get_today_follow_ups,
)
from database.resumes import get_resumes
from database.jobs import get_saved_jobs


def render_dashboard():
    """
    Renders the modern SaaS Executive Dashboard with live user-scoped metrics,
    follow-up priority alerts, action shortcuts, recommended jobs, and active applications.
    """
    username = st.session_state.get("auth_username", "venky")
    profile = auth_get_profile(username) if username else {}
    first_name = profile.get("full_name", "").split()[0] if profile.get("full_name") else username.capitalize() or "there"

    # App Header
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">🤖</div>
            <div>
                <h1 class="app-title">AI Job Application Assistant</h1>
                <p class="app-subtitle">Your end-to-end intelligent command center for resumes, discovery, and applications.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Welcome Banner
    banner_col1, banner_col2 = st.columns([3, 1])
    with banner_col1:
        st.markdown(f"""
        <div class="welcome-banner">
            <h2 class="welcome-title">Welcome back, {first_name} 👋</h2>
            <p class="welcome-desc">Track opportunities, optimize your resume against live ATS criteria, and manage your follow-ups.</p>
        </div>
        """, unsafe_allow_html=True)
    with banner_col2:
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        if st.button("📄 Analyze My Resume", type="primary", use_container_width=True):
            st.session_state.current_page = "resume_analyzer"
            st.rerun()

    # Load User-Scoped Data
    applications = get_applications(username)
    counts = get_status_counts(applications)
    total_apps = len(applications)
    saved_resumes = get_resumes(username)
    saved_jobs = get_saved_jobs(username)
    overdue_followups = get_overdue_follow_ups(applications)
    today_followups = get_today_follow_ups(applications)

    interview_count = (
        counts.get("Interview", 0) +
        counts.get("Technical Round", 0) +
        counts.get("HR Round", 0)
    )

    try:
        jobs = load_jobs()
        total_jobs_found = len(jobs)
    except Exception:
        jobs = []
        total_jobs_found = 0

    has_resume = bool(st.session_state.get("resume_text", "").strip())
    resume_score_val = st.session_state.get("resume_score", 0)
    if not has_resume and saved_resumes:
        # Pick default or first resume score
        default_r = next((r for r in saved_resumes if r.get("is_default")), saved_resumes[0])
        resume_score_val = default_r.get("score", 70)
        has_resume = True

    # Urgent Follow-Up Alert Banner (if applicable)
    if overdue_followups:
        o_first = overdue_followups[0]["application"]
        st.error(f"🔴 **Action Required:** You have **{len(overdue_followups)} overdue follow-up(s)**! First due: **{o_first.get('company')}** ({o_first.get('title')}). [Open Follow-Up Center →](javascript:void(0))")
    elif today_followups:
        t_first = today_followups[0]["application"]
        st.warning(f"🟡 **Due Today:** Follow-up scheduled with **{t_first.get('company')}** for **{t_first.get('title')}**.")

    # 5 KPI Summary Cards
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        score_status = "↑ Strong" if resume_score_val >= 80 else ("↑ Good" if resume_score_val >= 60 else ("Needs Work" if has_resume else "No Resume"))
        st.markdown(f"""
        <div class="stat-card">
            <div>
                <div class="stat-label">📄 Resume Health</div>
                <div class="stat-value">{resume_score_val} <span style="font-size: 0.9rem; color: #64748b; font-weight: 500;">/ 100</span></div>
            </div>
            <div class="stat-subtext" style="color: {'#10b981' if resume_score_val >= 60 else '#f59e0b'};">{score_status}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="stat-card">
            <div>
                <div class="stat-label">📁 Saved Resumes</div>
                <div class="stat-value">{len(saved_resumes)}</div>
            </div>
            <div class="stat-subtext-neutral">Active versions</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="stat-card">
            <div>
                <div class="stat-label">⭐ Bookmarked Jobs</div>
                <div class="stat-value">{len(saved_jobs)}</div>
            </div>
            <div class="stat-subtext-neutral">Target opportunities</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="stat-card">
            <div>
                <div class="stat-label">📌 Tracked Applications</div>
                <div class="stat-value">{total_apps}</div>
            </div>
            <div class="stat-subtext-neutral">{counts.get('Applied', 0)} submitted</div>
        </div>
        """, unsafe_allow_html=True)

    with c5:
        st.markdown(f"""
        <div class="stat-card">
            <div>
                <div class="stat-label">🎤 Active Interviews</div>
                <div class="stat-value" style="color: #4f46e5;">{interview_count}</div>
            </div>
            <div class="stat-subtext" style="color: #10b981;">{counts.get('Offer', 0)} Offers received</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Quick Actions Row
    st.markdown("### ⚡ Quick Navigation")
    q1, q2, q3, q4, q5, q6 = st.columns(6)

    with q1:
        if st.button("📄 Analyze Resume", use_container_width=True):
            st.session_state.current_page = "resume_analyzer"
            st.rerun()
    with q2:
        if st.button("📁 My Resumes", use_container_width=True):
            st.session_state.current_page = "my_resumes"
            st.rerun()
    with q3:
        if st.button("🔎 Search Jobs", use_container_width=True):
            st.session_state.current_page = "job_search"
            st.rerun()
    with q4:
        if st.button("⭐ Saved Jobs", use_container_width=True):
            st.session_state.current_page = "saved_jobs"
            st.rerun()
    with q5:
        if st.button("⏰ Follow-Ups", use_container_width=True):
            st.session_state.current_page = "followups"
            st.rerun()
    with q6:
        if st.button("🤖 AI Assistant", use_container_width=True):
            st.session_state.current_page = "application_assistant"
            st.rerun()

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Main Dashboard Body: Recommended Jobs & Recent Applications
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 🎯 Recommended Opportunities")
        resume_skills = st.session_state.get("resume_skills", [])
        
        if not jobs:
            st.info("No jobs found in the local catalog.")
        else:
            try:
                from services.job_recommendation import recommend_jobs_for_user
                recommendations = recommend_jobs_for_user(username, jobs, limit=4)
            except Exception:
                recommendations = recommend_jobs(resume_skills, jobs) if resume_skills else [{"job": j, "score": 75, "matching_skills": [], "missing_skills": []} for j in jobs[:4]]
            
            for idx, rec in enumerate(recommendations[:4]):
                job = rec["job"]
                score = rec["score"]
                matching = rec.get("explanation", {}).get("matching_skills", rec.get("matching_skills", []))
                
                with st.container():
                    st.markdown(f"""
                    <div class="job-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <h4 class="job-title">{job.get('title', 'Position')}</h4>
                                <div class="job-company">🏢 {job.get('company', 'Company')} &nbsp;•&nbsp; 📍 {job.get('location', 'India')}</div>
                            </div>
                            <span style="background: {'#ecfdf5' if score >= 70 else '#eff6ff'}; color: {'#065f46' if score >= 70 else '#1e40af'}; font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 99px; border: 1px solid {'#a7f3d0' if score >= 70 else '#bfdbfe'};">
                                🎯 {score}% Match
                            </span>
                        </div>
                        <div class="chip-container">
                            {''.join([f'<span class="skill-chip skill-chip-match">✓ {s}</span>' for s in matching[:4]])}
                            {''.join([f'<span class="skill-chip skill-chip-category">{s}</span>' for s in job.get('skills', [])[:3] if s not in matching])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    btn_c1, btn_c2 = st.columns([1, 1])
                    url = job.get("application_url") or job.get("redirect_url") or ""
                    with btn_c1:
                        if url:
                            st.link_button("🔗 View Job", url, use_container_width=True)
                        else:
                            st.button("📋 Details", key=f"rec_det_{idx}", use_container_width=True)
                    with btn_c2:
                        if st.button("⭐ Track in Pipeline", key=f"dash_save_job_{idx}", use_container_width=True):
                            saved = add_application(
                                title=job.get("title", "Job"),
                                company=job.get("company", "Company"),
                                location=job.get("location", "India"),
                                score=score,
                                application_url=url,
                                status="Saved",
                                user_id=username
                            )
                            if saved:
                                st.success("Saved to Pipeline Tracker!")
                                st.rerun()
                            else:
                                st.info("Already tracked.")

    with col_right:
        st.markdown("### 📌 Recent Applications")
        if not applications:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <div class="empty-state-title">No applications yet</div>
                <p class="empty-state-desc">Start applying or bookmark jobs to see your tracking pipeline here.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔎 Search Real Jobs", key="dash_empty_search", use_container_width=True):
                st.session_state.current_page = "job_search"
                st.rerun()
        else:
            for i, app in enumerate(applications[-4:][::-1]):
                status = app.get("status", "Saved")
                badge_class = f"badge-{status.lower().replace(' ', '-')}"
                st.markdown(f"""
                <div class="saas-card" style="padding: 1rem; margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
                        <div style="font-weight: 700; color: #0f172a; font-size: 14px;">{app.get('title', 'Role')}</div>
                        <span class="status-badge {badge_class}">{status}</span>
                    </div>
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 6px;">🏢 {app.get('company', 'Company')} &nbsp;•&nbsp; 📍 {app.get('location', 'India')}</div>
                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #94a3b8;">
                        <span>Applied: {app.get('applied_date') or 'Not yet'}</span>
                        <span style="font-weight: 600; color: #4f46e5;">{app.get('score', 0)}% Match</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if st.button("View All Applications →", key="dash_view_all_apps", use_container_width=True):
                st.session_state.current_page = "application_tracker"
                st.rerun()

