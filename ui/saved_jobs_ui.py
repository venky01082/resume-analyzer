"""
Saved Jobs UI Module
Provides a dedicated workspace for managing bookmarked jobs with user isolation.
"""

import streamlit as st
from database import (
    get_saved_jobs,
    delete_saved_job,
    create_application,
    get_applications,
)


def render_saved_jobs():
    """Renders the Saved Jobs bookmark workspace."""
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">⭐</div>
            <div>
                <h1 class="app-title">Saved Jobs</h1>
                <p class="app-subtitle">Your personal shortlist of bookmarked opportunities ready for application.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    username = st.session_state.get("auth_username", "venky")
    saved_jobs = get_saved_jobs(username)

    if not saved_jobs:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">⭐</div>
            <div class="empty-state-title">No Saved Jobs Yet</div>
            <p class="empty-state-desc">
                When searching for jobs or reviewing recommendations, click '⭐ Save Job' to shortlist them here.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔎 Search Real Jobs Now", type="primary"):
            st.session_state.current_page = "job_search"
            st.rerun()
        return

    # Top KPI Metrics
    total_saved = len(saved_jobs)
    scores = [j.get("score", 0) for j in saved_jobs if j.get("score")]
    avg_score = round(sum(scores) / len(scores)) if scores else 0

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">⭐ Total Bookmarked</div>
            <div class="stat-value">{total_saved}</div>
            <div class="stat-subtext-neutral">Opportunities saved</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🎯 Average Match</div>
            <div class="stat-value">{avg_score}%</div>
            <div class="stat-subtext" style="color: {'#10b981' if avg_score >= 70 else '#4f46e5'};">Against active resume</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🚀 Ready To Apply</div>
            <div class="stat-value">{len([j for j in saved_jobs if j.get('url')])}</div>
            <div class="stat-subtext-neutral">With direct apply links</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Search & Filter
    f1, f2 = st.columns([3, 1])
    with f1:
        search_query = st.text_input("Filter Saved Jobs", placeholder="Search by job title or company...", label_visibility="collapsed")
    with f2:
        min_score = st.selectbox("Min Match %", [0, 50, 70, 80], index=0, label_visibility="collapsed")

    filtered_jobs = [
        j for j in saved_jobs
        if (not search_query.strip() or search_query.lower() in j.get("title", "").lower() or search_query.lower() in j.get("company", "").lower())
        and (j.get("score", 0) >= min_score)
    ]

    st.markdown(f"#### 💼 Shortlisted Positions ({len(filtered_jobs)})")

    for idx, job in enumerate(filtered_jobs):
        job_id = job.get("job_id")
        title = job.get("title", "Position")
        company = job.get("company", "Company")
        location = job.get("location", "India")
        score = job.get("score", 0)
        url = job.get("url", "")
        saved_at = job.get("saved_at", "")
        status = job.get("status", "Saved")

        score_color = "#10b981" if score >= 75 else ("#4f46e5" if score >= 50 else "#64748b")

        with st.container():
            st.markdown(f"""
            <div class="job-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h3 class="job-title">{title}</h3>
                        <div class="job-company">🏢 {company} &nbsp;•&nbsp; 📍 {location}</div>
                        <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">Saved: {saved_at}</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: {'#ecfdf5' if score >= 70 else '#eff6ff'}; color: {score_color}; font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 99px; border: 1px solid {'#a7f3d0' if score >= 70 else '#bfdbfe'};">
                            🎯 {score}% Fit
                        </span>
                        <div style="margin-top: 6px;">
                            <span class="status-badge badge-saved">{status}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            b1, b2, b3, b4 = st.columns([1.5, 1.5, 1.5, 1])

            with b1:
                if url:
                    st.link_button("🔗 Open Job Link", url, use_container_width=True)
                else:
                    st.button("No Link Available", disabled=True, key=f"nolink_{job_id}", use_container_width=True)

            with b2:
                if st.button("✨ Tailor for This Role", key=f"tailor_job_{job_id}", use_container_width=True):
                    st.session_state.current_jd = job.get("description") or f"{title} at {company}. Requirements: analytical skills, problem solving."
                    st.session_state.current_page = "resume_tailoring"
                    st.rerun()

            with b3:
                if st.button("📌 Move to Applied", key=f"apply_job_{job_id}", use_container_width=True):
                    create_application(
                        user_id=username,
                        title=title,
                        company=company,
                        location=location,
                        score=score,
                        application_url=url,
                        status="Applied",
                        job_description=job.get("description", "")
                    )
                    delete_saved_job(username, job_id)
                    st.success("Moved from Saved to Applied Tracker!")
                    st.rerun()

            with b4:
                if st.button("🗑️ Remove", key=f"del_saved_{job_id}", use_container_width=True):
                    delete_saved_job(username, job_id)
                    st.rerun()
