"""
AI Mock Interview UI Module
Provides a professional, SaaS-style adaptive mock interview interface with
resume/job-specific questions, live timer, speech dictation, transparent evaluations,
longitudinal analytics, and an interactive 'Improvement Mode'.
"""

import time
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

from database.models import (
    INTERVIEW_TYPES,
    DIFFICULTY_LEVELS,
    INTERVIEWER_PERSONALITIES,
    QUESTION_COUNT_OPTIONS,
    DURATION_OPTIONS,
)
from database.resumes import get_resumes
from database.jobs import get_saved_jobs
from database.repository import (
    get_user_interview_sessions,
    get_user_interview_reports,
    get_interview_report,
    get_interview_progress_analytics,
    delete_interview_session,
    auth_get_profile,
)
from services.interview_engine import (
    start_new_interview,
    get_interview_session_state,
    process_answer_submission,
    pause_interview,
    resume_interview,
)
from services.interview_recommendations import generate_improvement_interview_plan
from services.voice_provider import get_web_speech_input_html


def render_mock_interview():
    """Main entrypoint for the AI Mock Interview page."""
    username = st.session_state.get("auth_username", "venky")
    profile = auth_get_profile(username) if username else {}

    # Top Header
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">🎙️</div>
            <div>
                <h1 class="app-title">AI Mock Interview Bot</h1>
                <p class="app-subtitle">Adaptive, role-specific technical & behavioral interview practice with real-time scoring and feedback.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize Session State Keys
    if "active_interview_session_id" not in st.session_state:
        st.session_state.active_interview_session_id = None
    if "interview_last_eval" not in st.session_state:
        st.session_state.interview_last_eval = None
    if "interview_view_report_id" not in st.session_state:
        st.session_state.interview_view_report_id = None
    if "interview_start_timestamp" not in st.session_state:
        st.session_state.interview_start_timestamp = None

    # Check for active session in DB if not in state
    if not st.session_state.active_interview_session_id:
        sessions = get_user_interview_sessions(username, limit=1)
        if sessions and sessions[0].get("status") == "in_progress":
            st.session_state.active_interview_session_id = sessions[0]["session_id"]

    # If currently in an active interview session
    if st.session_state.active_interview_session_id:
        render_active_interview_flow(username)
        return

    # If viewing a specific report
    if st.session_state.interview_view_report_id:
        render_report_view(username, st.session_state.interview_view_report_id)
        return

    # Normal Mode: 3 Tabs (New Practice, Past Reports, Progress Tracking)
    tab_setup, tab_reports, tab_analytics = st.tabs([
        "🎯 Start Interview",
        "📋 Performance Reports",
        "📈 Progress & Analytics"
    ])

    with tab_setup:
        render_setup_screen(username, profile)

    with tab_reports:
        render_reports_list(username)

    with tab_analytics:
        render_analytics_tab(username)


# =========================================================
# 1. SETUP SCREEN
# =========================================================

