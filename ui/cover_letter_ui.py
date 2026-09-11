import streamlit as st
from core_logic import (
    generate_cover_letter,
    create_cover_letter_pdf,
    extract_candidate_name_from_resume,
    extract_cover_letter_job_title,
    extract_cover_letter_company,
    auth_get_profile,
)


def render_cover_letter():
    """
    Renders clean, document-style AI Cover Letter Generator.
    Pre-fills verified details, supports custom tone/length,
    and exports to TXT and PDF.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">✍️</div>
            <div>
                <h1 class="app-title">AI Cover Letter Generator</h1>
                <p class="app-subtitle">Craft compelling, role-tailored cover letters grounded in your actual achievements.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    has_resume = bool(st.session_state.get("resume_text", "").strip())
    if not has_resume:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📄</div>
            <div class="empty-state-title">Upload a Resume to Generate Cover Letters</div>
            <p class="empty-state-desc">The generator links your real skills and projects to target company requirements.</p>
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
        <div class="saas-card-header">📝 Application Details</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        cand_name = st.text_input("Your Full Name", value=default_name, key="cl_cand_name")
        job_title = st.text_input("Target Job Title", value=default_title, key="cl_job_title")
        company = st.text_input("Company Name", value=default_company, placeholder="e.g. Microsoft, Amazon", key="cl_company")
    with col2:
        hiring_mgr = st.text_input("Hiring Manager (Optional)", placeholder="e.g. Sarah Jenkins", key="cl_hiring_mgr")
        col_tone, col_len = st.columns(2)
        with col_tone:
            tone = st.selectbox("Tone", ["Professional", "Confident", "Enthusiastic"], index=0, key="cl_tone")
        with col_len:
            length = st.selectbox("Length", ["Medium", "Short", "Long"], index=0, key="cl_length")

    jd_input = st.text_area(
        "Job Description Requirements",
        value=default_jd,
        height=140,
        placeholder="Paste target job description to emphasize matching skills...",
        key="cl_jd_input"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("✍️ Generate Cover Letter", type="primary", key="btn_gen_cover_letter"):
        with st.spinner("Generating personalized cover letter..."):
            letter, matching_skills, selected_projects = generate_cover_letter(
                candidate_name=cand_name,
                job_title=job_title,
                company_name=company,
                hiring_manager=hiring_mgr,
                resume_text=resume_text,
                job_description=jd_input,
                tone=tone,
                length=length
            )
            st.session_state.cover_letter_text = letter
            st.session_state.cl_matching = matching_skills
            st.session_state.cl_projects = selected_projects
            st.session_state.cl_generated = True
            st.success("Cover letter generated successfully!")

    if st.session_state.get("cl_generated", False) and st.session_state.get("cover_letter_text"):
        letter_text = st.session_state.cover_letter_text
        
        st.markdown("### 📄 Document Preview")
        st.markdown(f"""
        <div class="document-sheet">
{letter_text}
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "⬇️ Download Cover Letter (TXT)",
                data=letter_text,
                file_name=f"Cover_Letter_{job_title.replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with c2:
            pdf_bytes = create_cover_letter_pdf(letter_text, cand_name, job_title, company)
            if pdf_bytes:
                st.download_button(
                    "📄 Download Cover Letter (PDF)",
                    data=pdf_bytes,
                    file_name=f"Cover_Letter_{job_title.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
