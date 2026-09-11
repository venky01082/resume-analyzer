"""
My Resumes UI Module
Manages multiple resume profiles, version comparison, default selection, and role-specific exports.
"""

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
)
from database import (
    get_resumes,
    get_resume,
    get_default_resume,
    save_resume,
    set_default_resume,
    update_resume_title,
    delete_resume,
)


def load_resume_into_session(resume_data: dict) -> None:
    """Load a specific resume record into the application-wide session state."""
    text = resume_data.get("text", "")
    st.session_state.active_resume_id = resume_data.get("resume_id")
    st.session_state.active_resume_title = resume_data.get("title", "Resume")
    st.session_state.resume_text = text

    parsed = resume_data.get("parsed_data", {})
    st.session_state.resume_name = parsed.get("name") or extract_name(text)
    st.session_state.resume_email = parsed.get("email") or extract_email(text)
    st.session_state.resume_phone = parsed.get("phone") or extract_phone(text)
    st.session_state.resume_skills = parsed.get("skills") or extract_skills(text)
    st.session_state.resume_education = parsed.get("education") or extract_education_details(text)
    st.session_state.resume_projects = parsed.get("projects") or extract_projects(text)
    st.session_state.resume_experience = parsed.get("experience") or extract_experience(text)
    st.session_state.resume_certifications = parsed.get("certifications") or extract_section(text, ["Certifications", "Certificates"])
    st.session_state.resume_score = resume_data.get("score") or resume_score(
        text,
        st.session_state.resume_skills,
        st.session_state.resume_education,
        st.session_state.resume_projects,
        st.session_state.resume_experience,
        st.session_state.resume_certifications
    )


