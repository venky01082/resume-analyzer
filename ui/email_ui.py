import streamlit as st
from core_logic import (
    generate_application_email,
    create_application_email_pdf,
    extract_candidate_name_from_resume,
    extract_cover_letter_job_title,
    extract_cover_letter_company,
    auth_get_profile,
)


def render_application_email():
    """
    Renders modern AI Application Email Generator with
    realistic email client preview container and PDF/TXT export.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">📧</div>
            <div>
                <h1 class="app-title">AI Application Email Generator</h1>
                <p class="app-subtitle">Direct, professional outreach emails formatted for recruiters and hiring managers.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    has_resume = bool(st.session_state.get("resume_text", "").strip())
    if not has_resume:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📄</div>
            <div class="empty-state-title">Upload a Resume to Generate Emails</div>
            <p class="empty-state-desc">The email generator pulls key evidence from your resume.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Resume Analyzer →", type="primary"):
            st.session_state.current_page = "resume_analyzer"
            st.rerun()
        return

    resume_text = st.session_state.resume_text
    username = st.session_state.get("auth_username", "")
    profile = auth_get_profile(username) if username else {}

    default_name = profile.get("full_name") or extract_candidate_name_from_resume(resume_text) or "Your Name"
    default_jd = st.session_state.get("current_jd", "")
    default_title = extract_cover_letter_job_title(default_jd) if default_jd else "Data Analyst"
    default_company = extract_cover_letter_company(default_jd) if default_jd else ""

    st.markdown("""
    <div class="saas-card" style="margin-bottom: 1.25rem;">
        <div class="saas-card-header">✉️ Email Parameters</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        cand_name = st.text_input("Candidate Name", value=default_name, key="em_cand_name")
        job_title = st.text_input("Job Role", value=default_title, key="em_job_title")
        company = st.text_input("Company Name", value=default_company, placeholder="e.g. Google, Elsevier", key="em_company")
    with col2:
        hiring_mgr = st.text_input("Recipient / Hiring Manager (Optional)", placeholder="e.g. Hiring Team", key="em_hiring_mgr")
        col_tone, col_len = st.columns(2)
        with col_tone:
            tone = st.selectbox("Tone", ["Professional", "Confident", "Enthusiastic"], index=0, key="em_tone")
        with col_len:
            length = st.selectbox("Length", ["Standard", "Short", "Detailed"], index=0, key="em_len")

    jd_input = st.text_area(
        "Job Description Context",
        value=default_jd,
        height=140,
        placeholder="Paste target job description to highlight relevant skills in email...",
        key="em_jd_input"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("📧 Generate Application Email", type="primary", key="btn_gen_email"):
        with st.spinner("Writing personalized application email..."):
            full_email, subject, matching_skills, selected_projects, email_data = generate_application_email(
                candidate_name=cand_name,
                job_title=job_title,
                company_name=company,
                hiring_manager=hiring_mgr,
                resume_text=resume_text,
                job_description=jd_input,
                tone=tone,
                email_length=length,
                include_subject=False
            )
            st.session_state.email_subject = subject
            st.session_state.email_body = full_email
            st.session_state.email_generated = True
            st.success("Application email generated!")

    if st.session_state.get("email_generated", False) and st.session_state.get("email_body"):
        subject = st.session_state.email_subject
        body = st.session_state.email_body

        st.markdown("### 📬 Email Client Preview")
        st.markdown(f"""
        <div class="email-container">
            <div class="email-header">
                <div class="email-header-row"><strong>To:</strong> {hiring_mgr if hiring_mgr else 'recruiting@' + (company.lower().replace(' ', '') if company else 'company') + '.com'}</div>
                <div class="email-header-row"><strong>From:</strong> {profile.get('email') or (cand_name.lower().replace(' ', '.') + '@email.com')}</div>
                <div class="email-header-row"><strong>Subject:</strong> {subject}</div>
            </div>
            <div class="email-body">{body}</div>
        </div>
        """, unsafe_allow_html=True)

        full_copy_text = f"Subject: {subject}\n\n{body}"

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "⬇️ Download Email (TXT)",
                data=full_copy_text,
                file_name="Application_Email.txt",
                mime="text/plain",
                use_container_width=True
            )
        with c2:
            pdf_bytes = create_application_email_pdf(full_copy_text, job_title, company)
            if pdf_bytes:
                st.download_button(
                    "📄 Download Email (PDF)",
                    data=pdf_bytes,
                    file_name="Application_Email.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
