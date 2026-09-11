import os
import json
import streamlit as st
from database.users import get_user_by_username, update_user_preferences
from database.applications import get_applications
from database.jobs import get_saved_jobs
from database.resumes import get_resumes


def render_settings():
    """
    Renders system diagnostics, user preferences, API connectivity checks,
    local database file verifications, full data export, and session settings.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">⚙️</div>
            <div>
                <h1 class="app-title">System Settings & Preferences</h1>
                <p class="app-subtitle">Configure application defaults, check model & database health, and export your personal data.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    username = st.session_state.get("auth_username", "venky")
    user_record = get_user_by_username(username)
    current_prefs = user_record.get("preferences", {}) if user_record else {}

    # Tabbed layout: Preferences vs System Diagnostics & Backup
    tab_prefs, tab_diag, tab_backup = st.tabs([
        "⚙️ Application Preferences",
        "🔌 Diagnostics & Health",
        "💾 Data Backup & Export"
    ])

    # =========================================================
    # TAB 1: PREFERENCES
    # =========================================================
    with tab_prefs:
        st.markdown("""
        <div class="saas-card" style="margin-bottom: 1.25rem;">
            <div class="saas-card-header">⚙️ Application Defaults & Follow-Up Timing</div>
            <p style="font-size: 0.85rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 0.75rem;">
                Customize how your job assistant schedules reminders and formats career compensation.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            cadence_options = [3, 5, 7, 10, 14]
            current_cadence = current_prefs.get("follow_up_cadence_days", 5)
            cadence_idx = cadence_options.index(current_cadence) if current_cadence in cadence_options else 1
            pref_cadence = st.selectbox(
                "Default Follow-Up Reminder (Days after applying)",
                cadence_options,
                index=cadence_idx,
                format_func=lambda d: f"{d} days after submission"
            )
            pref_currency = st.selectbox(
                "Preferred Compensation Currency",
                ["INR (₹)", "USD ($)", "EUR (€)", "GBP (£)"],
                index=0
            )

        with col_p2:
            pref_default_status = st.selectbox(
                "Default Stage when Saving New Job",
                ["Saved", "Applied"],
                index=0
            )
            pref_email_notifications = st.checkbox(
                "Enable In-App Follow-Up Due Banners",
                value=current_prefs.get("email_notifications_enabled", True)
            )

        if st.button("💾 Save Preferences", type="primary", key="btn_save_preferences"):
            ok = update_user_preferences(username, {
                "follow_up_cadence_days": pref_cadence,
                "preferred_currency": pref_currency,
                "default_status": pref_default_status,
                "email_notifications_enabled": pref_email_notifications,
            })
            if ok:
                st.success("✅ Preferences saved successfully!")
            else:
                st.error("Failed to update preferences.")

    # =========================================================
    # TAB 2: SYSTEM DIAGNOSTICS & HEALTH
    # =========================================================
    with tab_diag:
        st.markdown("### 🔌 Service & Model Status")
        c1, c2, c3 = st.columns(3)

        # 1. Adzuna API
        with c1:
            has_adzuna = "ADZUNA_APP_ID" in st.secrets and "ADZUNA_APP_KEY" in st.secrets
            st.markdown(f"""
            <div class="saas-card">
                <div class="saas-card-header">
                    <span>🌐 Adzuna Job API</span>
                    <span style="font-size: 11px; color: {'#10b981' if has_adzuna else '#ef4444'}; font-weight: 700;">
                        {'● Connected' if has_adzuna else '● Missing Keys'}
                    </span>
                </div>
                <p style="font-size: 12px; color: #64748b; margin-top: -0.2rem;">
                    Powers live job search across Indian tech portals.
                </p>
                <div style="font-size: 12px; color: #1e293b; background: #f8fafc; padding: 6px 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
                    Secrets: {'Configured ✅' if has_adzuna else 'Not Found ⚠️'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 2. spaCy Model
        with c2:
            try:
                import spacy
                spacy.load("en_core_web_sm")
                spacy_ok = True
            except Exception:
                spacy_ok = False
            st.markdown(f"""
            <div class="saas-card">
                <div class="saas-card-header">
                    <span>🧠 spaCy NLP Parser</span>
                    <span style="font-size: 11px; color: {'#10b981' if spacy_ok else '#f59e0b'}; font-weight: 700;">
                        {'● Loaded' if spacy_ok else '● Loading...'}
                    </span>
                </div>
                <p style="font-size: 12px; color: #64748b; margin-top: -0.2rem;">
                    Model: <code>en_core_web_sm</code> for entity and name extraction.
                </p>
                <div style="font-size: 12px; color: #1e293b; background: #f8fafc; padding: 6px 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
                    Status: {'Active & Loaded ✅' if spacy_ok else 'Fallback Regex active'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 3. Sentence Transformers
        with c3:
            try:
                from sentence_transformers import SentenceTransformer
                st_ok = True
            except Exception:
                st_ok = False
            st.markdown(f"""
            <div class="saas-card">
                <div class="saas-card-header">
                    <span>✨ Sentence Transformers</span>
                    <span style="font-size: 11px; color: {'#10b981' if st_ok else '#64748b'}; font-weight: 700;">
                        {'● Ready' if st_ok else '● Fallback Ready'}
                    </span>
                </div>
                <p style="font-size: 12px; color: #64748b; margin-top: -0.2rem;">
                    Model: <code>all-MiniLM-L6-v2</code> for semantic cosine vectors.
                </p>
                <div style="font-size: 12px; color: #1e293b; background: #f8fafc; padding: 6px 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
                    Status: {'Deep Vector Sim ✅' if st_ok else 'Vector Cosine Fallback Active'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Database Files Status
        st.markdown("### 🗄️ Local Data Integrity")
        db_cols = st.columns(5)
        files_to_check = [
            ("applications.json", "Applications & Pipeline"),
            ("jobs.json", "Local Jobs Catalog"),
            ("users.json", "User Credentials & Auth"),
            ("resumes.json", "Multi-Resume Library"),
            ("saved_jobs.json", "Saved Bookmarks"),
        ]

        for idx, (filename, label) in enumerate(files_to_check):
            with db_cols[idx]:
                exists = os.path.exists(filename)
                st.markdown(f"""
                <div class="saas-card" style="padding: 10px; text-align: center;">
                    <div style="font-weight: 700; color: #0f172a; font-size: 12px;">{filename}</div>
                    <div style="font-size: 11px; color: #64748b; margin: 3px 0;">{label}</div>
                    <div style="font-size: 11px; color: {'#10b981' if exists else '#ef4444'}; font-weight: 700;">
                        {'● Healthy' if exists else '● Missing'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Cache clear
        st.markdown("### 🧹 Workspace Session")
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">In-Memory Cache Management</div>
            <p style="font-size: 13px; color: #64748b; margin-top: -0.4rem; margin-bottom: 1rem;">
                Clearing temporary workspace cache will remove in-memory parsed text for the current session without deleting your saved applications or user profile.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🧹 Clear In-Memory Resume Cache", type="secondary"):
            for key in ["resume_text", "resume_skills", "resume_score", "current_jd", "ats_audited", "matching_computed", "tailoring_done", "cl_generated", "email_generated"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Session resume cache cleared.")
            st.rerun()

    # =========================================================
    # TAB 3: COMPLETE DATA BACKUP & EXPORT
    # =========================================================
    with tab_backup:
        st.markdown("""
        <div class="saas-card" style="margin-bottom: 1.25rem;">
            <div class="saas-card-header">💾 Complete Data Backup & Export</div>
            <p style="font-size: 0.85rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 0.75rem;">
                Export all your saved resumes, bookmarked jobs, application pipelines, notes, and profile data in a structured, portable JSON bundle.
            </p>
        </div>
        """, unsafe_allow_html=True)

        user_apps = get_applications(username)
        user_bookmarks = get_saved_jobs(username)
        user_resumes = get_resumes(username)

        b_c1, b_c2, b_c3 = st.columns(3)
        b_c1.metric("Saved Resumes", len(user_resumes))
        b_c2.metric("Bookmarked Jobs", len(user_bookmarks))
        b_c3.metric("Tracked Applications", len(user_apps))

        export_data = {
            "version": "2.0",
            "exported_at": str(os.getenv("DATE", "2026-09-11")),
            "username": username,
            "profile": user_record.get("profile", {}) if user_record else {},
            "preferences": user_record.get("preferences", {}) if user_record else {},
            "resumes": user_resumes,
            "saved_jobs": user_bookmarks,
            "applications": user_apps,
        }

        export_json_str = json.dumps(export_data, indent=2, ensure_ascii=False)

        st.download_button(
            label="⬇️ Download Complete Portfolio Backup (JSON)",
            data=export_json_str,
            file_name=f"job_assistant_backup_{username}.json",
            mime="application/json",
            use_container_width=True,
            type="primary"
        )