def render_setup_screen(username: str, profile: Dict[str, Any]):
    """Renders the clean interview configuration panel."""
    # Check if a job was passed via cross-navigation
    preselected_job = st.session_state.pop("interview_selected_job", None)
    default_role = ""
    default_type_idx = 1  # Technical

    if preselected_job:
        default_role = preselected_job.get("title", "")
        default_type_idx = 5  # Job-Specific
        st.success(f"🎯 **Target Job Attached:** '{preselected_job.get('title')}' at **{preselected_job.get('company')}**. Interview will be customized to this job description.")
    elif profile.get("target_roles"):
        default_role = profile.get("target_roles").split(",")[0].strip()
    elif profile.get("professional_title"):
        default_role = profile.get("professional_title")
    else:
        default_role = "Python Developer"

    st.markdown('<div class="saas-card" style="margin-top: 10px;">', unsafe_allow_html=True)
    st.markdown('<div class="saas-card-header">⚙️ Configure Your Practice Session</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        target_role = st.text_input(
            "Target Role / Position",
            value=default_role,
            placeholder="e.g. Senior Python Engineer, Data Analyst",
            help="The specific job title you are interviewing for."
        )

        interview_type = st.selectbox(
            "Interview Mode",
            INTERVIEW_TYPES,
            index=default_type_idx,
            help="Select the domain focus of the interview questions."
        )

        difficulty = st.selectbox(
            "Difficulty Level",
            DIFFICULTY_LEVELS,
            index=3,  # Adaptive default
            help="'Adaptive' dynamically raises difficulty after strong answers and asks fundamentals after weak answers."
        )

        interviewer_personality = st.selectbox(
            "Interviewer Style",
            INTERVIEWER_PERSONALITIES,
            index=0,  # Professional
            help="Controls tone, framing, and strictness of the interviewer."
        )

    with col2:
        q_count = st.selectbox(
            "Number of Questions",
            QUESTION_COUNT_OPTIONS,
            index=0,  # 5 questions default
            help="Choose between quick drill (5 Qs) or full interview simulation (10-20 Qs)."
        )

        duration_choice = st.selectbox(
            "Interview Timer",
            [0, 15, 30, 45, 60],
            format_func=lambda x: "No Timer (Untimed)" if x == 0 else f"{x} Minutes",
            index=1,  # 15 minutes default
            help="Adds a real-time countdown timer to simulate authentic interview pacing."
        )

        # Resume Selector
        user_resumes = get_resumes(username)
        resume_options = {"None (General Assessment)": ""}
        for r in user_resumes:
            lbl = f"{r.get('title', 'Resume')} ({r.get('score', 0)}% ATS)" + (" [Default]" if r.get("is_default") else "")
            resume_options[lbl] = r.get("resume_id")

        selected_resume_label = st.selectbox(
            "Ground Questions in Resume",
            list(resume_options.keys()),
            index=min(1, len(resume_options) - 1),
            help="Select a resume to have the AI probe your actual projects, libraries, and verified experience."
        )
        selected_resume_id = resume_options[selected_resume_label]

        # Job Selector
        user_jobs = get_saved_jobs(username)
        job_options = {"None (Role-Based Questions)": ""}
        if preselected_job:
            job_options[f"📌 Selected: {preselected_job.get('title')} ({preselected_job.get('company')})"] = "preselected"

        for j in user_jobs:
            j_lbl = f"{j.get('title')} - {j.get('company')}"
            job_options[j_lbl] = j.get("job_id")

        selected_job_label = st.selectbox(
            "Job Description Context",
            list(job_options.keys()),
            index=1 if preselected_job else 0,
            help="Select a saved job to tailor questions to its exact tech stack and required skills."
        )
        selected_job_id = job_options[selected_job_label]

    st.markdown("</div>", unsafe_allow_html=True)

    # Start Session Action
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    if st.button("🚀 Start Interview Simulation", type="primary", use_container_width=True):
        if not target_role.strip():
            st.error("Please enter a Target Role to begin.")
            return

        with st.spinner("Preparing your personalized interview room and grounding questions..."):
            resolved_job_data = preselected_job if selected_job_id == "preselected" else None
            actual_job_id = "" if selected_job_id == "preselected" else selected_job_id

            ok, session_id, state = start_new_interview(
                user_id=username,
                target_role=target_role.strip(),
                interview_type=interview_type,
                difficulty=difficulty,
                interviewer_personality=interviewer_personality,
                question_count=q_count,
                duration_minutes=duration_choice,
                resume_id=selected_resume_id,
                job_id=actual_job_id,
                job_data=resolved_job_data
            )

            if ok:
                st.session_state.active_interview_session_id = session_id
                st.session_state.interview_last_eval = None
                st.session_state.interview_start_timestamp = time.time()
                st.success("✅ Interview started!")
                st.rerun()
            else:
                st.error(f"❌ Failed to start interview: {session_id}")


# =========================================================
# 2. ACTIVE INTERVIEW FLOW
# =========================================================

