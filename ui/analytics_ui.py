import streamlit as st
import pandas as pd
from core_logic import step17_analytics
from database.applications import get_applications
from database.analytics import calculate_user_analytics


def render_analytics():
    """
    Renders modern Application Analytics dashboard with
    user-scoped conversion rates, full pipeline distribution, monthly trends,
    and strategic recommendations based on real user data.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">📊</div>
            <div>
                <h1 class="app-title">Application Analytics & Insights</h1>
                <p class="app-subtitle">Real-time performance metrics, conversion funnels, and trends from your personal pipeline.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    username = st.session_state.get("auth_username", "venky")
    applications = get_applications(username)

    if not applications:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📊</div>
            <div class="empty-state-title">No Application Data Available</div>
            <p class="empty-state-desc">
                Add or save jobs to your tracker to generate real-time pipeline analytics, conversion rates, and company trends.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Search & Save Jobs →", type="primary"):
            st.session_state.current_page = "job_search"
            st.rerun()
        return

    # Calculate real factual analytics
    user_metrics = calculate_user_analytics(username)
    legacy_data = step17_analytics(applications)

    # Top KPI Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">📋 Tracked Roles</div>
            <div class="stat-value">{user_metrics['total_applications']}</div>
            <div class="stat-subtext-neutral">Total opportunities</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">📤 Submitted</div>
            <div class="stat-value">{user_metrics['submitted_applications']}</div>
            <div class="stat-subtext-neutral">Applied & in-review</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">⚡ Response Rate</div>
            <div class="stat-value" style="color: #4f46e5;">{user_metrics['response_rate']}%</div>
            <div class="stat-subtext-neutral">{user_metrics['active_interviews'] + user_metrics['total_offers'] + user_metrics['total_rejections']} responses</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🎤 Interview Rate</div>
            <div class="stat-value" style="color: #0284c7;">{user_metrics['interview_rate']}%</div>
            <div class="stat-subtext-neutral">{user_metrics['active_interviews']} rounds invited</div>
        </div>
        """, unsafe_allow_html=True)
    with m5:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🎯 Avg Match</div>
            <div class="stat-value" style="color: #10b981;">{user_metrics['avg_match_score']}%</div>
            <div class="stat-subtext-neutral">Across tracked roles</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Conversion Funnel Visual
    st.markdown("""
    <div class="saas-card" style="margin-bottom: 1.25rem;">
        <div class="saas-card-header">🚀 Application Conversion Funnel</div>
        <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; text-align: center; margin-top: 10px;">
            <div style="background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0;">
                <div style="font-size: 11px; font-weight: 700; color: #64748b;">1. SAVED</div>
                <div style="font-size: 20px; font-weight: 800; color: #0f172a;">{status_counts.get('Saved', 0)}</div>
            </div>
            <div style="background: #eff6ff; padding: 12px; border-radius: 8px; border: 1px solid #bfdbfe;">
                <div style="font-size: 11px; font-weight: 700; color: #1e40af;">2. APPLIED</div>
                <div style="font-size: 20px; font-weight: 800; color: #1e40af;">{status_counts.get('Applied', 0)}</div>
            </div>
            <div style="background: #f0fdf4; padding: 12px; border-radius: 8px; border: 1px solid #bbf7d0;">
                <div style="font-size: 11px; font-weight: 700; color: #166534;">3. SCREENING</div>
                <div style="font-size: 20px; font-weight: 800; color: #166534;">{status_counts.get('Screening', 0)}</div>
            </div>
            <div style="background: #eef2ff; padding: 12px; border-radius: 8px; border: 1px solid #c7d2fe;">
                <div style="font-size: 11px; font-weight: 700; color: #4338ca;">4. INTERVIEWS</div>
                <div style="font-size: 20px; font-weight: 800; color: #4338ca;">{user_metrics['active_interviews']}</div>
            </div>
            <div style="background: #ecfdf5; padding: 12px; border-radius: 8px; border: 1px solid #a7f3d0;">
                <div style="font-size: 11px; font-weight: 700; color: #065f46;">5. OFFERS</div>
                <div style="font-size: 20px; font-weight: 800; color: #065f46;">{user_metrics['total_offers']}</div>
            </div>
        </div>
    </div>
    """.format(
        status_counts=user_metrics['status_distribution'],
        user_metrics=user_metrics
    ), unsafe_allow_html=True)

    # Charts Row: Status Distribution & Monthly Trends
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">📊 Applications by Pipeline Stage</div>
        """, unsafe_allow_html=True)
        status_dict = user_metrics["status_distribution"]
        df_status = pd.DataFrame(list(status_dict.items()), columns=["Stage", "Count"])
        df_status = df_status[df_status["Count"] > 0]
        if not df_status.empty:
            st.bar_chart(df_status.set_index("Stage"))
        else:
            st.info("No status data to visualize.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">📅 Monthly Application Activity</div>
        """, unsafe_allow_html=True)
        monthly_counts = legacy_data.get("monthly_counts", {})
        if monthly_counts:
            df_monthly = pd.DataFrame(list(monthly_counts.items()), columns=["Month", "Applications"]).sort_values("Month")
            st.line_chart(df_monthly.set_index("Month"))
        else:
            st.info("Set 'Applied Date' on applications in the tracker to see monthly velocity trends.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Top Companies & Priority Breakdown
    b_left, b_right = st.columns(2)

    with b_left:
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">🏢 Top Companies in Pipeline</div>
        """, unsafe_allow_html=True)
        company_counts = user_metrics.get("top_companies", {})
        if company_counts:
            df_comp = pd.DataFrame(list(company_counts.items()), columns=["Company", "Count"]).sort_values("Count", ascending=False).head(6)
            for _, row in df_comp.iterrows():
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #f1f5f9; font-size: 13px;">
                    <span style="font-weight: 600; color: #1e293b;">🏢 {row['Company']}</span>
                    <span style="background: #eef2ff; color: #4338ca; padding: 2px 8px; border-radius: 99px; font-weight: 700; font-size: 11px;">{row['Count']} roles</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No company data found.")
        st.markdown("</div>", unsafe_allow_html=True)

    with b_right:
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">🚨 Applications by Priority</div>
        """, unsafe_allow_html=True)
        p_counts = legacy_data.get("priority_counts", {})
        st.markdown(f"""
        <div style="display: flex; flex-direction: column; gap: 8px; font-size: 13px; margin-top: 6px;">
            <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: #fef2f2; border-radius: 8px;">
                <span style="color: #dc2626; font-weight: 700;">🔴 High Priority</span>
                <span style="font-weight: 800; color: #dc2626;">{p_counts.get('High', 0)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: #fffbeb; border-radius: 8px;">
                <span style="color: #d97706; font-weight: 700;">🟡 Medium Priority</span>
                <span style="font-weight: 800; color: #d97706;">{p_counts.get('Medium', 0)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: #f0fdf4; border-radius: 8px;">
                <span style="color: #16a34a; font-weight: 700;">🟢 Low Priority</span>
                <span style="font-weight: 800; color: #16a34a;">{p_counts.get('Low', 0)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Strategy Recommendations
    st.markdown("""
    <div class="saas-card">
        <div class="saas-card-header">💡 Personalized Career Recommendations</div>
    """, unsafe_allow_html=True)
    
    recs = []
    if user_metrics['submitted_applications'] < 5:
        recs.append("Increase your weekly application volume to build statistical momentum across hiring cycles.")
    if user_metrics['avg_match_score'] < 65:
        recs.append("Tailor your resume keywords before applying to increase callback rates above 75%.")
    if user_metrics['interview_rate'] > 20:
        recs.append("High interview conversion! Focus heavily on technical round and coding assessment preparations.")
    if user_metrics['total_offers'] > 0:
        recs.append("Congratulations on receiving offers! Compare compensation packages and benefits before finalizing.")
    if not recs:
        recs.append("Your application velocity is consistent. Keep monitoring upcoming follow-up dates in the Follow-Up Center.")

    for r in recs:
        st.markdown(f"""
        <div style="padding: 6px 0; display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: #334155;">
            <span style="color: #4f46e5;">•</span>
            <span>{r}</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

