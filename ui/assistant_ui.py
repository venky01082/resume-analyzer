import streamlit as st
from core_logic import (
    load_applications,
    step16_prepare_package,
    auth_get_profile,
    extract_candidate_name_from_resume,
    update_application_status,
)
from database.repository import get_applications, get_saved_jobs, get_default_resume


def render_application_assistant():
    """
    Renders Semi-Automatic Job Application Assistant (Phase 17 & 18).
    Guides candidate through preparation of tailored summary, cover letter,
    application email, and the 7-item Smart Application Checklist.
    Strictly user-controlled manual submission to ensure 100% human-in-the-loop integrity.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">🤖</div>
            <div>
                <h1 class="app-title">Semi-Automatic Application Assistant</h1>
                <p class="app-subtitle">Guided preparation cockpit ensuring high-impact tailored applications strictly submitted under your control.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    username = st.session_state.get("auth_username", "")
    if not username:
        st.warning("Please log in to use the Application Assistant.")
        return

    # Check resume availability
    resume_text = st.session_state.get("resume_text", "").strip()
    if not resume_text:
        default_res = get_default_resume(username)
        if default_res:
            resume_text = default_res.get("text", "")
            st.session_state.resume_text = resume_text
            st.session_state.resume_score = default_res.get("score", 75)
            st.session_state.resume_skills = default_res.get("skills", [])

    if not resume_text:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📄</div>
            <div class="empty-state-title">No Resume Loaded</div>
            <p class="empty-state-desc">The assistant requires your resume to generate tailored application documents.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Resume Analyzer →", type="primary"):
            st.session_state.current_page = "resume_analyzer"
            st.rerun()
        return

    profile = auth_get_profile(username)
    cand_name = profile.get("full_name") or extract_candidate_name_from_resume(resume_text) or username.capitalize()

    applications = get_applications(username)
    saved_jobs = get_saved_jobs(username)

    if not applications and not saved_jobs:
        st.info("No tracked applications or bookmarked jobs found. Please find and save an opportunity first!")
        if st.button("Search Jobs →", type="primary"):
            st.session_state.current_page = "job_search"
            st.rerun()
        return

    # Stepper Indicator
    st.markdown("""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 0.9rem 1.25rem; margin-bottom: 1.25rem;">
        <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #94a3b8; margin-bottom: 8px;">ASSISTANT WORKFLOW</div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap; font-size: 12px; font-weight: 600;">
            <span style="background: #eff6ff; color: #1e40af; padding: 4px 8px; border-radius: 6px;">1. Select Job</span>
            <span style="color: #cbd5e1;">➔</span>
            <span style="background: #eff6ff; color: #1e40af; padding: 4px 8px; border-radius: 6px;">2. Review Requirements</span>
            <span style="color: #cbd5e1;">➔</span>
            <span style="background: #eff6ff; color: #1e40af; padding: 4px 8px; border-radius: 6px;">3. Generate Materials</span>
            <span style="color: #cbd5e1;">➔</span>
            <span style="background: #eff6ff; color: #1e40af; padding: 4px 8px; border-radius: 6px;">4. Smart Checklist</span>
            <span style="color: #cbd5e1;">➔</span>
            <span style="background: #ecfdf5; color: #065f46; padding: 4px 8px; border-radius: 6px;">5. User Submits</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Combine Tracker and Bookmarks for selection
    job_choices = []
    for a in applications:
        job_choices.append({
            "type": "application",
            "id": a.get("app_id"),
            "title": a.get("title", "Role"),
            "company": a.get("company", "Company"),
            "location": a.get("location", "India"),
            "url": a.get("application_url", ""),
            "description": a.get("job_description", ""),
            "status": a.get("status", "Applied"),
            "display": f"📌 [Tracker] {a.get('company')} — {a.get('title')}"
        })
    for b in saved_jobs:
        job_choices.append({
            "type": "saved_job",
            "id": b.get("job_id"),
            "title": b.get("title", "Role"),
            "company": b.get("company", "Company"),
            "location": b.get("location", "India"),
            "url": b.get("url", ""),
            "description": b.get("description", ""),
            "status": "Saved",
            "display": f"⭐ [Saved] {b.get('company')} — {b.get('title')}"
        })

    st.markdown("""
    <div class="saas-card">
        <div class="saas-card-header">1️⃣ Select Target Opportunity</div>
    """, unsafe_allow_html=True)

    selected_idx = st.selectbox(
        "Choose Opportunity to Prepare",
        range(len(job_choices)),
        format_func=lambda i: job_choices[i]["display"]
    )
    current_job = job_choices[selected_idx]

    c1, c2, c3 = st.columns(3)
    c1.write(f"🏢 **Company:** {current_job.get('company')}")
    c2.write(f"💼 **Role:** {current_job.get('title')}")
    c3.write(f"📍 **Location:** {current_job.get('location')}")

    job_url = current_job.get("url", "").strip()
    target_jd = st.text_area(
        "Job Description & Key Requirements (paste full text for maximum tailoring precision)",
        value=current_job.get("description") or st.session_state.get("current_jd", ""),
        height=130,
        key="assistant_jd_input"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # 2. Package Generator
    if st.button("✨ Generate Tailored Application Package", type="primary", key="btn_prep_pkg", use_container_width=True):
        if not target_jd.strip():
            st.warning("Please paste the job description above to generate tailored materials.")
        else:
            with st.spinner("Analyzing job requirements and synthesizing customized application package..."):
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
                st.success("Application package successfully generated!")

    pkg_ready = st.session_state.get("assistant_pkg_ready", False) and bool(st.session_state.get("assistant_package"))

    # 3. Phase 18: Smart Application Checklist
    ats_score = st.session_state.get("resume_score", 0)
    checklist_items = [
        ("Candidate resume loaded", bool(resume_text.strip())),
        ("ATS keyword compatibility checked", bool(ats_score > 0)),
        ("Role-aligned resume summary tailored", pkg_ready),
        ("Personalized cover letter drafted", pkg_ready),
        ("Outreach email prepared", pkg_ready),
        ("Job description & skills reviewed", bool(target_jd.strip())),
        ("Official application URL verified", bool(job_url)),
    ]

    all_ready = all(ok for _, ok in checklist_items)
    ready_count = sum(1 for _, ok in checklist_items if ok)

    st.markdown(f"""
    <div class="saas-card" style="margin-top: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <div class="saas-card-header" style="margin: 0;">2️⃣ Smart Application Checklist</div>
            <span style="font-size: 12px; font-weight: 700; background: {'#ecfdf5' if all_ready else '#fffbeb'}; color: {'#065f46' if all_ready else '#b45309'}; padding: 2px 10px; border-radius: 99px; border: 1px solid {'#a7f3d0' if all_ready else '#fef3c7'};">
                {ready_count}/7 Items Complete
            </span>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; font-size: 13px;">
    """, unsafe_allow_html=True)

    for label, ok in checklist_items:
        icon = "✅" if ok else "⚠️"
        color = "#047857" if ok else "#b45309"
        weight = "700" if ok else "500"
        st.markdown(f"<div style='color: {color}; font-weight: {weight};'>{icon} {label}</div>", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    # 4. Display Generated Application Materials
    if pkg_ready:
        pkg = st.session_state.assistant_package
        st.markdown("### 📦 Generated Application Documents")
        pkg_tab1, pkg_tab2, pkg_tab3 = st.tabs(["✨ Tailored Summary", "📄 Cover Letter", "✉️ Application Email"])

        with pkg_tab1:
            st.markdown(f"""
            <div class="saas-card">
                <div class="saas-card-header">Tailored Candidate Summary</div>
                <p style="font-size: 14px; line-height: 1.6; color: #1e293b;">{pkg['summary']}</p>
                <div style="font-weight: 700; margin-top: 12px; font-size: 13px;">Key Matched Skills:</div>
                <div class="chip-container">
                    {''.join([f'<span class="skill-chip skill-chip-match">✓ {s}</span>' for s in pkg.get('matching', [])])}
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

        # 5. Final Step: Ethical User-Controlled Submission
        st.markdown("""
        <div class="saas-card" style="border: 2px solid #4f46e5; background: #fdfefe; margin-top: 1.5rem;">
            <div class="saas-card-header" style="color: #4f46e5; font-size: 1.05rem;">
                🛡️ Human-in-the-Loop: Ready to Apply
            </div>
            <p style="font-size: 0.88rem; color: #475569; margin-bottom: 0.85rem; line-height: 1.5;">
                In accordance with employer portal security guidelines and anti-spam protocols, final application submission is strictly under your control. Click below to launch the official career page and paste your customized application documents.
            </p>
        </div>
        """, unsafe_allow_html=True)

        act_c1, act_c2 = st.columns(2)
        with act_c1:
            if job_url:
                st.link_button("🌐 Open Official Job Portal", job_url, type="primary", use_container_width=True)
            else:
                st.info("No direct application link recorded. Please navigate to the employer's official careers site.")
        with act_c2:
            if st.button("✅ Mark Application as 'Applied'", use_container_width=True, key="btn_assistant_mark_applied"):
                if current_job["type"] == "application":
                    update_application_status(current_job["id"], "Applied")
                st.success(f"Status for '{current_job.get('company')}' successfully updated to 'Applied' in your pipeline!")
                st.rerun()
