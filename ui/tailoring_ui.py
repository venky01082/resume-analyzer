import streamlit as st
from core_logic import (
    build_tailored_summary,
    get_tailoring_skill_recommendations,
    get_tailoring_project_recommendations,
    generate_tailoring_recommendations,
    create_restored_tailored_resume_pdf,
    extract_section,
    extract_education_details,
    extract_skills,
)
from database.resumes import get_resumes, create_resume


def render_resume_tailoring():
    """
    Renders AI Resume Tailoring workspace with
    multi-resume selection, tabbed comparison (Original vs Tailored vs Recommendations),
    library persistence, and PDF/TXT downloads.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">✨</div>
            <div>
                <h1 class="app-title">AI Resume Tailoring Workspace</h1>
                <p class="app-subtitle">Adapt your resume language to a specific job description without falsifying experience.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    username = st.session_state.get("auth_username", "venky")
    saved_resumes = get_resumes(username)
    has_active_resume = bool(st.session_state.get("resume_text", "").strip())

    if not has_active_resume and not saved_resumes:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📄</div>
            <div class="empty-state-title">Upload a Resume to Tailor</div>
            <p class="empty-state-desc">Please upload your baseline resume first in the Resume Analyzer.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Resume Analyzer →", type="primary"):
            st.session_state.current_page = "resume_analyzer"
            st.rerun()
        return

    # Multi-Resume Selector
    if saved_resumes:
        st.markdown("""
        <div class="saas-card" style="padding: 1rem 1.25rem; margin-bottom: 1rem;">
            <div style="font-size: 13px; font-weight: 700; color: #0f172a; margin-bottom: 0.5rem;">📄 SELECT BASELINE RESUME TO TAILOR</div>
        """, unsafe_allow_html=True)
        r_labels = [f"{r.get('title', 'Resume')} ({r.get('version', 'v1')})" for r in saved_resumes]
        chosen_idx = st.selectbox(
            "Choose Baseline Resume",
            range(len(r_labels)),
            format_func=lambda i: r_labels[i],
            key="tailor_resume_picker",
            label_visibility="collapsed"
        )
        picked_r = saved_resumes[chosen_idx]
        resume_text = picked_r.get("content", "")
        base_title = picked_r.get("title", "Baseline Resume")
        st.markdown(f"<div style='font-size: 12px; color: #64748b;'>Selected baseline: <strong>{base_title}</strong></div></div>", unsafe_allow_html=True)
    else:
        resume_text = st.session_state.resume_text
        base_title = "Uploaded Resume"

    default_jd = st.session_state.get("current_jd", "")

    st.markdown("""
    <div class="saas-card" style="margin-bottom: 1.25rem;">
        <div class="saas-card-header">📋 Target Job Description</div>
        <p style="font-size: 0.85rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 0.75rem;">
            Provide the target job description to guide the tailoring engine:
        </p>
    </div>
    """, unsafe_allow_html=True)

    target_jd = st.text_area(
        "Job Description for Tailoring",
        value=default_jd,
        height=160,
        placeholder="Paste target job description to tailor your resume...",
        key="tailor_jd_input",
        label_visibility="collapsed"
    )

    if st.button("✨ Generate Tailored Resume", type="primary", key="btn_run_tailoring"):
        if not target_jd.strip():
            st.warning("Please paste a target job description first.")
        else:
            st.session_state.current_jd = target_jd
            with st.spinner("Tailoring professional summary and extracting role-aligned projects..."):
                tailored_summary = build_tailored_summary(resume_text, target_jd)
                matching_skills, missing_skills = get_tailoring_skill_recommendations(resume_text, target_jd)
                project_recs = get_tailoring_project_recommendations(resume_text, target_jd)
                improvements = generate_tailoring_recommendations(resume_text, target_jd, matching_skills, missing_skills)

                st.session_state.tailored_summary = tailored_summary
                st.session_state.tailored_matching = matching_skills
                st.session_state.tailored_missing = missing_skills
                st.session_state.tailored_project_recs = project_recs
                st.session_state.tailored_improvements = improvements
                st.session_state.tailoring_done = True
                st.success("✨ Resume successfully tailored to target role!")

    if not st.session_state.get("tailoring_done", False):
        st.info("👆 Enter target job description above and click 'Generate Tailored Resume' to open your workspace.")
        return

    summary = st.session_state.get("tailored_summary", "")
    matching = st.session_state.get("tailored_matching", [])
    missing = st.session_state.get("tailored_missing", [])
    project_recs = st.session_state.get("tailored_project_recs", [])
    improvements = st.session_state.get("tailored_improvements", [])

    # Workspace Tabs: Original vs Tailored vs Comparison
    tab_tailored, tab_orig, tab_comp = st.tabs(["✨ Tailored Version", "📄 Baseline Resume", "🔍 Alignment & Recommendations"])

    with tab_tailored:
        st.markdown("### 📝 Tailored Professional Profile")
        
        st.markdown(f"""
        <div class="document-sheet">
