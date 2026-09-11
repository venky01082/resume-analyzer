import streamlit as st
from resume_parser import extract_text
from core_logic import (
    extract_name,
    extract_email,
    extract_phone,
    extract_skills,
    extract_education_details,
    extract_projects,
    extract_experience,
    extract_section,
    resume_score,
    missing_skills,
    suggestions,
)


def render_resume_analyzer():
    """
    Renders modern 4-step Resume Analyzer workspace with
    cards for personal info, skills chips, education/projects,
    score metrics, and improvement recommendations.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">📄</div>
            <div>
                <h1 class="app-title">AI Resume Analyzer</h1>
                <p class="app-subtitle">Deep parsing, ATS scoring, and intelligent career recommendations.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    has_resume = bool(st.session_state.get("resume_text", "").strip())
    current_step = 3 if has_resume else 1

    # 4-Step Visual Stepper
    st.markdown(f"""
    <div class="stepper-container">
        <div class="stepper-step {'completed' if has_resume else 'active'}">
            <div class="stepper-num">1</div>
            <span>Upload Resume</span>
        </div>
        <div style="color: #cbd5e1;">───</div>
        <div class="stepper-step {'completed' if has_resume else ''}">
            <div class="stepper-num">2</div>
            <span>AI Parsing</span>
        </div>
        <div style="color: #cbd5e1;">───</div>
        <div class="stepper-step {'active' if has_resume else ''}">
            <div class="stepper-num">3</div>
            <span>Analysis & Score</span>
        </div>
        <div style="color: #cbd5e1;">───</div>
        <div class="stepper-step">
            <div class="stepper-num">4</div>
            <span>Actionable Improvements</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Upload Card
    with st.container():
        st.markdown("""
        <div class="saas-card" style="margin-bottom: 1.5rem;">
            <div class="saas-card-header">
                <span>📤 Upload Your Resume (PDF)</span>
            </div>
            <p style="font-size: 0.88rem; color: #64748b; margin-top: -0.5rem; margin-bottom: 1rem;">
                Upload a standard text-based PDF to extract personal details, technical skills, projects, and calculate your ATS baseline score.
            </p>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload Resume PDF",
            type=["pdf"],
            label_visibility="collapsed",
            key="resume_pdf_uploader"
        )

        if uploaded_file is not None:
            try:
                with st.spinner("Extracting and analyzing resume text..."):
                    extracted_text = extract_text(uploaded_file)
                if not extracted_text.strip():
                    st.error("Unable to extract text from this PDF. Please ensure it is not a scanned image.")
                else:
                    # Save into session state for application-wide persistence
                    st.session_state.resume_text = extracted_text
                    st.session_state.resume_name = extract_name(extracted_text)
                    st.session_state.resume_email = extract_email(extracted_text)
                    st.session_state.resume_phone = extract_phone(extracted_text)
                    st.session_state.resume_skills = extract_skills(extracted_text)
                    st.session_state.resume_education = extract_education_details(extracted_text)
                    st.session_state.resume_projects = extract_projects(extracted_text)
                    st.session_state.resume_experience = extract_experience(extracted_text)
                    st.session_state.resume_certifications = extract_section(extracted_text, ["Certifications", "Certificates"])
                    
                    from core_logic import calculate_detailed_resume_health
                    from database import save_resume
                    
                    st.session_state.resume_score = resume_score(
                        extracted_text,
                        st.session_state.resume_skills,
                        st.session_state.resume_education,
                        st.session_state.resume_projects,
                        st.session_state.resume_experience,
                        st.session_state.resume_certifications
                    )
                    
                    # Persist into database for multi-resume management
                    username = st.session_state.get("auth_username", "venky")
                    save_resume(
                        user_id=username,
                        title=uploaded_file.name.replace(".pdf", ""),
                        filename=uploaded_file.name,
                        text=extracted_text,
                        score=st.session_state.resume_score,
                        parsed_data={
                            "name": st.session_state.resume_name,
                            "email": st.session_state.resume_email,
                            "phone": st.session_state.resume_phone,
                            "skills": st.session_state.resume_skills,
                            "education": st.session_state.resume_education,
                            "projects": st.session_state.resume_projects,
                            "experience": st.session_state.resume_experience,
                            "certifications": st.session_state.resume_certifications,
                        },
                        set_default=True
                    )
                    st.success("✅ Resume successfully parsed and saved to your profile!")
            except Exception as e:
                st.error(f"Error reading PDF: {e}")

    # If no resume yet, show attractive empty state guide
    if not st.session_state.get("resume_text", "").strip():
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📄</div>
            <div class="empty-state-title">No Resume Uploaded Yet</div>
            <p class="empty-state-desc">
                Drag and drop your PDF resume above to view skill tags, structure breakdowns, baseline ATS scoring, and targeted improvement suggestions.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Extracted Data Display
    r_text = st.session_state.resume_text
    r_name = st.session_state.get("resume_name", "Not Found")
    r_email = st.session_state.get("resume_email", "Not Found")
    r_phone = st.session_state.get("resume_phone", "Not Found")
    r_skills = st.session_state.get("resume_skills", [])
    r_edu = st.session_state.get("resume_education", [])
    r_proj = st.session_state.get("resume_projects", [])
    r_exp = st.session_state.get("resume_experience", [])
    r_certs = st.session_state.get("resume_certifications", [])
    r_score = st.session_state.get("resume_score", 0)

    # Top Results Row: Score Gauge & Personal Details
    col_score, col_info = st.columns([1, 2])

    with col_score:
        status_label = "Strong Resume" if r_score >= 80 else ("Good Baseline" if r_score >= 60 else "Needs Improvement")
        status_color = "#10b981" if r_score >= 80 else ("#f59e0b" if r_score >= 60 else "#ef4444")
        st.markdown(f"""
        <div class="saas-card" style="text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 13px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 10px;">Overall Resume Score</div>
            <div class="score-circle">
                <div class="score-circle-num">{r_score}</div>
                <div class="score-circle-label">/ 100</div>
            </div>
            <div style="margin-top: 14px; font-weight: 700; font-size: 14px; color: {status_color};">
                ● {status_label}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        st.markdown(f"""
        <div class="saas-card" style="height: 100%;">
            <div class="saas-card-header">👤 Contact & Identification</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
                <div>
                    <div style="font-size: 12px; color: #64748b; font-weight: 600;">FULL NAME</div>
                    <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-top: 2px;">{r_name}</div>
                </div>
                <div>
                    <div style="font-size: 12px; color: #64748b; font-weight: 600;">EMAIL ADDRESS</div>
                    <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-top: 2px;">{r_email}</div>
                </div>
                <div>
                    <div style="font-size: 12px; color: #64748b; font-weight: 600;">PHONE NUMBER</div>
                    <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-top: 2px;">{r_phone}</div>
                </div>
                <div>
                    <div style="font-size: 12px; color: #64748b; font-weight: 600;">DETECTED SKILLS COUNT</div>
                    <div style="font-size: 15px; font-weight: 700; color: #4f46e5; margin-top: 2px;">{len(r_skills)} Verified Skills</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Deep Resume Health Analysis
    from core_logic import calculate_detailed_resume_health
    health = calculate_detailed_resume_health(r_text, r_skills, r_edu, r_proj, r_exp, r_certs)

    st.markdown("### 🏥 Resume Health & Quality Audit")
    h_col1, h_col2 = st.columns([1, 2])

    with h_col1:
        st.markdown(f"""
        <div class="saas-card" style="text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 13px; font-weight: 700; color: #64748b; text-transform: uppercase;">Composite Health Index</div>
            <div class="score-circle" style="margin: 12px auto;">
                <div class="score-circle-num">{health['overall_health']}</div>
                <div class="score-circle-label">HEALTH</div>
            </div>
            <div style="font-size: 12px; color: {'#10b981' if health['overall_health'] >= 75 else '#f59e0b'}; font-weight: 700;">
                {'● Production Ready' if health['overall_health'] >= 80 else '● Optimization Recommended'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with h_col2:
        st.markdown('<div class="saas-card">', unsafe_allow_html=True)
        st.markdown("<div style='font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 8px;'>Component Strength Breakdown</div>", unsafe_allow_html=True)
        st.write(f"**Skills Coverage:** {health['skills_score']}%")
        st.progress(health['skills_score'] / 100)
        st.write(f"**ATS Parseability:** {health['ats_score']}%")
        st.progress(health['ats_score'] / 100)
        st.write(f"**Experience & Projects Depth:** {max(health['experience_score'], health['projects_score'])}%")
        st.progress(max(health['experience_score'], health['projects_score']) / 100)
        st.write(f"**Formatting & Layout:** {health['formatting_score']}%")
        st.progress(health['formatting_score'] / 100)
        st.write(f"**Completeness & Links:** {health['completeness_score']}%")
        st.progress(health['completeness_score'] / 100)
        st.markdown('</div>', unsafe_allow_html=True)

    # Detailed Quality Audit Row
    st.markdown("#### 🔬 Detailed Quality Audit")
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        weak_count = len(health['weak_verbs'])
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Action Verbs</div>
            <div class="stat-value" style="font-size: 1.15rem; color: {'#dc2626' if weak_count > 0 else '#10b981'};">
                {weak_count} Weak Detected
            </div>
            <div class="stat-subtext-neutral">{len(health['strong_verbs'])} impact verbs found</div>
        </div>
        """, unsafe_allow_html=True)
    with d2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Quantified Results</div>
            <div class="stat-value" style="font-size: 1.15rem; color: {'#10b981' if health['has_metrics'] else '#f59e0b'};">
                {'Metrics Present ✅' if health['has_metrics'] else 'Missing Metrics ⚠️'}
            </div>
            <div class="stat-subtext-neutral">Numbers, % or KPIs</div>
        </div>
        """, unsafe_allow_html=True)
    with d3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Paragraph Density</div>
            <div class="stat-value" style="font-size: 1.15rem; color: {'#f59e0b' if health['has_long_paragraphs'] else '#10b981'};">
                {'Dense Blocks ⚠️' if health['has_long_paragraphs'] else 'Clean Bullets ✅'}
            </div>
            <div class="stat-subtext-neutral">Concise 1-2 line points</div>
        </div>
        """, unsafe_allow_html=True)
    with d4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Professional Links</div>
            <div class="stat-value" style="font-size: 1.15rem; color: {'#f59e0b' if health['missing_links'] else '#10b981'};">
                {'Missing Links ⚠️' if health['missing_links'] else 'Links Complete ✅'}
            </div>
            <div class="stat-subtext-neutral">GitHub & LinkedIn</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Technical Skills Chips Card
    st.markdown(f"""
    <div class="saas-card">
        <div class="saas-card-header">
            <span>💻 Detected Technical Skills ({len(r_skills)})</span>
        </div>
        <p style="font-size: 0.85rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 0.75rem;">
            Recognized against standard industry databases:
        </p>
        <div class="chip-container">
            {''.join([f'<span class="skill-chip">✓ {skill}</span>' for skill in r_skills]) if r_skills else '<span style="color: #64748b;">No technical skills detected.</span>'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Education & Projects Side by Side
    col_edu, col_proj = st.columns(2)

    with col_edu:
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">🎓 Education Qualifications</div>
        """, unsafe_allow_html=True)
        if r_edu:
            for item in r_edu:
                st.markdown(f"""
                <div style="padding: 8px 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 6px; font-size: 13px; color: #1e293b;">
                    🏛️ {item}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No formal education section identified.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_proj:
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">📁 Projects Recognized</div>
        """, unsafe_allow_html=True)
        if r_proj:
            for item in r_proj:
                st.markdown(f"""
                <div style="padding: 8px 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 6px; font-size: 13px; color: #1e293b;">
                    💡 {item}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No projects section identified.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Experience & Certifications Row
    col_exp, col_cert = st.columns(2)

    with col_exp:
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">💼 Work & Practical Experience</div>
        """, unsafe_allow_html=True)
        if r_exp:
            for item in r_exp:
                st.markdown(f"""
                <div style="padding: 8px 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 6px; font-size: 13px; color: #1e293b;">
                    💼 {item}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No formal experience section identified.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_cert:
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">📜 Certifications & Achievements</div>
        """, unsafe_allow_html=True)
        if r_certs:
            for item in r_certs:
                st.markdown(f"""
                <div style="padding: 8px 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 6px; font-size: 13px; color: #1e293b;">
                    🏆 {item}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No certifications detected.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Missing Recommended Skills & Improvement Suggestions
    st.markdown("### 💡 Career Optimization Insights")
    col_missing, col_sugg = st.columns(2)

    with col_missing:
        rec_missing = missing_skills(r_skills)
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">⚠️ Top Industry In-Demand Skills Missing</div>
            <p style="font-size: 0.85rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 0.75rem;">
                Skills frequently requested in tech roles that were not found in your resume:
            </p>
        """, unsafe_allow_html=True)
        if rec_missing:
            st.markdown(f"""
            <div class="chip-container">
                {''.join([f'<span class="skill-chip skill-chip-missing">+ {skill}</span>' for skill in rec_missing[:12]])}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success("🎉 You have strong coverage across all standard tech skills!")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_sugg:
        sugg_list = suggestions(r_score, r_skills, r_proj, r_exp, r_certs)
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">🚀 Targeted Action Items</div>
        """, unsafe_allow_html=True)
        for s in sugg_list:
            st.markdown(f"""
            <div style="padding: 6px 0; display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: #334155;">
                <span style="color: #4f46e5;">•</span>
                <span>{s}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Extracted Text Expander
    with st.expander("🔍 View Raw Extracted Resume Content"):
        st.text_area("Extracted Resume Text", r_text, height=300, key="raw_resume_text_area")
