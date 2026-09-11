"""
Follow-Up System UI Module
Manages overdue, today, and upcoming recruiter communication deadlines with auto-generated follow-up emails.
"""

import streamlit as st
from datetime import date, timedelta, datetime
from database import (
    get_applications,
    get_overdue_follow_ups,
    get_today_follow_ups,
    get_upcoming_follow_ups,
    update_application,
    get_user_profile,
    STATUS_OPTIONS,
)


def generate_polite_follow_up_email(candidate_name: str, company: str, role: str, applied_date: str, contact_name: str = "") -> str:
    """Generate a polite, professional follow-up email inquiry."""
    salutation = f"Dear {contact_name}," if contact_name.strip() else f"Dear {company} Hiring Team,"
    date_context = f" on {applied_date}" if applied_date else " recently"

    return f"""Subject: Following up on application for {role} role - {candidate_name}

{salutation}

I hope this email finds you well.

I am writing to respectfully follow up on my application for the {role} position at {company}, which I submitted{date_context}. I remain very enthusiastic about the opportunity to contribute my skills and background to your team.

Could you please provide a brief update on the recruitment timeline for this position? I would welcome the opportunity to discuss how my qualifications align with your current goals.

Thank you very much for your time and continued consideration.

Warm regards,

{candidate_name}
"""


def render_followups():
    """Renders the Follow-Up Center workspace."""
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">⏰</div>
            <div>
                <h1 class="app-title">Follow-Up Center</h1>
                <p class="app-subtitle">Stay proactive with scheduled recruiter checkpoints and follow-up templates.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    username = st.session_state.get("auth_username", "venky")
    apps = get_applications(username)
    profile = get_user_profile(username)
    candidate_name = profile.get("full_name") or username.capitalize() or "Candidate"

    overdue = get_overdue_follow_ups(apps)
    today_items = get_today_follow_ups(apps)
    upcoming = get_upcoming_follow_ups(apps, days_ahead=14)

    # Top KPI Metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🔴 Overdue Follow-ups</div>
            <div class="stat-value" style="color: {'#dc2626' if overdue else '#64748b'};">{len(overdue)}</div>
            <div class="stat-subtext-neutral">Requires immediate outreach</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🟡 Due Today</div>
            <div class="stat-value" style="color: {'#d97706' if today_items else '#64748b'};">{len(today_items)}</div>
            <div class="stat-subtext-neutral">Scheduled for contact today</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🟢 Upcoming (14 Days)</div>
            <div class="stat-value" style="color: #10b981;">{len(upcoming)}</div>
            <div class="stat-subtext-neutral">Pipeline checkpoints planned</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    tab_overdue, tab_today, tab_upcoming = st.tabs([
        f"🔴 Overdue ({len(overdue)})",
        f"🟡 Due Today ({len(today_items)})",
        f"🟢 Upcoming ({len(upcoming)})"
    ])

    def render_follow_up_cards(items, category_type):
        if not items:
            st.markdown(f"""
            <div class="empty-state">
                <div class="empty-state-icon">✅</div>
                <div class="empty-state-title">No {category_type} Follow-ups</div>
                <p class="empty-state-desc">You are completely up to date with your applications in this category.</p>
            </div>
            """, unsafe_allow_html=True)
            return

        for idx, item in enumerate(items):
            app = item["application"]
            app_id = app.get("app_id", str(idx))
            company = app.get("company", "Company")
            title = app.get("title", "Position")
            applied = app.get("applied_date", "Not recorded")
            scheduled = app.get("follow_up_date", "")
            contact_name = app.get("contact_name", "")
            contact_email = app.get("contact_email", "")

            border_color = "#ef4444" if category_type == "Overdue" else ("#f59e0b" if category_type == "Due Today" else "#10b981")
            diff_text = f"{item.get('days_diff')} days overdue" if category_type == "Overdue" else (f"in {item.get('days_diff')} days" if category_type == "Upcoming" else "Due today")

            with st.container():
                st.markdown(f"""
                <div class="saas-card" style="border-left: 4px solid {border_color}; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <h4 style="margin: 0; font-size: 1.1rem; color: #0f172a;">{company}</h4>
                            <div style="font-weight: 600; color: #4f46e5; margin-top: 2px;">{title}</div>
                            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
                                Applied: {applied} &nbsp;•&nbsp; <strong>Follow-up Scheduled:</strong> {scheduled} ({diff_text})
                            </div>
                            {f'<div style="font-size: 11px; color: #475569; margin-top: 2px;">Contact: {contact_name} ({contact_email})</div>' if contact_name or contact_email else ''}
                        </div>
                        <span class="status-badge badge-{app.get('status', 'applied').lower()}">{app.get('status', 'Applied')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_act1, col_act2, col_act3 = st.columns([2, 1.5, 1.5])

                with col_act1:
                    with st.popover(f"📧 Draft Follow-Up Email", use_container_width=True):
                        st.markdown(f"**Follow-Up Draft for {company}**")
                        c_name_input = st.text_input("Recruiter Name", value=contact_name, key=f"fu_rec_{app_id}_{category_type}")
                        email_draft = generate_polite_follow_up_email(candidate_name, company, title, applied, c_name_input)
                        st.text_area("Email Content", value=email_draft, height=200, key=f"fu_text_{app_id}_{category_type}")
                        st.download_button(
                            "📥 Download Email (.txt)",
                            data=email_draft,
                            file_name=f"Followup_{company}_{title}.txt",
                            mime="text/plain",
                            key=f"dl_fu_{app_id}_{category_type}",
                            use_container_width=True
                        )

                with col_act2:
                    if st.button(f"📅 Postpone +7 Days", key=f"postpone_{app_id}_{category_type}", use_container_width=True):
                        new_date = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
                        update_application(username, app_id, {"follow_up_date": new_date})
                        st.success(f"Rescheduled for {new_date}")
                        st.rerun()

                with col_act3:
                    with st.popover("🔄 Update Status", use_container_width=True):
                        new_stat = st.selectbox("New Stage", STATUS_OPTIONS, index=STATUS_OPTIONS.index(app.get("status", "Applied")) if app.get("status") in STATUS_OPTIONS else 1, key=f"stat_sel_{app_id}_{category_type}")
                        if st.button("Save Status", key=f"btn_save_stat_{app_id}_{category_type}"):
                            update_application(username, app_id, {"status": new_stat})
                            st.rerun()

    with tab_overdue:
        render_follow_up_cards(overdue, "Overdue")

    with tab_today:
        render_follow_up_cards(today_items, "Due Today")

    with tab_upcoming:
        render_follow_up_cards(upcoming, "Upcoming")