<strong>PROFESSIONAL SUMMARY</strong>
{summary}

<strong>VERIFIED TARGET SKILLS</strong>
{', '.join(matching) if matching else 'See original skills list'}

<strong>RECOMMENDED PROJECT EMPHASIS</strong>
{chr(10).join(['• ' + p for p in project_recs])}
        </div>
        """, unsafe_allow_html=True)

        full_tailored_text = f"""TAILORED RESUME - {base_title}

PROFESSIONAL SUMMARY:
{summary}

MATCHING TECHNICAL SKILLS:
{', '.join(matching)}

PROJECT ALIGNMENT:
""" + "\n".join(f"- {p}" for p in project_recs) + "\n\n" + resume_text

        # Action Buttons Row
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                "⬇️ Download Tailored TXT",
                data=full_tailored_text,
                file_name="tailored_resume.txt",
                mime="text/plain",
                use_container_width=True
            )
        with c2:
            projects = extract_section(resume_text, ["Projects", "Project"])
            certs = extract_section(resume_text, ["Certifications", "Certificates"])
            pdf_bytes = create_restored_tailored_resume_pdf(resume_text, summary, matching, projects, certs)
            if pdf_bytes:
                st.download_button(
                    "📄 Download Tailored PDF",
                    data=pdf_bytes,
                    file_name="tailored_resume.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.info("PDF export formatted as TXT.")
        with c3:
            if st.button("💾 Save as Tailored Resume Version", use_container_width=True):
                new_title = f"[Tailored] {base_title[:24]}"
                ok, msg, _ = create_resume(
                    user_id=username,
                    title=new_title,
                    content=full_tailored_text,
                    skills=matching,
                    score=85,
                    filename="tailored_resume.txt",
                    is_default=False
                )
                if ok:
                    st.success(f"Saved '{new_title}' into My Resumes library!")
                else:
                    st.info(msg)

    with tab_orig:
        st.markdown(f"### 📄 Baseline Resume: {base_title}")
        st.text_area("Baseline Content", resume_text, height=350, disabled=True)

    with tab_comp:
        st.markdown("### 🔍 Role Alignment & Strategy")
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">✨ AI Improvements & Highlighting</div>
        """, unsafe_allow_html=True)
        for imp in improvements:
            st.markdown(f"""
            <div style="padding: 6px 0; display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: #334155;">
                <span style="color: #4f46e5;">•</span>
                <span>{imp}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="saas-card">
            <div class="saas-card-header">🎯 Key Job Skills Matching ({len(matching)})</div>
            <div class="chip-container">
                {''.join([f'<span class="skill-chip skill-chip-match">✓ {s}</span>' for s in matching])}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Ethical Notice
        st.markdown("""
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 12px 16px; margin-top: 14px; font-size: 12.5px; color: #1e40af;">
            <strong>🛡️ Fact-Based Tailoring Guarantee:</strong> This tool only reframes and aligns your genuine experiences with the employer's vocabulary. Never claim technologies, projects, or metrics that you cannot defend in a technical interview.
        </div>
        """, unsafe_allow_html=True)