def render_my_resumes():
    """Renders the My Resumes management workspace."""
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">📑</div>
            <div>
                <h1 class="app-title">My Resumes</h1>
                <p class="app-subtitle">Manage, compare, and tailor multiple resume profiles for different roles.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    username = st.session_state.get("auth_username", "venky")
    user_resumes = get_resumes(username)

    tab_list, tab_upload, tab_compare = st.tabs(["📁 Saved Resumes", "➕ Add New Resume", "⚖️ Compare Resumes"])

    # =========================================================
    # TAB 1: SAVED RESUMES LIST
    # =========================================================
    with tab_list:
        if not user_resumes:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📄</div>
                <div class="empty-state-title">No Resumes Saved Yet</div>
                <p class="empty-state-desc">Upload tailored versions for different careers (e.g., Data Analyst, Software Engineer).</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"#### 📑 Your Resume Profiles ({len(user_resumes)})")
            active_id = st.session_state.get("active_resume_id", "")

            for idx, res in enumerate(user_resumes):
                r_id = res.get("resume_id")
                title = res.get("title", "Untitled Resume")
                score = res.get("score", 0)
                uploaded = res.get("uploaded_at", "")
                is_default = res.get("is_default", False)
                is_current = (active_id == r_id)

                card_border = "#4f46e5" if is_current else ("#10b981" if is_default else "#e2e8f0")
                badge_html = ""
                if is_current:
                    badge_html += '<span style="background: #e0e7ff; color: #3730a3; font-weight: 700; font-size: 11px; padding: 2px 8px; border-radius: 99px; margin-right: 6px;">● Active in Workspace</span>'
                if is_default:
                    badge_html += '<span style="background: #ecfdf5; color: #065f46; font-weight: 700; font-size: 11px; padding: 2px 8px; border-radius: 99px;">⭐ Default</span>'

                st.markdown(f"""
                <div class="saas-card" style="border-left: 4px solid {card_border}; padding: 1.25rem; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <h3 style="margin: 0; font-size: 1.15rem; color: #0f172a;">{title}</h3>
                                {badge_html}
                            </div>
                            <div style="font-size: 0.82rem; color: #64748b; margin-top: 4px;">
                                📁 {res.get('filename', 'resume.pdf')} &nbsp;•&nbsp; 🕒 Uploaded: {uploaded}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 1.3rem; font-weight: 800; color: {'#10b981' if score >= 75 else '#4f46e5'};">{score}</span>
                            <span style="font-size: 0.8rem; color: #64748b;">/ 100</span>
                            <div style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 600;">ATS Baseline</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                c1, c2, c3, c4, c5 = st.columns([1.5, 1.2, 1.2, 1.2, 1.2])

                with c1:
                    if st.button("🚀 Set Active in Workspace", key=f"activate_{r_id}", use_container_width=True, type="primary" if is_current else "secondary"):
                        load_resume_into_session(res)
                        st.success(f"'{title}' is now loaded across all AI tools!")
                        st.rerun()

                with c2:
                    if st.button("🔍 Analyze", key=f"analyze_{r_id}", use_container_width=True):
                        load_resume_into_session(res)
                        st.session_state.current_page = "resume_analyzer"
                        st.rerun()

                with c3:
                    if st.button("✨ Tailor", key=f"tailor_{r_id}", use_container_width=True):
                        load_resume_into_session(res)
                        st.session_state.current_page = "resume_tailoring"
                        st.rerun()

                with c4:
                    if not is_default:
                        if st.button("⭐ Make Default", key=f"default_{r_id}", use_container_width=True):
                            set_default_resume(username, r_id)
                            st.rerun()
                    else:
                        st.markdown("<div style='text-align: center; color: #10b981; font-size: 13px; padding-top: 8px;'>Default Profile</div>", unsafe_allow_html=True)

                with c5:
                    with st.popover("⚙️ More"):
                        st.download_button(
                            "📥 Download Text",
                            data=res.get("text", ""),
                            file_name=f"{title.replace(' ', '_')}.txt",
                            mime="text/plain",
                            key=f"dl_{r_id}"
                        )
                        new_name = st.text_input("Rename", value=title, key=f"rename_input_{r_id}")
                        if st.button("Save Name", key=f"save_rename_{r_id}"):
                            if new_name.strip():
                                update_resume_title(username, r_id, new_name)
                                st.rerun()
                        st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)
                        if st.button("🗑️ Delete Resume", key=f"del_{r_id}"):
                            delete_resume(username, r_id)
                            if st.session_state.get("active_resume_id") == r_id:
                                st.session_state.resume_text = ""
                                st.session_state.active_resume_id = None
                            st.rerun()

    # =========================================================
    # TAB 2: ADD NEW RESUME
    # =========================================================
    with tab_upload:
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">➕ Upload Additional Resume Profile</div>
            <p style="font-size: 0.88rem; color: #64748b; margin-top: -0.5rem; margin-bottom: 1rem;">
                Keep distinct resumes tailored for specific roles (e.g. Data Analyst vs. Machine Learning Engineer).
            </p>
        </div>
        """, unsafe_allow_html=True)

        new_title = st.text_input("Resume Profile Name", placeholder="e.g. Senior Data Analyst Resume", key="new_resume_title_input")
        uploaded_pdf = st.file_uploader("Upload PDF Resume", type=["pdf"], key="my_resumes_file_uploader")
        make_default_check = st.checkbox("Set as my default resume profile", value=False, key="make_default_checkbox")

        if st.button("💾 Parse & Save Resume Profile", type="primary", key="btn_save_new_resume"):
            if not uploaded_pdf:
                st.warning("Please select a PDF file to upload.")
            else:
                try:
                    with st.spinner("Extracting text and calculating baseline ATS score..."):
                        text = extract_text(uploaded_pdf)
                    if not text.strip():
                        st.error("Could not extract readable text from PDF. Please make sure it is not a scanned image.")
                    else:
                        skills = extract_skills(text)
                        edu = extract_education_details(text)
                        proj = extract_projects(text)
                        exp = extract_experience(text)
                        certs = extract_section(text, ["Certifications", "Certificates"])
                        score = resume_score(text, skills, edu, proj, exp, certs)

                        parsed = {
                            "name": extract_name(text),
                            "email": extract_email(text),
                            "phone": extract_phone(text),
                            "skills": skills,
                            "education": edu,
                            "projects": proj,
                            "experience": exp,
                            "certifications": certs
                        }

                        label = new_title.strip() or uploaded_pdf.name.replace(".pdf", "")
                        saved = save_resume(
                            user_id=username,
                            title=label,
                            filename=uploaded_pdf.name,
                            text=text,
                            score=score,
                            parsed_data=parsed,
                            set_default=make_default_check
                        )
                        load_resume_into_session(saved)
                        st.success(f"✅ '{label}' saved and loaded into your workspace!")
                        st.rerun()
                except Exception as err:
                    st.error(f"Error processing resume: {err}")

    # =========================================================
    # TAB 3: COMPARE RESUMES
    # =========================================================
    with tab_compare:
        st.markdown("### ⚖️ Side-by-Side Resume Comparison")
        if len(user_resumes) < 2:
            st.info("You need at least 2 saved resumes to compare. Upload another resume in the 'Add New Resume' tab.")
        else:
            comp_c1, comp_c2 = st.columns(2)
            titles = [r.get("title", f"Resume {i+1}") for i, r in enumerate(user_resumes)]

            with comp_c1:
                sel_a = st.selectbox("Select First Resume", range(len(titles)), format_func=lambda i: titles[i], index=0, key="comp_sel_a")
            with comp_c2:
                sel_b = st.selectbox("Select Second Resume", range(len(titles)), format_func=lambda i: titles[i], index=min(1, len(titles)-1), key="comp_sel_b")

            res_a = user_resumes[sel_a]
            res_b = user_resumes[sel_b]

            skills_a = set(s.lower() for s in res_a.get("parsed_data", {}).get("skills", []))
            skills_b = set(s.lower() for s in res_b.get("parsed_data", {}).get("skills", []))

            col_res_a, col_res_b = st.columns(2)

            with col_res_a:
                st.markdown(f"""
                <div class="saas-card" style="border-top: 3px solid #4f46e5;">
                    <h4 style="margin: 0; color: #0f172a;">{res_a.get('title')}</h4>
                    <div style="font-size: 2rem; font-weight: 800; color: #4f46e5; margin: 8px 0;">{res_a.get('score', 0)} <span style="font-size: 1rem; color: #64748b;">/ 100</span></div>
                    <div style="font-size: 13px; color: #64748b;">Skills detected: <strong>{len(skills_a)}</strong></div>
                </div>
                """, unsafe_allow_html=True)
                only_a = [s.title() for s in sorted(skills_a - skills_b)]
                if only_a:
                    st.markdown(f"**Unique to {res_a.get('title')}:**")
                    st.write(", ".join(only_a))
                else:
                    st.write("No unique skills compared to Resume B.")

            with col_res_b:
                st.markdown(f"""
                <div class="saas-card" style="border-top: 3px solid #10b981;">
                    <h4 style="margin: 0; color: #0f172a;">{res_b.get('title')}</h4>
                    <div style="font-size: 2rem; font-weight: 800; color: #10b981; margin: 8px 0;">{res_b.get('score', 0)} <span style="font-size: 1rem; color: #64748b;">/ 100</span></div>
                    <div style="font-size: 13px; color: #64748b;">Skills detected: <strong>{len(skills_b)}</strong></div>
                </div>
                """, unsafe_allow_html=True)
                only_b = [s.title() for s in sorted(skills_b - skills_a)]
                if only_b:
                    st.markdown(f"**Unique to {res_b.get('title')}:**")
                    st.write(", ".join(only_b))
                else:
                    st.write("No unique skills compared to Resume A.")