def render_active_interview_flow(username: str):
    """Renders the distraction-free active interview interaction room."""
    session_id = st.session_state.active_interview_session_id
    state = get_interview_session_state(username, session_id)

    if not state:
        st.error("Session could not be retrieved.")
        if st.button("← Return to Setup"):
            st.session_state.active_interview_session_id = None
            st.rerun()
        return

    # Check if session is completed
    if state["is_completed"]:
        st.session_state.active_interview_session_id = None
        st.session_state.interview_view_report_id = session_id
        st.rerun()
        return

    curr_q = state["current_question"]
    q_num = state["current_question_number"]
    total_q = state["total_questions"]
    role = state["target_role"]
    sess_rec = state["session"]
    duration_mins = sess_rec.get("duration_minutes", 0)

    # Top Status Bar
    header_col1, header_col2, header_col3 = st.columns([2, 1, 1])

    with header_col1:
        st.markdown(f"### 🎙️ {role}")
        st.markdown(f"<span style='color: #64748b; font-size: 13px;'>Mode: <b>{state['interview_type']}</b> &nbsp;•&nbsp; Difficulty: <b>{state['difficulty']}</b></span>", unsafe_allow_html=True)

    with header_col2:
        st.markdown(f"**Question {q_num} of {total_q}**")
        st.progress(state["progress_pct"] / 100.0)

    with header_col3:
        if duration_mins > 0 and st.session_state.interview_start_timestamp:
            elapsed = time.time() - st.session_state.interview_start_timestamp
            remaining = max(0, int((duration_mins * 60) - elapsed))
            mins, secs = divmod(remaining, 60)
            timer_color = "#dc2626" if remaining < 180 else "#0f172a"
            st.markdown(f"<div style='text-align: right; font-size: 18px; font-weight: 800; color: {timer_color};'>⏳ {mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)
            if remaining == 0:
                st.warning("⚠️ Time limit reached! You may finish your current answer or submit to conclude.")
        else:
            st.markdown("<div style='text-align: right; font-size: 13px; color: #64748b;'>⏱️ Untimed</div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin: 12px 0 16px 0; border: none; border-top: 1px solid #e2e8f0;' />", unsafe_allow_html=True)

    # Question Display Card
    cat_badge = curr_q.get("category", "Technical")
    diff_badge = curr_q.get("difficulty", "Medium")

    st.markdown(f"""
    <div class="saas-card" style="padding: 1.5rem; border-left: 4px solid #4f46e5; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="background: #eef2ff; color: #4338ca; font-weight: 700; font-size: 11.5px; padding: 3px 10px; border-radius: 99px;">
                🏷️ {cat_badge}
            </span>
            <span style="background: #f8fafc; color: #64748b; font-weight: 600; font-size: 11.5px; padding: 3px 10px; border-radius: 99px; border: 1px solid #e2e8f0;">
                ⚡ {diff_badge}
            </span>
        </div>
        <div style="font-size: 17px; font-weight: 700; color: #0f172a; line-height: 1.5; white-space: pre-line;">
            {curr_q.get('question_text', '')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Optional Web Speech Voice Dictation Bridge
    st.markdown(get_web_speech_input_html(f"voice_input_q{q_num}"), unsafe_allow_html=True)

    # Answer Input Box
    answer_input = st.text_area(
        "Your Answer",
        height=200,
        placeholder="Type or dictate your structured response here... Explain your reasoning, core concepts, and practical examples.",
        key=f"answer_ta_{curr_q.get('question_id')}"
    )

    word_count = len(answer_input.strip().split()) if answer_input.strip() else 0
    st.markdown(f"<div style='font-size: 11.5px; color: #94a3b8; text-align: right; margin-top: -8px; margin-bottom: 12px;'>Words: {word_count} &nbsp;|&nbsp; Characters: {len(answer_input)}</div>", unsafe_allow_html=True)

    # Last Evaluation Feedback Preview (if submitted on this question)
    if st.session_state.interview_last_eval:
        ev = st.session_state.interview_last_eval
        st.markdown(f"""
        <div class="saas-card" style="background: #f8fafc; border: 1px solid #cbd5e1; margin-bottom: 1.25rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="font-weight: 700; font-size: 14px; color: #0f172a;">⚡ Answer Evaluation Feedback</div>
                <div style="font-size: 18px; font-weight: 800; color: #4f46e5;">{ev['overall_answer_score']} / 100</div>
            </div>
            <div style="font-size: 13px; color: #334155; margin-bottom: 10px;">{ev['feedback']}</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 12px;">
                <div style="background: #ecfdf5; padding: 8px; border-radius: 6px; border: 1px solid #a7f3d0;">
                    <div style="font-weight: 700; color: #065f46; margin-bottom: 4px;">Strengths:</div>
                    {''.join([f'<div style="color: #047857;">✓ {s}</div>' for s in ev.get('strengths', [])])}
                </div>
                <div style="background: #fffbeb; padding: 8px; border-radius: 6px; border: 1px solid #fde68a;">
                    <div style="font-weight: 700; color: #92400e; margin-bottom: 4px;">Areas to Improve:</div>
                    {''.join([f'<div style="color: #b45309;">⚠ {w}</div>' for w in ev.get('improvements', [])])}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Action Buttons Row
    btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])

    with btn_col1:
        if st.button("⚡ Submit Answer & Next Question →", type="primary", use_container_width=True):
            if not answer_input.strip():
                st.warning("Please provide an answer before submitting.")
                return

            with st.spinner("Evaluating your response and formulating next adaptive question..."):
                res = process_answer_submission(
                    user_id=username,
                    session_id=session_id,
                    question_id=curr_q["question_id"],
                    answer_text=answer_input
                )

                if res.get("success"):
                    st.session_state.interview_last_eval = res.get("evaluation")
                    if res.get("is_completed"):
                        st.session_state.active_interview_session_id = None
                        st.session_state.interview_view_report_id = session_id
                    st.rerun()
                else:
                    st.error(f"Error submitting answer: {res.get('error')}")

    with btn_col2:
        if st.button("⏸️ Pause Session", use_container_width=True):
            pause_interview(username, session_id)
            st.session_state.active_interview_session_id = None
            st.info("Interview paused! You can resume from your reports list whenever you're ready.")
            st.rerun()

    with btn_col3:
        if st.button("⏹️ Conclude Early", use_container_width=True):
            from services.interview_engine import finalize_interview_session
            finalize_interview_session(username, session_id)
            st.session_state.active_interview_session_id = None
            st.session_state.interview_view_report_id = session_id
            st.rerun()


