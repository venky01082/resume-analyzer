import streamlit as st
from core_logic import (
    analyze_ats_keywords,
    analyze_skill_categories,
    analyze_experience,
    analyze_projects,
    analyze_achievements,
    analyze_action_verbs,
    analyze_structure,
    analyze_resume_length,
    analyze_keyword_stuffing,
    analyze_job_title,
    calculate_advanced_ats_score,
    generate_advanced_ats_recommendations,
)


def render_ats_analyzer():
    """
    Renders dedicated ATS Compatibility Workspace with
    compatibility gauge, keyword coverage, breakdown by category,
    and downloadable audit report.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">🎯</div>
            <div>
                <h1 class="app-title">Advanced ATS Analyzer</h1>
                <p class="app-subtitle">Simulate Applicant Tracking Systems to test keyword density and structure.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    has_resume = bool(st.session_state.get("resume_text", "").strip())
    if not has_resume:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📄</div>
            <div class="empty-state-title">Please Upload a Resume First</div>
            <p class="empty-state-desc">
                The ATS Analyzer compares your actual resume text against target job descriptions.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Upload Resume in Analyzer →", type="primary"):
            st.session_state.current_page = "resume_analyzer"
            st.rerun()
        return

    from database import get_resumes
    username = st.session_state.get("auth_username", "venky")
    saved_resumes = get_resumes(username)

    if saved_resumes and len(saved_resumes) > 1:
        titles = [r.get("title", "Resume") for r in saved_resumes]
        active_idx = 0
        curr_id = st.session_state.get("active_resume_id")
        for i, r in enumerate(saved_resumes):
            if r.get("resume_id") == curr_id:
                active_idx = i
                break
        
        sel_res_idx = st.selectbox("📄 Select Resume Profile for ATS Audit", range(len(titles)), format_func=lambda i: titles[i], index=active_idx, key="ats_resume_profile_select")
        selected_res = saved_resumes[sel_res_idx]
        resume_text = selected_res.get("text", "")
        parsed = selected_res.get("parsed_data", {})
        experience = parsed.get("experience", [])
        projects = parsed.get("projects", [])
        education = parsed.get("education", [])
        certifications = parsed.get("certifications", [])
    else:
        resume_text = st.session_state.resume_text
        experience = st.session_state.get("resume_experience", [])
        projects = st.session_state.get("resume_projects", [])
        education = st.session_state.get("resume_education", [])
        certifications = st.session_state.get("resume_certifications", [])

    st.markdown("""
    <div class="saas-card">
        <div class="saas-card-header">📋 Target Job Description</div>
        <p style="font-size: 0.85rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 0.75rem;">
            Paste the job description you want to optimize your resume against:
        </p>
    </div>
    """, unsafe_allow_html=True)

    default_jd = st.session_state.get("current_jd", "")
    target_jd = st.text_area(
        "Target Job Description",
        value=default_jd,
        height=200,
        placeholder="""Senior Data Analyst / ML Engineer
