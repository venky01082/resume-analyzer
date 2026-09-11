import streamlit as st
from core_logic import (
    analyze_ats_keywords,
    analyze_job_title,
    calculate_semantic_similarity,
    calculate_semantic_keyword_score,
    calculate_title_relevance_score,
    calculate_combined_semantic_score,
    get_semantic_match_label,
    build_semantic_match_explanation,
    compare_skills,
    calculate_match_score,
    extract_job_skills,
    extract_skills,
    add_application,
)
from database.resumes import get_resumes


def render_job_matching():
    """
    Renders dedicated Job Matching Workspace with
    dual-engine analysis (Keyword-based + Sentence Transformers Semantic Matching),
    multi-resume selector, and structured Why You Match / Why You May Not Match / What to Improve breakdown.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">🧠</div>
            <div>
                <h1 class="app-title">AI Job Matching Engine</h1>
                <p class="app-subtitle">Deep contextual comparison between your resume and a target job specification.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    username = st.session_state.get("auth_username", "venky")
    saved_resumes = get_resumes(username)

    # Resume Selection & Availability
    has_active_resume = bool(st.session_state.get("resume_text", "").strip())
    
    if not has_active_resume and not saved_resumes:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📄</div>
            <div class="empty-state-title">No Resume Available for Matching</div>
            <p class="empty-state-desc">Please upload your resume to begin semantic and keyword matching.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Upload Resume Now →", type="primary"):
            st.session_state.current_page = "resume_analyzer"
            st.rerun()
        return

    # Multi-Resume Selector Bar
    if saved_resumes:
        st.markdown("""
        <div class="saas-card" style="padding: 1rem 1.25rem; margin-bottom: 1rem;">
            <div style="font-size: 13px; font-weight: 700; color: #0f172a; margin-bottom: 0.5rem;">📄 SELECT RESUME FOR MATCHING</div>
        """, unsafe_allow_html=True)
        resume_titles = [f"{r.get('title', 'Untitled')} ({r.get('version', 'v1')})" for r in saved_resumes]
        selected_r_idx = st.selectbox(
            "Select Resume Version",
            range(len(resume_titles)),
            format_func=lambda i: resume_titles[i],
            key="matching_resume_picker",
            label_visibility="collapsed"
        )
        picked_rec = saved_resumes[selected_r_idx]
        resume_text = picked_rec.get("content", "")
        resume_skills = picked_rec.get("skills", [])
        if not resume_skills and resume_text:
            resume_skills = extract_skills(resume_text)
        st.markdown(f"<div style='font-size: 12px; color: #64748b;'>Active: <strong>{picked_rec.get('title')}</strong> ({len(resume_skills)} skills identified)</div></div>", unsafe_allow_html=True)
    else:
        resume_text = st.session_state.resume_text
        resume_skills = st.session_state.get("resume_skills", [])

    # Process Flowchart Visual
    st.markdown("""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem; text-align: center;">
        <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin-bottom: 10px;">DUAL-ENGINE MATCHING PIPELINE</div>
        <div style="display: flex; justify-content: center; align-items: center; gap: 12px; flex-wrap: wrap;">
            <span style="background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; font-size: 13px; font-weight: 700; padding: 6px 14px; border-radius: 8px;">📄 Resume Text</span>
            <span style="color: #94a3b8; font-weight: 700;">➔</span>
            <span style="background: #eef2ff; color: #4338ca; border: 1px solid #c7d2fe; font-size: 13px; font-weight: 700; padding: 6px 14px; border-radius: 8px;">🧠 Semantic & Keyword Analysis</span>
            <span style="color: #94a3b8; font-weight: 700;">➔</span>
            <span style="background: #f8fafc; color: #334155; border: 1px solid #e2e8f0; font-size: 13px; font-weight: 700; padding: 6px 14px; border-radius: 8px;">📋 Job Description</span>
            <span style="color: #94a3b8; font-weight: 700;">➔</span>
            <span style="background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; font-size: 13px; font-weight: 700; padding: 6px 14px; border-radius: 8px;">🎯 Match Fit & Gap Analysis</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    default_jd = st.session_state.get("current_jd", "")
    st.markdown("""
    <div class="saas-card">
        <div class="saas-card-header">📋 Target Job Description</div>
        <p style="font-size: 0.85rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 0.75rem;">
            Paste target job description to compute semantic alignment, technical skill overlap, and custom improvement advice:
        </p>
    </div>
    """, unsafe_allow_html=True)

    target_jd = st.text_area(
        "Job Description Input",
        value=default_jd,
        height=180,
        placeholder="Paste full job description including requirements, responsibilities, and qualifications...",
        key="matching_jd_input",
        label_visibility="collapsed"
    )

    if st.button("🧠 Compute AI Match Analysis", type="primary", key="btn_run_job_matching"):
        if not target_jd.strip():
            st.warning("Please paste a job description first.")
        else:
            st.session_state.current_jd = target_jd
            st.session_state.matching_computed = True

    if not st.session_state.get("matching_computed", False) or not target_jd.strip():
        st.info("👆 Enter a job description and click 'Compute AI Match Analysis' to view metrics.")
        return

    # Run Semantic Model & Keyword Matching
    with st.spinner("Computing semantic vectors and matching keyword overlaps..."):
        # 1. Keyword check
        job_skills = extract_job_skills(target_jd)
        matching_skills, missing_skills = compare_skills(resume_skills, job_skills)
        basic_score = calculate_match_score(matching_skills, job_skills)
        
        # 2. Semantic Analysis
        keyword_data = analyze_ats_keywords(resume_text, target_jd)
        keyword_score = calculate_semantic_keyword_score(resume_text, target_jd)
        title_score = calculate_title_relevance_score(resume_text, target_jd)

        semantic_sim = 0.0
        try:
            semantic_sim = calculate_semantic_similarity(resume_text, target_jd)
            combined_score = calculate_combined_semantic_score(semantic_sim, keyword_score, title_score)
        except Exception:
            semantic_sim = keyword_score
            combined_score = round(keyword_score * 0.75 + title_score * 0.25, 1)

        label_title, label_desc = get_semantic_match_label(combined_score)
        explanation = build_semantic_match_explanation(semantic_sim, keyword_score, title_score, keyword_data)

    # Top KPI Banner
    col_score_card, col_breakdown = st.columns([1, 2])

    with col_score_card:
        score_color = "#10b981" if combined_score >= 75 else ("#4f46e5" if combined_score >= 50 else "#ef4444")
        st.markdown(f"""
        <div class="saas-card" style="text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 13px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 10px;">Overall Match Fit</div>
            <div class="score-circle">
                <div class="score-circle-num">{int(combined_score)}%</div>
                <div class="score-circle-label">MATCH</div>
            </div>
            <div style="margin-top: 14px; font-weight: 700; font-size: 14px; color: {score_color};">
                {label_title}
            </div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">{label_desc}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_breakdown:
        st.markdown(f"""
        <div class="saas-card" style="height: 100%;">
            <div class="saas-card-header">📊 Multimodal Match Breakdown</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-size: 13px; margin-top: 0.5rem;">
                <div style="background: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <div style="color: #64748b; font-size: 11px; font-weight: 600;">SEMANTIC SIMILARITY</div>
                    <div style="font-size: 18px; font-weight: 800; color: #4f46e5;">{semantic_sim}%</div>
                    <div style="font-size: 11px; color: #94a3b8;">Contextual domain alignment</div>
                </div>
                <div style="background: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <div style="color: #64748b; font-size: 11px; font-weight: 600;">KEYWORD OVERLAP</div>
                    <div style="font-size: 18px; font-weight: 800; color: #10b981;">{keyword_score}%</div>
                    <div style="font-size: 11px; color: #94a3b8;">Exact technical keyword hits</div>
                </div>
                <div style="background: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <div style="color: #64748b; font-size: 11px; font-weight: 600;">TITLE RELEVANCE</div>
                    <div style="font-size: 18px; font-weight: 800; color: #0284c7;">{title_score}%</div>
                    <div style="font-size: 11px; color: #94a3b8;">Target role compatibility</div>
                </div>
                <div style="background: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <div style="color: #64748b; font-size: 11px; font-weight: 600;">SKILLS COVERAGE</div>
                    <div style="font-size: 18px; font-weight: 800; color: #7c3aed;">{basic_score}%</div>
                    <div style="font-size: 11px; color: #94a3b8;">{len(matching_skills)} of {len(job_skills)} required skills</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 3-PILLAR DEEP DIVE: WHY YOU MATCH / WHY YOU MAY NOT MATCH / WHAT TO IMPROVE
    st.markdown("### 🔍 Comprehensive Fit Analysis")
    col_why_match, col_why_not, col_improve = st.columns(3)

    # Pillar 1: Why You Match
    with col_why_match:
        st.markdown("""
        <div class="saas-card" style="height: 100%; border-top: 3px solid #10b981;">
            <div class="saas-card-header" style="color: #065f46;">🎯 WHY YOU MATCH</div>
        """, unsafe_allow_html=True)
        if matching_skills:
            st.markdown(f"**{len(matching_skills)} Core Technical Overlaps:**")
            st.markdown(f"""
            <div class="chip-container" style="margin-bottom: 12px;">
                {''.join([f'<span class="skill-chip skill-chip-match">✓ {s}</span>' for s in matching_skills[:12]])}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='font-size: 13px; color: #64748b;'>No direct technical skills overlap identified.</p>", unsafe_allow_html=True)

        if semantic_sim >= 60:
            st.markdown(f"<div style='font-size: 12.5px; color: #334155; margin-bottom: 6px;'>• Strong contextual alignment ({semantic_sim}%) indicates your background is in a compatible domain.</div>", unsafe_allow_html=True)
        if title_score >= 60:
            st.markdown(f"<div style='font-size: 12.5px; color: #334155; margin-bottom: 6px;'>• Your resume title matches the target job family ({title_score}%).</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Pillar 2: Why You May Not Match
    with col_why_not:
        st.markdown("""
        <div class="saas-card" style="height: 100%; border-top: 3px solid #f59e0b;">
            <div class="saas-card-header" style="color: #b45309;">⚠️ WHY YOU MAY NOT MATCH</div>
        """, unsafe_allow_html=True)
        if missing_skills:
            st.markdown(f"**{len(missing_skills)} Missing Target Skills:**")
            st.markdown(f"""
            <div class="chip-container" style="margin-bottom: 12px;">
                {''.join([f'<span class="skill-chip skill-chip-missing">+ {s}</span>' for s in missing_skills[:12]])}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='font-size: 13px; color: #10b981;'>🎉 All detected job keywords found in your resume!</p>", unsafe_allow_html=True)

        if title_score < 50:
            st.markdown("<div style='font-size: 12.5px; color: #92400e; margin-bottom: 6px;'>• Title divergence: The target job title isn't prominent in your recent work history or headline.</div>", unsafe_allow_html=True)
        if keyword_score < 50:
            st.markdown("<div style='font-size: 12.5px; color: #92400e; margin-bottom: 6px;'>• Low keyword density: Several high-frequency recruiter search terms are missing.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Pillar 3: What to Improve
    with col_improve:
        st.markdown("""
        <div class="saas-card" style="height: 100%; border-top: 3px solid #4f46e5;">
            <div class="saas-card-header" style="color: #4338ca;">🚀 WHAT TO IMPROVE</div>
        """, unsafe_allow_html=True)
        suggestions = []
        if missing_skills:
            top_miss = ", ".join(missing_skills[:3])
            suggestions.append(f"If you possess experience with **{top_miss}**, explicitly include them in your skills section.")
        if title_score < 60:
            suggestions.append("Align your resume headline with the target role (e.g. 'Software Engineer | Python & Cloud').")
        suggestions.append("Incorporate verifiable metrics (% improvement, scale, users served) in project bullet points.")
        suggestions.append("Do not fabricate experience — reframe your existing transferable projects towards this job's needs.")

        for sug in suggestions:
            st.markdown(f"<div style='font-size: 12.5px; color: #334155; margin-bottom: 8px;'>• {sug}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Next Action Bar
    st.markdown("""
    <div class="saas-card">
        <div class="saas-card-header">⚡ Next Recommended Actions</div>
        <p style="font-size: 0.85rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 1rem;">
            Turn these match insights into actionable application assets:
        </p>
    """, unsafe_allow_html=True)
    act_col1, act_col2, act_col3, act_col4 = st.columns(4)

    with act_col1:
        if st.button("✨ Tailor Resume for this Role", use_container_width=True, type="primary"):
            st.session_state.current_jd = target_jd
            st.session_state.current_page = "resume_tailoring"
            st.rerun()

    with act_col2:
        if st.button("✍️ Generate Custom Cover Letter", use_container_width=True):
            st.session_state.current_jd = target_jd
            st.session_state.current_page = "cover_letter"
            st.rerun()

    with act_col3:
        if st.button("📌 Track in Application Pipeline", use_container_width=True):
            title_guess = target_jd.split("\n")[0][:40] if target_jd else "Target Role"
            add_application(
                title=title_guess.strip(),
                company="Target Company",
                location="Remote / Flexible",
                score=int(combined_score),
                status="Saved",
                notes="Created via Job Matching Engine."
            )
            st.success("Added to Application Tracker as 'Saved'!")

    with act_col4:
        if st.button("🎙️ Practice for this Job", use_container_width=True):
            title_guess = target_jd.split("\n")[0][:40] if target_jd else "Target Role"
            st.session_state.interview_selected_job = {
                "title": title_guess.strip(),
                "company": "Target Company",
                "description": target_jd,
                "skills": job_skills,
                "matching_skills": matching_skills,
            }
            st.session_state.current_page = "mock_interview"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Download Match Report
    report = [
        "AI JOB MATCHING REPORT",
        "=" * 40,
        f"Overall Match Score: {combined_score}% ({label_title})",
        f"Semantic Similarity: {semantic_sim}%",
        f"Keyword Overlap Score: {keyword_score}%",
        f"Title Relevance Score: {title_score}%",
        f"Skills Coverage: {basic_score}%",
        "",
        "Matching Skills: " + (", ".join(matching_skills) if matching_skills else "None"),
        "Missing Skills: " + (", ".join(missing_skills) if missing_skills else "None"),
        "",
        "AI Explanation:",
        "\n".join(f"- {e}" for e in explanation)
    ]
    st.download_button(
        label="⬇️ Download Match Report (TXT)",
        data="\n".join(report),
        file_name="job_match_report.txt",
        mime="text/plain",
        key="btn_download_match_report"
    )