# =========================================================
# 3. PERFORMANCE REPORT VIEW
# =========================================================

def render_report_view(username: str, session_id: str):
    """Renders the full post-interview diagnostic report and scorecard."""
    rep = get_interview_report(username, session_id)

    if not rep:
        st.error("Report could not be found.")
        if st.button("← Back to Interviews"):
            st.session_state.interview_view_report_id = None
            st.rerun()
        return

    st.markdown("<div style='margin-bottom: 12px;'>", unsafe_allow_html=True)
    if st.button("← Back to Mock Interview Dashboard"):
        st.session_state.interview_view_report_id = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    overall = rep.get("overall_score", 0.0)
    score_color = "#10b981" if overall >= 80 else ("#4f46e5" if overall >= 65 else "#f59e0b")

    # Scorecard Banner
    st.markdown(f"""
    <div class="saas-card" style="margin-bottom: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
            <div>
                <span style="background: #eef2ff; color: #4338ca; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 99px;">
                    COMPLETED REPORT
                </span>
                <h2 style="margin: 6px 0 2px 0; color: #0f172a; font-size: 22px;">{rep.get('target_role', 'Interview')} Performance Report</h2>
                <div style="font-size: 12px; color: #64748b;">Conducted on {rep.get('created_at', '')[:16]}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase;">Overall Score</div>
                <div style="font-size: 38px; font-weight: 800; color: {score_color}; line-height: 1;">{overall}<span style="font-size: 18px; color: #94a3b8;">/100</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 5 Dimensional Sub-Scores
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">💻 Technical</div>
            <div class="stat-value" style="color: #4f46e5;">{rep.get('technical_score', 0)}%</div>
            <div class="stat-subtext-neutral">Core depth</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🧩 Problem Solving</div>
            <div class="stat-value" style="color: #0284c7;">{rep.get('problem_solving_score', 0)}%</div>
            <div class="stat-subtext-neutral">Practical reasoning</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🗣️ Clarity</div>
            <div class="stat-value" style="color: #10b981;">{rep.get('communication_score', 0)}%</div>
            <div class="stat-subtext-neutral">Structure & tone</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">📝 Completeness</div>
            <div class="stat-value" style="color: #f59e0b;">{rep.get('completeness_score', 0)}%</div>
            <div class="stat-subtext-neutral">Trade-offs covered</div>
        </div>
        """, unsafe_allow_html=True)
    with k5:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🎯 Relevance</div>
            <div class="stat-value" style="color: #8b5cf6;">{rep.get('relevance_score', 0)}%</div>
            <div class="stat-subtext-neutral">Prompt alignment</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Strengths & Needs Improvement
    col_str, col_weak = st.columns(2)

    with col_str:
        st.markdown("""
        <div class="saas-card" style="height: 100%;">
            <div class="saas-card-header" style="color: #166534;">✅ Strong Areas Demonstrated</div>
        """, unsafe_allow_html=True)
        for s in rep.get("strengths", []):
            st.markdown(f"""
            <div style="display: flex; gap: 8px; font-size: 13px; color: #1e293b; padding: 4px 0;">
                <span style="color: #16a34a; font-weight: 700;">✓</span>
                <span>{s}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_weak:
        st.markdown("""
        <div class="saas-card" style="height: 100%;">
            <div class="saas-card-header" style="color: #991b1b;">⚠️ Areas to Strengthen</div>
        """, unsafe_allow_html=True)
        for w in rep.get("weaknesses", []):
            st.markdown(f"""
            <div style="display: flex; gap: 8px; font-size: 13px; color: #1e293b; padding: 4px 0;">
                <span style="color: #dc2626; font-weight: 700;">•</span>
                <span>{w}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Recommended Study & Improvement Mode Trigger
    st.markdown("""
    <div class="saas-card">
        <div class="saas-card-header">💡 Personalized Learning Recommendations</div>
    """, unsafe_allow_html=True)

    for idx, rec in enumerate(rep.get("recommendations", [])):
        st.markdown(f"""
        <div style="padding: 6px 0; font-size: 13.5px; color: #334155; display: flex; gap: 8px;">
            <span style="font-weight: 700; color: #4f46e5;">{idx + 1}.</span>
            <span>{rec}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Improvement Mode Action Button
    act_col1, act_col2 = st.columns([1, 1])
    with act_col1:
        if st.button("🎯 Practice Weak Areas (Improvement Mode)", type="primary", use_container_width=True):
            weak_list = rep.get("weaknesses", [])
            plan = generate_improvement_interview_plan(rep.get("target_role", ""), weak_list)
            st.info(f"Setting up targeted drill for: **{plan['focus_summary']}**...")

            ok, new_sess_id, _ = start_new_interview(
                user_id=username,
                target_role=rep.get("target_role", "Engineer"),
                interview_type="Technical",
                difficulty="Adaptive",
                interviewer_personality="Technical",
                question_count=3,
                duration_minutes=15
            )
            if ok:
                st.session_state.active_interview_session_id = new_sess_id
                st.session_state.interview_view_report_id = None
                st.session_state.interview_start_timestamp = time.time()
                st.rerun()

    with act_col2:
        report_text = [
            f"AI MOCK INTERVIEW PERFORMANCE REPORT",
            "=" * 45,
            f"Role: {rep.get('target_role')}",
            f"Date: {rep.get('created_at')}",
            f"Overall Score: {rep.get('overall_score')}/100",
            f"Technical Depth: {rep.get('technical_score')}%",
            f"Problem Solving: {rep.get('problem_solving_score')}%",
            f"Clarity & Structure: {rep.get('communication_score')}%",
            f"Completeness: {rep.get('completeness_score')}%",
            "",
            "STRENGTHS:",
            "\n".join(f"- {s}" for s in rep.get("strengths", [])),
            "",
            "AREAS TO IMPROVE:",
            "\n".join(f"- {w}" for w in rep.get("weaknesses", [])),
            "",
            "RECOMMENDATIONS:",
            "\n".join(f"{i+1}. {r}" for i, r in enumerate(rep.get("recommendations", [])))
        ]
        st.download_button(
            "⬇️ Download Full Performance Report (TXT)",
            data="\n".join(report_text),
            file_name=f"interview_report_{session_id[:8]}.txt",
            mime="text/plain",
            use_container_width=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Detailed Question-by-Question Review
    st.markdown("### 🔍 Question-by-Question Review")
    reviews = rep.get("question_reviews", [])

    if not reviews:
        st.info("Detailed breakdown is processing.")
    else:
        for r_item in reviews:
            q_idx = r_item.get("question_number", 1)
            q_score = r_item.get("overall_score", 0.0)
            score_badge = "#10b981" if q_score >= 80 else ("#4f46e5" if q_score >= 65 else "#ef4444")

            with st.expander(f"Question {q_idx}: {r_item.get('question_text')[:75]}... ({int(q_score)}/100)"):
                st.markdown(f"**Question:**\n> {r_item.get('question_text')}")
                st.markdown(f"**Your Answer:**\n```text\n{r_item.get('answer_text') or '(No answer recorded)'}\n```")
                st.markdown(f"**Interviewer Evaluation Score:** <span style='font-weight: 800; color: {score_badge};'>{q_score}/100</span>", unsafe_allow_html=True)
                st.markdown(f"**Feedback:** {r_item.get('feedback')}")

                sub_c1, sub_c2 = st.columns(2)
                with sub_c1:
                    st.markdown("**✓ What you did well:**")
                    for s in r_item.get("strengths", []):
                        st.markdown(f"- <span style='color: #16a34a;'>{s}</span>", unsafe_allow_html=True)
                with sub_c2:
                    st.markdown("**⚠ What was missing:**")
                    for w in r_item.get("improvements", []):
                        st.markdown(f"- <span style='color: #d97706;'>{w}</span>", unsafe_allow_html=True)


# =========================================================
# 4. REPORTS LIST TAB
# =========================================================

def render_reports_list(username: str):
    """Renders the chronological repository of completed and paused interview sessions."""
    sessions = get_user_interview_sessions(username, limit=30)

    if not sessions:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📋</div>
            <div class="empty-state-title">No interviews completed yet</div>
            <p class="empty-state-desc">Start your first AI mock interview to build your personalized performance history and track score progress.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"<div style='font-size: 13px; color: #64748b; margin-bottom: 12px;'>Showing your last <b>{len(sessions)}</b> interview attempts:</div>", unsafe_allow_html=True)

    for sess in sessions:
        sid = sess["session_id"]
        status = sess.get("status", "completed")
        score = sess.get("overall_score", 0.0)
        role = sess.get("target_role", "Professional")
        itype = sess.get("interview_type", "Technical")
        date_str = sess.get("started_at", "")[:10]
        q_count = sess.get("question_count", 5)

        with st.container():
            st.markdown(f"""
            <div class="saas-card" style="margin-bottom: 0.75rem; padding: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div style="font-weight: 700; font-size: 15px; color: #0f172a;">{role}</div>
                        <div style="font-size: 12px; color: #64748b; margin-top: 2px;">
                            📅 {date_str} &nbsp;•&nbsp; 🏷️ {itype} &nbsp;•&nbsp; ❓ {q_count} Questions
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: {'#ecfdf5' if score >= 75 else '#eff6ff'}; color: {'#065f46' if score >= 75 else '#1e40af'}; font-weight: 800; font-size: 14px; padding: 3px 10px; border-radius: 99px;">
                            {score}/100
                        </span>
                        <div style="font-size: 11px; color: #94a3b8; margin-top: 4px; text-transform: uppercase;">{status}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            b1, b2 = st.columns([1, 1])
            with b1:
                if status == "completed":
                    if st.button("📊 View Performance Report", key=f"btn_view_rep_{sid}", use_container_width=True):
                        st.session_state.interview_view_report_id = sid
                        st.rerun()
                elif status == "paused":
                    if st.button("▶️ Resume Session", key=f"btn_resume_{sid}", type="primary", use_container_width=True):
                        resume_interview(username, sid)
                        st.session_state.active_interview_session_id = sid
                        st.rerun()
            with b2:
                if st.button("🗑️ Delete Record", key=f"btn_del_sess_{sid}", use_container_width=True):
                    delete_interview_session(username, sid)
                    st.success("Record removed.")
                    st.rerun()


# =========================================================
# 5. PROGRESS & ANALYTICS TAB
# =========================================================

def render_analytics_tab(username: str):
    """Renders longitudinal performance trajectory charts and weak-spot summaries."""
    analytics = get_interview_progress_analytics(username)

    if not analytics["has_data"]:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📈</div>
            <div class="empty-state-title">Insufficient Historical Data</div>
            <p class="empty-state-desc">Complete at least one interview session to unlock longitudinal skill progression charts and category trends.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Top KPI Metrics Row
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🏁 Interviews Completed</div>
            <div class="stat-value">{analytics['total_completed']}</div>
            <div class="stat-subtext-neutral">Total practice runs</div>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🎯 Average Score</div>
            <div class="stat-value" style="color: #4f46e5;">{analytics['average_score']}</div>
            <div class="stat-subtext-neutral">Across all attempts</div>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        delta_color = "#10b981" if analytics["score_delta"] >= 0 else "#ef4444"
        delta_sign = "+" if analytics["score_delta"] >= 0 else ""
        subtext = f"{delta_sign}{analytics['score_delta']} vs prior interview" if analytics["has_previous"] else "First interview"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🚀 Latest Score</div>
            <div class="stat-value" style="color: {delta_color};">{analytics['latest_score']}</div>
            <div class="stat-subtext-neutral">{subtext}</div>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        top_weak = analytics["top_weak_topics"][0] if analytics["top_weak_topics"] else "None"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🎯 Primary Focus Area</div>
            <div class="stat-value" style="font-size: 16px; color: #d97706; padding-top: 4px;">{top_weak[:18]}</div>
            <div class="stat-subtext-neutral">Highest occurrence</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Score Progression Chart
    st.markdown("""
    <div class="saas-card">
        <div class="saas-card-header">📈 Longitudinal Score Progression</div>
    """, unsafe_allow_html=True)

    df_trend = pd.DataFrame(analytics["score_trend"])
    if not df_trend.empty:
        chart_data = df_trend.rename(columns={"index": "Attempt", "score": "Interview Score"})
        st.line_chart(chart_data.set_index("Attempt")["Interview Score"])
    st.markdown("</div>", unsafe_allow_html=True)

    # Top Strengths vs Recurring Weaknesses
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">🌟 Consistently Strong Topics</div>
        """, unsafe_allow_html=True)
        if analytics["top_strong_topics"]:
            for s in analytics["top_strong_topics"]:
                st.markdown(f"""
                <div style="padding: 6px 0; font-size: 13px; color: #166534; display: flex; gap: 8px;">
                    <span>✓</span>
                    <span>{s}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Complete more interviews to detect recurring strengths.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">🎯 Key Opportunity Areas</div>
        """, unsafe_allow_html=True)
        if analytics["top_weak_topics"]:
            for w in analytics["top_weak_topics"]:
                st.markdown(f"""
                <div style="padding: 6px 0; font-size: 13px; color: #b45309; display: flex; gap: 8px;">
                    <span>⚠</span>
                    <span>{w}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recurring weak spots identified yet.")
        st.markdown("</div>", unsafe_allow_html=True)
