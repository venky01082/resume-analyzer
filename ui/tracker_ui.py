import streamlit as st
from datetime import date
from io import StringIO
import csv
from database.applications import (
    STATUS_OPTIONS,
    PRIORITY_OPTIONS,
    get_applications,
    create_application,
    update_application,
    delete_application,
    get_status_counts,
    get_overdue_follow_ups,
    get_today_follow_ups,
    migrate_legacy_applications,
)


def render_application_tracker():
    """
    Renders professional Job Application Tracking & Pipeline Management system
    with 9-stage pipeline statuses, follow-up notifications, inline stage updates,
    search & filters, and CSV export.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">📌</div>
            <div>
                <h1 class="app-title">Job Application Tracker & Pipeline</h1>
                <p class="app-subtitle">Track your 9-stage application lifecycle, manage recruiter communications, and meet follow-up deadlines.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    migrate_legacy_applications()
    username = st.session_state.get("auth_username", "venky")
    applications = get_applications(username)
    counts = get_status_counts(applications)
    overdue = get_overdue_follow_ups(applications)
    today_followups = get_today_follow_ups(applications)

    # Top Pipeline KPI Cards
    p1, p2, p3, p4, p5, p6 = st.columns(6)
    with p1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">📋 Total Saved</div>
            <div class="stat-value">{counts.get('Saved', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">📤 Applied</div>
            <div class="stat-value">{counts.get('Applied', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with p3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🔍 Screening</div>
            <div class="stat-value">{counts.get('Screening', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with p4:
        interview_sum = counts.get('Interview', 0) + counts.get('Technical Round', 0) + counts.get('HR Round', 0)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🎤 Interviews</div>
            <div class="stat-value" style="color: #4f46e5;">{interview_sum}</div>
        </div>
        """, unsafe_allow_html=True)
    with p5:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🎉 Offers</div>
            <div class="stat-value" style="color: #10b981;">{counts.get('Offer', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with p6:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">⏰ Overdue</div>
            <div class="stat-value" style="color: {'#dc2626' if overdue else '#64748b'};">{len(overdue)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Follow-Up Center Notification Alerts
    if overdue:
        for item in overdue[:2]:
            app_item = item["application"]
            st.error(f"🔴 **Overdue Follow-Up:** Contact **{app_item.get('company')}** regarding **{app_item.get('title')}** (Scheduled: {app_item.get('follow_up_date')})")
    elif today_followups:
        for item in today_followups[:2]:
            app_item = item["application"]
            st.warning(f"🟡 **Follow-Up Due Today:** Contact **{app_item.get('company')}** regarding **{app_item.get('title')}**")

    # Filter & Search Controls
    st.markdown("""
    <div class="saas-card" style="padding: 1rem 1.25rem; margin-bottom: 1.25rem;">
        <div style="font-weight: 700; color: #0f172a; margin-bottom: 0.5rem; font-size: 13px;">FILTER & SEARCH PIPELINE</div>
    """, unsafe_allow_html=True)

    f1, f2, f3 = st.columns([2, 2, 3])
    with f1:
        status_filter = st.selectbox("Status Filter", ["All"] + STATUS_OPTIONS, key="tracker_filter_status")
    with f2:
        priority_filter = st.selectbox("Priority Filter", ["All"] + PRIORITY_OPTIONS, key="tracker_filter_priority")
    with f3:
        search_query = st.text_input("Search by Company, Role or Location", key="tracker_search_query", placeholder="Search keywords...")
    st.markdown("</div>", unsafe_allow_html=True)

    # Filter Applications
    filtered = []
    for idx, item in enumerate(applications):
        searchable = f"{item.get('title', '')} {item.get('company', '')} {item.get('location', '')}".lower()
        if status_filter != "All" and item.get("status", "Saved") != status_filter:
            continue
        if priority_filter != "All" and item.get("priority", "Medium") != priority_filter:
            continue
        if search_query.strip() and search_query.strip().lower() not in searchable:
            continue
        filtered.append((idx, item))

    # Top Action Bar: Add Manual & Export CSV
    top_c1, top_c2 = st.columns([3, 1])
    with top_c1:
        st.write(f"Showing **{len(filtered)}** of **{len(applications)}** tracked applications.")
    with top_c2:
        if applications:
            buffer = StringIO()
            fields = [
                "title", "company", "location", "score", "status", "priority",
                "applied_date", "follow_up_date", "contact_name", "contact_email",
                "salary", "source", "notes", "application_url", "last_updated"
            ]
            writer = csv.DictWriter(buffer, fieldnames=fields)
            writer.writeheader()
            for app in applications:
                writer.writerow({f: app.get(f, "") for f in fields})
            st.download_button(
                "⬇️ Export CSV",
                data=buffer.getvalue(),
                file_name=f"job_applications_{username}.csv",
                mime="text/csv",
                use_container_width=True
            )

    # Manual Add Expander
    with st.expander("➕ Add Application Manually"):
        m_c1, m_c2 = st.columns(2)
        with m_c1:
            man_title = st.text_input("Job Role / Title *", key="man_add_title")
            man_company = st.text_input("Company Name *", key="man_add_company")
            man_loc = st.text_input("Location", value="India", key="man_add_loc")
            man_url = st.text_input("Application Portal URL", key="man_add_url")
        with m_c2:
            man_status = st.selectbox("Current Pipeline Stage", STATUS_OPTIONS, index=0, key="man_add_status")
            man_priority = st.selectbox("Priority Level", PRIORITY_OPTIONS, index=1, key="man_add_priority")
            man_score = st.number_input("Match Score %", 0, 100, 70, key="man_add_score")
            man_salary = st.text_input("Expected Compensation", key="man_add_salary")
        man_notes = st.text_area("Application Notes / Contacts", key="man_add_notes")

        if st.button("Save New Application", type="primary", key="btn_save_manual_app"):
            if not man_title.strip() or not man_company.strip():
                st.warning("Job title and company name are required.")
            else:
                ok = create_application(
                    user_id=username,
                    title=man_title.strip(),
                    company=man_company.strip(),
                    location=man_loc.strip(),
                    score=man_score,
                    application_url=man_url.strip(),
                    status=man_status,
                    priority=man_priority,
                    salary=man_salary.strip(),
                    notes=man_notes.strip()
                )
                if ok:
                    st.success("✅ Application successfully added to your tracker!")
                    st.rerun()
                else:
                    st.info("This application already exists in your pipeline.")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Applications List Rendering
    if not filtered:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📋</div>
            <div class="empty-state-title">No Applications Found</div>
            <p class="empty-state-desc">Try adjusting your filters or search terms, or add a new job application above.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for idx, item in filtered:
            app_id = item.get("app_id")
            status = item.get("status", "Saved")
            priority = item.get("priority", "Medium")
            score = item.get("score", 0)
            url = item.get("application_url", "")
            badge_class = f"badge-{status.lower().replace(' ', '-')}"
            p_class = f"priority-{priority.lower()}"

            with st.container():
                st.markdown(f"""
                <div class="saas-card" style="margin-bottom: 0.85rem;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <h3 class="job-title" style="margin: 0;">{item.get('title', 'Position')}</h3>
                            <div class="job-company">🏢 {item.get('company', 'Company')} &nbsp;•&nbsp; 📍 {item.get('location', 'N/A')}</div>
                        </div>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <span class="status-badge {badge_class}">{status}</span>
                            <span class="{p_class}" style="font-size: 12px; background: #f8fafc; padding: 2px 8px; border-radius: 4px; border: 1px solid #e2e8f0;">● {priority}</span>
                            <span style="font-weight: 700; color: #4f46e5; font-size: 13px;">🎯 {score}%</span>
                        </div>
                    </div>
                    <div style="font-size: 12px; color: #64748b; margin-top: 6px; display: flex; gap: 16px; flex-wrap: wrap;">
                        <span>📅 Applied: {item.get('applied_date') or 'Not specified'}</span>
                        <span>⏰ Follow-up: {item.get('follow_up_date') or 'None scheduled'}</span>
                        {f'<span>👤 Recruiter: {item.get("contact_name")}</span>' if item.get("contact_name") else ''}
                        {f'<span>💰 Salary: {item.get("salary")}</span>' if item.get("salary") else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"✏️ Manage & Update Stage — {item.get('company')}"):
                    e_c1, e_c2 = st.columns(2)
                    with e_c1:
                        new_status = st.selectbox(
                            "Update Pipeline Stage",
                            STATUS_OPTIONS,
                            index=STATUS_OPTIONS.index(status) if status in STATUS_OPTIONS else 0,
                            key=f"edit_status_{idx}"
                        )
                        new_priority = st.selectbox(
                            "Priority Level",
                            PRIORITY_OPTIONS,
                            index=PRIORITY_OPTIONS.index(priority) if priority in PRIORITY_OPTIONS else 1,
                            key=f"edit_priority_{idx}"
                        )
                        new_applied = st.text_input(
                            "Applied Date (YYYY-MM-DD)",
                            value=item.get("applied_date", ""),
                            key=f"edit_applied_{idx}"
                        )
                        new_followup = st.text_input(
                            "Follow-Up Date (YYYY-MM-DD)",
                            value=item.get("follow_up_date", ""),
                            key=f"edit_followup_{idx}"
                        )
                    with e_c2:
                        new_contact = st.text_input("Contact Recruiter Name", value=item.get("contact_name", ""), key=f"edit_contact_{idx}")
                        new_email = st.text_input("Contact Email", value=item.get("contact_email", ""), key=f"edit_email_{idx}")
                        new_salary = st.text_input("Salary / Compensation", value=item.get("salary", ""), key=f"edit_salary_{idx}")
                        new_url = st.text_input("Job URL", value=url, key=f"edit_url_{idx}")
                    new_notes = st.text_area("Notes & Interview Logs", value=item.get("notes", ""), key=f"edit_notes_{idx}")

                    # Status History Timeline
                    from database.repository import get_status_history
                    history = get_status_history(username, app_id) if app_id else []
                    if history:
                        st.markdown("<div style='font-size: 11.5px; font-weight: 700; color: #64748b; margin-top: 8px;'>📜 Status Progression History:</div>", unsafe_allow_html=True)
                        for h in history[-4:]:
                            st.markdown(f"<div style='font-size: 12px; color: #475569; padding-left: 6px;'>• <strong>{h.get('changed_at', '')[:16]}</strong>: <span style='color: #4f46e5; font-weight: 600;'>{h.get('status')}</span> — {h.get('notes')}</div>", unsafe_allow_html=True)

                    act_c1, act_c2, act_c3 = st.columns([1, 1, 1])
                    with act_c1:
                        if st.button("💾 Save Changes", key=f"save_edit_{idx}", type="primary", use_container_width=True):
                            ok = update_application(
                                user_id=username,
                                identifier=app_id or idx,
                                status=new_status,
                                priority=new_priority,
                                applied_date=new_applied.strip(),
                                follow_up_date=new_followup.strip(),
                                notes=new_notes.strip(),
                                contact_name=new_contact.strip(),
                                contact_email=new_email.strip(),
                                salary=new_salary.strip()
                            )
                            if ok:
                                st.success("Updated application record!")
                                st.rerun()
                    with act_c2:
                        if url:
                            st.link_button("🔗 Open Job Portal", url, use_container_width=True)
                    with act_c3:
                        if st.button("🗑️ Delete Record", key=f"del_app_{idx}", use_container_width=True):
                            delete_application(user_id=username, identifier=app_id or idx)
                            st.success("Deleted from tracker.")
                            st.rerun()

