import streamlit as st
from real_jobs import get_real_jobs
from core_logic import (
    load_jobs,
    recommend_jobs,
    extract_job_skills,
    compare_skills,
    calculate_match_score,
    add_application,
    auth_get_profile,
)
from database.jobs import save_job, is_job_saved


def render_job_search():
    """
    Renders modern Job Search & Discovery workspace with
    support for Adzuna Live Job Search API, Local Jobs Database,
    and Personalized Role Recommendations based on user profile.
    Presents jobs as modern cards with match scores, salary, bookmarks, and tracker save.
    """
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">🔎</div>
            <div>
                <h1 class="app-title">Job Search & Matching</h1>
                <p class="app-subtitle">Discover live roles, calculate resume fit, bookmark favorites, and track applications.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    username = st.session_state.get("auth_username", "venky")
    profile = auth_get_profile(username) if username else {}
    target_roles = profile.get("target_roles", "Data Analyst")
    default_role = target_roles.split(",")[0].strip() if target_roles else "Data Analyst"
    default_location = profile.get("preferred_location") or "India"

    resume_skills = st.session_state.get("resume_skills", [])

    tab_real, tab_local, tab_rec = st.tabs([
        "🌐 Live Job Search (Adzuna)",
        "💼 Local Opportunity Catalog",
        "✨ Recommended For You"
    ])

    # =========================================================
    # TAB 1: LIVE REAL JOB SEARCH
    # =========================================================
    with tab_real:
        st.markdown("""
        <div class="saas-card" style="margin-bottom: 1.25rem;">
            <div class="saas-card-header">🔎 Search Live Listings</div>
            <p style="font-size: 0.85rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 0.75rem;">
                Search across active hiring portals and instantly compute matching percentages against your resume skills.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_role, col_loc, col_num = st.columns([3, 2, 1])
        with col_role:
            keyword = st.text_input("Job Role / Keywords", value=default_role, key="real_search_role")
        with col_loc:
            location = st.text_input("Location", value=default_location, key="real_search_location")
        with col_num:
            job_count = st.selectbox("Results", [10, 20, 30, 50], index=1, key="real_search_count")

        if st.button("🔎 Search Live Jobs", type="primary", key="btn_search_live_jobs"):
            if not keyword.strip():
                st.warning("Please specify a job role to search.")
            else:
                has_api_keys = "ADZUNA_APP_ID" in st.secrets and "ADZUNA_APP_KEY" in st.secrets
                if not has_api_keys:
                    st.warning("⚠️ **Adzuna API Credentials Not Configured**: Live search requires `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` in `.streamlit/secrets.toml`. You can still browse curated jobs in the 'Local Opportunity Catalog' tab!")
                
                try:
                    with st.spinner(f"Fetching real jobs for '{keyword}' in '{location}'..."):
                        results = get_real_jobs(keyword.strip(), location.strip(), results_per_page=job_count)
                    
                    matched_jobs = []
                    for job in results:
                        job_text = job.get("title", "") + " " + job.get("description", "")
                        job_skills = extract_job_skills(job_text)
                        matching, missing = compare_skills(resume_skills, job_skills)
                        score = calculate_match_score(matching, job_skills)
                        matched_jobs.append({
                            "job": job,
                            "score": score,
                            "matching": matching,
                            "missing": missing
                        })
                    
                    matched_jobs.sort(key=lambda x: x["score"], reverse=True)
                    st.session_state.live_search_results = matched_jobs
                    if matched_jobs:
                        st.success(f"Found {len(matched_jobs)} live job postings!")
                    else:
                        st.info(f"No postings found for '{keyword}' in '{location}'. Try adjusting keywords or location.")
                except Exception as err:
                    st.error(f"Live job search temporarily unavailable: {err}. Please check your internet connection or browse local jobs.")

        # Display Live Search Results
        live_results = st.session_state.get("live_search_results", [])
        if live_results:
            st.markdown(f"#### 🎯 Matching Results ({len(live_results)})")
            for idx, item in enumerate(live_results, start=1):
                job = item["job"]
                score = item["score"]
                matching = item["matching"]
                missing = item["missing"]
                salary_min = job.get("salary_min")
                salary_max = job.get("salary_max")
                url = job.get("application_url", "")
                is_saved = is_job_saved(username, job.get("title", ""), job.get("company", ""))

                score_color = "#10b981" if score >= 75 else ("#4f46e5" if score >= 50 else "#64748b")
                
                with st.container():
                    st.markdown(f"""
                    <div class="job-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <h3 class="job-title">{idx}. {job.get('title', 'Unknown Job')}</h3>
                                <div class="job-company">🏢 {job.get('company', 'Unknown')} &nbsp;•&nbsp; 📍 {job.get('location', 'India')}</div>
                            </div>
                            <span style="background: #f8fafc; color: {score_color}; font-weight: 800; font-size: 14px; padding: 4px 12px; border-radius: 99px; border: 1px solid #e2e8f0;">
                                🎯 {score}% Match
                            </span>
                        </div>
                        <div class="job-meta-row">
                            {'<span>💼 ' + str(job.get('contract_type')) + '</span>' if job.get('contract_type') else ''}
                            {'<span>💰 Salary: ' + str(salary_min or 'N/A') + ' - ' + str(salary_max or 'N/A') + '</span>' if (salary_min or salary_max) else ''}
                        </div>
                        <div style="margin: 8px 0;">
                            <div style="font-size: 12px; font-weight: 600; color: #475569;">Matching Skills:</div>
                            <div class="chip-container">
                                {''.join([f'<span class="skill-chip skill-chip-match">✓ {s}</span>' for s in matching]) if matching else '<span style="font-size: 12px; color: #94a3b8;">Upload resume to calculate skills</span>'}
                            </div>
                        </div>
                        {'''
                        <div style="margin: 8px 0;">
                            <div style="font-size: 12px; font-weight: 600; color: #991b1b;">Missing Skills:</div>
                            <div class="chip-container">
                                ''' + ''.join([f'<span class="skill-chip skill-chip-missing">+ {s}</span>' for s in missing[:6]]) + '''
                            </div>
                        </div>
                        ''' if missing else ''}
                    </div>
                    """, unsafe_allow_html=True)

                    if job.get("description"):
                        with st.expander("📋 View Job Description"):
                            st.write(job.get("description"))

                    b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
                    with b1:
                        if url:
                            st.link_button("🔗 Apply Live", url, use_container_width=True)
                    with b2:
                        if st.button("⭐ Bookmark Job", key=f"bookmark_live_job_{idx}", use_container_width=True, disabled=is_saved):
                            ok, msg = save_job(username, {
                                "title": job.get("title", "Unknown"),
                                "company": job.get("company", "Unknown"),
                                "location": job.get("location", "India"),
                                "salary": f"{salary_min or ''} - {salary_max or ''}".strip(" -"),
                                "url": url,
                                "description": job.get("description", ""),
                                "match_score": score,
                                "matching_skills": matching,
                                "missing_skills": missing,
                            })
                            if ok:
                                st.success("⭐ Saved to bookmarks!")
                                st.rerun()
                            else:
                                st.info(msg)
                    with b3:
                        if st.button("🚀 Track Application", key=f"track_live_job_{idx}", use_container_width=True):
                            ok = add_application(
                                title=job.get("title", "Unknown"),
                                company=job.get("company", "Unknown"),
                                location=job.get("location", "India"),
                                score=score,
                                application_url=url,
                                status="Saved",
                                user_id=username
                            )
                            if ok:
                                st.success("🚀 Added to Application Tracker!")
                                st.rerun()
                            else:
                                st.info("Already tracked in your pipeline.")
                    with b4:
                        if st.button("🎙️ Practice Interview", key=f"interview_live_job_{idx}", use_container_width=True):
                            st.session_state.interview_selected_job = {
                                "title": job.get("title", "Unknown"),
                                "company": job.get("company", "Unknown"),
                                "description": job.get("description", ""),
                                "skills": job.get("skills", []),
                                "matching_skills": matching,
                            }
                            st.session_state.current_page = "mock_interview"
                            st.rerun()

    # =========================================================
    # TAB 2: LOCAL JOB DATABASE
    # =========================================================
    with tab_local:
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-header">💼 Local Opportunity Catalog</div>
            <p style="font-size: 0.85rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 0.75rem;">
                Curated pre-configured opportunities ranked by your skills compatibility.
            </p>
        </div>
        """, unsafe_allow_html=True)

        try:
            local_jobs = load_jobs()
            fc1, fc2 = st.columns([2, 2])
            with fc1:
                min_score = st.slider("Filter by Minimum Match Score", 0, 100, 30, 5, key="local_min_score_filter")
            with fc2:
                local_filter_query = st.text_input("Filter Catalog Keywords", placeholder="e.g. Python, Analyst, Remote...", key="local_filter_kw")

            recommendations = recommend_jobs(resume_skills, local_jobs)
            filtered_jobs = []
            for r in recommendations:
                if r["score"] < min_score:
                    continue
                if local_filter_query.strip():
                    j_text = f"{r['job'].get('title', '')} {r['job'].get('company', '')} {r['job'].get('location', '')}".lower()
                    if local_filter_query.strip().lower() not in j_text:
                        continue
                filtered_jobs.append(r)

            st.markdown(f"#### Showing {len(filtered_jobs)} matching roles:")
            for idx, rec in enumerate(filtered_jobs, start=1):
                job = rec["job"]
                score = rec["score"]
                matching = rec.get("matching_skills", [])
                missing = rec.get("missing_skills", [])
                url = job.get("application_url") or job.get("redirect_url") or ""
                is_saved = is_job_saved(username, job.get("title", ""), job.get("company", ""))

                with st.container():
                    st.markdown(f"""
                    <div class="job-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <h3 class="job-title">{idx}. {job.get('title', 'Unknown Job')}</h3>
                                <div class="job-company">🏢 {job.get('company', 'Unknown')} &nbsp;•&nbsp; 📍 {job.get('location', 'India')}</div>
                            </div>
                            <span style="background: #eff6ff; color: #1e40af; font-weight: 800; font-size: 14px; padding: 4px 12px; border-radius: 99px; border: 1px solid #bfdbfe;">
                                🎯 {score}% Match
                            </span>
                        </div>
                        <div class="chip-container">
                            {''.join([f'<span class="skill-chip skill-chip-match">✓ {s}</span>' for s in matching])}
                            {''.join([f'<span class="skill-chip skill-chip-missing">+ {s}</span>' for s in missing[:5]])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    b1, b2, b3 = st.columns([1, 1, 1])
                    with b1:
                        if url:
                            st.link_button("🔗 Apply", url, use_container_width=True)
                    with b2:
                        if st.button("⭐ Bookmark", key=f"save_local_job_{idx}", use_container_width=True, disabled=is_saved):
                            ok, msg = save_job(username, {
                                "title": job.get("title", "Unknown"),
                                "company": job.get("company", "Unknown"),
                                "location": job.get("location", "India"),
                                "url": url,
                                "match_score": score,
                                "matching_skills": matching,
                                "missing_skills": missing,
                            })
                            if ok:
                                st.success("⭐ Saved to bookmarks!")
                                st.rerun()
                            else:
                                st.info(msg)
                    with b3:
                        if st.button("🚀 Track", key=f"track_local_job_{idx}", use_container_width=True):
                            ok = add_application(
                                title=job.get("title", "Unknown"),
                                company=job.get("company", "Unknown"),
                                location=job.get("location", "India"),
                                score=score,
                                application_url=url,
                                status="Saved",
                                user_id=username
                            )
                            if ok:
                                st.success("🚀 Added to Tracker!")
                                st.rerun()
                            else:
                                st.info("Already tracked in your pipeline.")
        except Exception as err:
            st.error(f"Error loading local jobs: {err}")

    # =========================================================
    # TAB 3: PERSONALIZED RECOMMENDATIONS
    # =========================================================
    with tab_rec:
        st.markdown("""
        <div class="saas-card" style="margin-bottom: 1rem;">
            <div class="saas-card-header">✨ Intelligent Career Recommendations</div>
            <p style="font-size: 0.85rem; color: #64748b; margin-top: -0.4rem; margin-bottom: 0.75rem;">
                Ranked specifically for you by evaluating your preferred target roles, location, and verified resume skills.
            </p>
        </div>
        """, unsafe_allow_html=True)

        pref_c1, pref_c2 = st.columns(2)
        pref_c1.info(f"🎯 **Target Roles Profile:** {target_roles or 'Not specified'}")
        pref_c2.info(f"📍 **Preferred Location:** {default_location}")

        try:
            from services.job_recommendation import recommend_jobs_for_user
            from services.job_sources import fetch_local_catalog_jobs
            catalog = fetch_local_catalog_jobs()
            scored_recs = recommend_jobs_for_user(username, catalog, limit=10)

            st.markdown(f"#### Top {len(scored_recs)} Personalized AI Opportunities:")
            for idx, rec in enumerate(scored_recs, start=1):
                job = rec["job"]
                score = rec["score"]
                expl = rec.get("explanation", {})
                matching = expl.get("matching_skills", [])
                missing = expl.get("missing_skills", [])
                why_list = expl.get("why_match", [])
                miss_list = expl.get("what_is_missing", [])
                url = job.get("application_url") or job.get("redirect_url") or ""

                st.markdown(f"""
                <div class="saas-card" style="margin-bottom: 0.85rem;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <div style="font-size: 15.5px; font-weight: 700; color: #0f172a;">{idx}. {job.get('title')}</div>
                            <div style="font-size: 12.5px; color: #64748b; margin-top: 2px;">🏢 {job.get('company')} &nbsp;•&nbsp; 📍 {job.get('location', 'India')} &nbsp;•&nbsp; 🏷️ {job.get('remote_status', 'Unspecified')}</div>
                        </div>
                        <span style="background: #ecfdf5; color: #065f46; font-weight: 800; font-size: 13px; padding: 3px 12px; border-radius: 99px; border: 1px solid #a7f3d0;">
                            🎯 {score}% Recommendation Fit
                        </span>
                    </div>
                """, unsafe_allow_html=True)

                if why_list:
                    st.markdown(f"<div style='font-size: 12px; color: #047857; margin-top: 6px;'><strong>✓ Why You Match:</strong> {' '.join(why_list)}</div>", unsafe_allow_html=True)
                if miss_list:
                    st.markdown(f"<div style='font-size: 12px; color: #b45309; margin-top: 4px;'><strong>⚠️ Missing Requirements:</strong> {' '.join(miss_list)}</div>", unsafe_allow_html=True)

                if matching:
                    st.markdown(f"""
                    <div class="chip-container" style="margin-top: 8px;">
                        {''.join([f'<span class="skill-chip skill-chip-match">✓ {s}</span>' for s in matching[:6]])}
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

                c_a1, c_a2, c_a3, c_a4 = st.columns([1, 1, 1, 1])
                with c_a1:
                    if url:
                        st.link_button("🔗 View & Apply", url, use_container_width=True)
                with c_a2:
                    if st.button("⭐ Bookmark", key=f"bookmark_rec_{idx}", use_container_width=True):
                        ok, msg = save_job(user_id=username, title_or_dict=job, score=score)
                        if ok:
                            st.success("⭐ Saved to bookmarks!")
                            st.rerun()
                        else:
                            st.info(msg)
                with c_a3:
                    if st.button("🚀 Track Application", key=f"track_rec_{idx}", use_container_width=True):
                        ok = add_application(
                            title=job.get("title", "Unknown"),
                            company=job.get("company", "Unknown"),
                            location=job.get("location", "India"),
                            score=score,
                            application_url=url,
                            status="Saved",
                            user_id=username
                        )
                        if ok:
                            st.success("Added to Application Tracker!")
                            st.rerun()
                        else:
                            st.info("Already tracked.")
                with c_a4:
                    if st.button("🎙️ Practice", key=f"interview_rec_{idx}", use_container_width=True):
                        st.session_state.interview_selected_job = {
                            "title": job.get("title", "Unknown"),
                            "company": job.get("company", "Unknown"),
                            "description": job.get("description", ""),
                            "skills": job.get("skills", []),
                            "matching_skills": matching,
                        }
                        st.session_state.current_page = "mock_interview"
                        st.rerun()
        except Exception as err:
            st.error(f"Error computing recommendations: {err}")

