import streamlit as st
from core_logic import (
    load_applications,
    step16_get_job,
    step16_checklist,
    step16_prepare_package,
    auth_get_profile,
    extract_candidate_name_from_resume,
    update_application_status,
)


def render_application_assistant():
    """
    Renders Semi-Automatic Job Application Assistant (Step 16).
    Guides user through an 8-step pipeline with preparation of
    tailored resume, cover letter, email, checklist, and strictly
    user-controlled manual submission.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">🤖</div>
            <div>
                <h1 class="app-title">Semi-Automatic Application Assistant</h1>
                <p class="app-subtitle">A guided, 8-step preparation cockpit ensuring high-quality submissions under your control.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    has_resume = bool(st.session_state.get("resume_text", "").strip())
    if not has_resume:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📄</div>
            <div class="empty-state-title">Upload Resume First</div>
            <p class="empty-state-desc">The assistant requires your resume text to tailor application materials.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Resume Analyzer →", type="primary"):
            st.session_state.current_page = "resume_analyzer"
            st.rerun()
        return

    resume_text = st.session_state.resume_text
    username = st.session_state.get("auth_username", "")
    profile = auth_get_profile(username) if username else {}
    cand_name = profile.get("full_name") or extract_candidate_name_from_resume(resume_text) or "Your Name"

    applications = load_applications()
    if not applications:
        st.info("No applications currently in your tracker. Add a job in Job Search or Tracker to use the guided assistant.")
        if st.button("Search Jobs →", type="primary"):
            st.session_state.current_page = "job_search"
            st.rerun()
        return

    # Visual 8-step Stepper
    st.markdown("""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; margin-bottom: 1.5rem;">
        <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #94a3b8; margin-bottom: 8px;">GUIDED WORKFLOW STEPS</div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap; font-size: 12px; font-weight: 600;">
            <span style="background: #eff6ff; color: #1e40af; padding: 4px 8px; border-radius: 6px;">1. Select Job</span>
            <span style="color: #cbd5e1;">➔</span>
            <span style="background: #eff6ff; color: #1e40af; padding: 4px 8px; border-radius: 6px;">2. Review Resume</span>
            <span style="color: #cbd5e1;">➔</span>
            <span style="background: #eff6ff; color: #1e40af; padding: 4px 8px; border-radius: 6px;">3. Tailor</span>
            <span style="color: #cbd5e1;">➔</span>
            <span style="background: #eff6ff; color: #1e40af; padding: 4px 8px; border-radius: 6px;">4. Cover Letter</span>
            <span style="color: #cbd5e1;">➔</span>
            <span style="background: #eff6ff; color: #1e40af; padding: 4px 8px; border-radius: 6px;">5. Email</span>
            <span style="color: #cbd5e1;">➔</span>
            <span style="background: #eff6ff; color: #1e40af; padding: 4px 8px; border-radius: 6px;">6. Open Portal</span>
            <span style="color: #cbd5e1;">➔</span>
            <span style="background: #eff6ff; color: #1e40af; padding: 4px 8px; border-radius: 6px;">7. User Review</span>
            <span style="color: #cbd5e1;">➔</span>
            <span style="background: #ecfdf5; color: #065f46; padding: 4px 8px; border-radius: 6px;">8. User Submits</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Step 1: Select Application
    st.markdown("""
    <div class="saas-card">
        <div class="saas-card-header">1️⃣ Select Target Application</div>
    """, unsafe_allow_html=True)

    app_options = [f"{idx + 1}. {a.get('company')} — {a.get('title')}" for idx, a in enumerate(applications)]
    selected_idx = st.selectbox("Choose Saved Job from Tracker", range(len(app_options)), format_func=lambda i: app_options[i])
    current_job = applications[selected_idx]

    c1, c2, c3 = st.columns(3)
    c1.write(f"🏢 **Company:** {current_job.get('company')}")
    c2.write(f"💼 **Role:** {current_job.get('title')}")
    c3.write(f"📌 **Status:** {current_job.get('status')}")

    job_url = current_job.get("application_url", "")
    target_jd = st.text_area(
        "Target Job Description (for Tailoring & Generation)",
        value=current_job.get("job_description") or st.session_state.get("current_jd", ""),
        height=130,
        key="assistant_jd_input"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Step 2: Readiness Checklist
    checklist = step16_checklist(current_job, target_jd, resume_text)
    st.markdown("""
    <div class="saas-card">
        <div class="saas-card-header">2️⃣ Application Readiness Checklist</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 13px;">
    """, unsafe_allow_html=True)
    for label, ok in checklist:
        mark = "✅" if ok else "⚠️"
        color = "#065f46" if ok else "#b45309"
        st.markdown(f"<div style='color: {color};'><strong>{mark}</strong> {label}</div>", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    # Generate Full Package
    if st.button("🚀 Prepare Complete Application Package", type="primary", key="btn_prep_pkg"):
        if not target_jd.strip():
            st.warning("Please paste the job description above to generate tailored materials.")
        else:
            with st.spinner("Generating tailored resume summary, cover letter, and application email..."):
                pkg = step16_prepare_package(
                    resume_text=resume_text,
                    job_description=target_jd,
                    application=current_job,
                    candidate_name=cand_name,
                    hiring_manager="",
                    tone="Professional"
                )
                st.session_state.assistant_package = pkg
                st.session_state.assistant_pkg_ready = True
                st.success("Complete application package prepared!")

    if st.session_state.get("assistant_pkg_ready", False) and st.session_state.get("assistant_package"):
        pkg = st.session_state.assistant_package
        
        st.markdown("### 📦 Generated Application Materials")
        pkg_tab1, pkg_tab2, pkg_tab3 = st.tabs(["✨ Tailored Summary", "📄 Generated Cover Letter", "✉️ Application Email"])

        with pkg_tab1:
            st.markdown(f"""
            <div class="saas-card">
                <div class="saas-card-header">Tailored Executive Summary</div>
                <p style="font-size: 14px; line-height: 1.6; color: #1e293b;">{pkg['summary']}</p>
                <div style="font-weight: 700; margin-top: 12px; font-size: 13px;">Key Skills to Highlight:</div>
                <div class="chip-container">
                    {''.join([f'<span class="skill-chip skill-chip-match">✓ {s}</span>' for s in pkg['matching']])}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with pkg_tab2:
            st.markdown(f"""
            <div class="document-sheet">
{pkg['cover_letter']}
            </div>
            """, unsafe_allow_html=True)

        with pkg_tab3:
            st.markdown(f"""
            <div class="email-container">
                <div class="email-header">
                    <div class="email-header-row"><strong>Subject:</strong> {pkg['subject']}</div>
                </div>
                <div class="email-body">{pkg['email']}</div>
            </div>
            """, unsafe_allow_html=True)

        # Step 6, 7 & 8: Submission & Update Status
        st.markdown("""
        <div class="saas-card" style="border: 2px solid #4f46e5; background: #fdfefe;">
            <div class="saas-card-header" style="color: #4f46e5;">🛡️ Final Step: Review & Apply (User-Controlled)</div>
            <p style="font-size: 0.88rem; color: #475569; margin-bottom: 1rem;">
                Open the official employer application portal, review all materials, paste your customized letter/email, and submit.
            </p>
        </div>
        """, unsafe_allow_html=True)

        act_c1, act_c2 = st.columns(2)
        with act_c1:
            if job_url:
                st.link_button("🌐 Open Job Portal in New Tab", job_url, type="primary", use_container_width=True)
            else:
                st.info("No URL recorded for this role. You can manually apply on the company careers page.")
        with act_c2:
            if st.button("✅ Mark as 'Applied' in Tracker", use_container_width=True, key="btn_mark_applied"):
                update_application_status(selected_idx, "Applied")
                st.success(f"Status for {current_job.get('company')} updated to 'Applied'!")
                st.rerun()