Requirements:
- Strong experience with Python, SQL, and Power BI
- Familiarity with Machine Learning, Pandas, NumPy, and Scikit-learn
- Experience building dashboards, ETL pipelines, and working with cloud (AWS/Azure)
- Excellent analytical, problem-solving, and communication skills""",
        key="ats_target_jd_input",
        label_visibility="collapsed"
    )

    if st.button("🎯 Run ATS Audit", type="primary", key="run_ats_audit_btn"):
        if not target_jd.strip():
            st.warning("Please paste a target job description to run the ATS audit.")
        else:
            st.session_state.current_jd = target_jd
            st.session_state.ats_audited = True

    if not st.session_state.get("ats_audited", False) or not target_jd.strip():
        st.info("👆 Enter a job description above and click 'Run ATS Audit' to generate your detailed report.")
        return

    # Run analyzers
    with st.spinner("Analyzing ATS compatibility against job description..."):
        keyword_data = analyze_ats_keywords(resume_text, target_jd)
        skill_data = analyze_skill_categories(resume_text, target_jd)
        exp_data = analyze_experience(resume_text, experience)
        proj_data = analyze_projects(resume_text, projects)
        achieve_data = analyze_achievements(resume_text)
        action_data = analyze_action_verbs(resume_text)
        structure_data = analyze_structure(resume_text, education, projects, experience, certifications)
        length_data = analyze_resume_length(resume_text)
        stuffing_data = analyze_keyword_stuffing(resume_text)
        title_data = analyze_job_title(resume_text, target_jd)

        final_ats_score = calculate_advanced_ats_score(
            keyword_data["score"],
            skill_data["score"],
            exp_data["score"],
            proj_data["score"],
            achieve_data["score"],
            5 if education else 0,
            action_data["score"],
            structure_data["score"],
            title_data["score"]
        )

        recommendations = generate_advanced_ats_recommendations(
            keyword_data, exp_data, proj_data, achieve_data,
            action_data, structure_data, length_data, stuffing_data, title_data
        )

    # Top ATS Score Widget
    score_status = "Excellent Compatibility" if final_ats_score >= 80 else ("Good Baseline" if final_ats_score >= 60 else "Low Match")
    score_color = "#10b981" if final_ats_score >= 80 else ("#f59e0b" if final_ats_score >= 60 else "#ef4444")

    col_gauge, col_summary = st.columns([1, 2])
    with col_gauge:
        st.markdown(f"""
        <div class="saas-card" style="text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 13px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 10px;">ATS Compatibility</div>
            <div class="score-circle">
                <div class="score-circle-num">{final_ats_score}%</div>
                <div class="score-circle-label">MATCH</div>
            </div>
            <div style="margin-top: 14px; font-weight: 700; font-size: 14px; color: {score_color};">
                ● {score_status}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_summary:
        st.markdown(f"""
        <div class="saas-card" style="height: 100%;">
            <div class="saas-card-header">📊 Section Score Breakdown</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; font-size: 13px;">
                <div><strong>Keywords Match:</strong> {keyword_data['score']}/30</div>
                <div><strong>Technical Skills:</strong> {skill_data['score']}/20</div>
                <div><strong>Experience Relevance:</strong> {exp_data['score']}/15</div>
                <div><strong>Projects Depth:</strong> {proj_data['score']}/10</div>
                <div><strong>Measurable Metrics:</strong> {achieve_data['score']}/10</div>
                <div><strong>Action Verbs:</strong> {action_data['score']}/5</div>
                <div><strong>Resume Structure:</strong> {structure_data['score']}/5</div>
                <div><strong>Education Section:</strong> {'5/5' if education else '0/5'}</div>
            </div>
            <div style="margin-top: 12px; font-size: 12px; color: #64748b;">
                <strong>Title Alignment:</strong> {title_data['message']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Keywords Grid: Matching vs Missing
    col_matching, col_missing = st.columns(2)

    with col_matching:
        st.markdown(f"""
        <div class="saas-card">
            <div class="saas-card-header">✅ Strong Areas / Matching Keywords ({len(keyword_data['matching'])})</div>
            <p style="font-size: 0.85rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 0.75rem;">
                Keywords from the job description verified on your resume:
            </p>
            <div class="chip-container">
                {''.join([f'<span class="skill-chip skill-chip-match">✓ {k}</span>' for k in keyword_data['matching']]) if keyword_data['matching'] else '<span style="color: #64748b;">No matching keywords found.</span>'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_missing:
        core_groups = ["Programming", "Data", "AI/ML", "Cloud/DevOps"]
        critical_missing = [k for k in keyword_data['missing'] if any(k in terms for grp, terms in keyword_data.get('groups', {}).items() if grp in core_groups)]
        general_missing = [k for k in keyword_data['missing'] if k not in critical_missing]

        st.markdown(f"""
        <div class="saas-card">
            <div class="saas-card-header">❌ Missing Target Keywords ({len(keyword_data['missing'])})</div>
            <p style="font-size: 0.85rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 0.75rem;">
                Target keywords from this JD that you should consider integrating:
            </p>
        """, unsafe_allow_html=True)
        
        if critical_missing:
            st.markdown("<div style='font-size: 11px; font-weight: 700; color: #dc2626; text-transform: uppercase; margin-bottom: 4px;'>⚠️ Critical Core Requirements</div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="chip-container">
                {''.join([f'<span class="skill-chip skill-chip-missing" style="border-color: #f87171; font-weight: 700;">★ {k}</span>' for k in critical_missing])}
            </div>
            """, unsafe_allow_html=True)

        if general_missing:
            st.markdown("<div style='font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-top: 8px; margin-bottom: 4px;'>Secondary Keywords</div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="chip-container">
                {''.join([f'<span class="skill-chip skill-chip-category">+ {k}</span>' for k in general_missing])}
            </div>
            """, unsafe_allow_html=True)
            
        if not keyword_data['missing']:
            st.markdown('<span style="color: #10b981; font-weight: 600;">🎉 All detected job keywords are present on your resume!</span>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Actionable Recommendations
    st.markdown("""
    <div class="saas-card">
        <div class="saas-card-header">📌 Targeted ATS Recommendations</div>
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; font-size: 12px; color: #166534;">
            💡 <strong>Ethical Optimization Rule:</strong> Only mention missing keywords or competencies if you genuinely have practical experience with them. Do not fabricate credentials.
        </div>
    """, unsafe_allow_html=True)
    for rec in recommendations:
        st.markdown(f"""
        <div style="padding: 6px 0; display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: #334155;">
            <span style="color: #4f46e5;">•</span>
            <span>{rec}</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Report Download Button
    report_lines = [
        "ADVANCED ATS AUDIT REPORT",
        "=" * 40,
        f"Overall Compatibility Score: {final_ats_score}/100",
        f"Keywords Score: {keyword_data['score']}/30",
        f"Skills Score: {skill_data['score']}/20",
        f"Experience Score: {exp_data['score']}/15",
        f"Projects Score: {proj_data['score']}/10",
        f"Achievements Score: {achieve_data['score']}/10",
        "",
        f"Matching Keywords ({len(keyword_data['matching'])}):",
        ", ".join(keyword_data["matching"]) if keyword_data["matching"] else "None",
        "",
        f"Missing Keywords ({len(keyword_data['missing'])}):",
        ", ".join(keyword_data["missing"]) if keyword_data["missing"] else "None",
        "",
        "Recommendations:",
        "\n".join(f"- {r}" for r in recommendations)
    ]
    st.download_button(
        label="⬇️ Download ATS Audit Report (TXT)",
        data="\n".join(report_lines),
        file_name="ats_audit_report.txt",
        mime="text/plain",
        key="download_ats_report_btn"
    )
