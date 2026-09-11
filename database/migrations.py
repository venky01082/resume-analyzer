"""
Database Migrations & Schema Initializer
Creates relational tables, indexes, and automatically migrates legacy JSON stores.
"""

import os
import json
from typing import Dict, Any, List
from database.connection import get_db_connection, execute_query, read_json_file
from database.models import UserProfile, UserPreferences


def init_db():
    """Create all required tables and indexes if they do not already exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
        """)

        # 2. User Profiles Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            username TEXT PRIMARY KEY,
            full_name TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            location TEXT DEFAULT '',
            professional_title TEXT DEFAULT '',
            target_roles TEXT DEFAULT '',
            preferred_locations TEXT DEFAULT '',
            work_mode_preference TEXT DEFAULT 'Any',
            years_of_experience REAL DEFAULT 0.0,
            skills TEXT DEFAULT '',
            technical_skills TEXT DEFAULT '',
            soft_skills TEXT DEFAULT '',
            education TEXT DEFAULT '',
            certifications TEXT DEFAULT '',
            preferred_industries TEXT DEFAULT '',
            expected_salary TEXT DEFAULT '',
            notice_period TEXT DEFAULT '',
            work_authorization TEXT DEFAULT '',
            linkedin TEXT DEFAULT '',
            github TEXT DEFAULT '',
            portfolio TEXT DEFAULT '',
            FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
        )
        """)

        # 3. User Preferences Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            username TEXT PRIMARY KEY,
            preferred_roles TEXT DEFAULT '',
            preferred_locations TEXT DEFAULT 'India',
            work_preference TEXT DEFAULT 'Any',
            default_cover_letter_tone TEXT DEFAULT 'Professional',
            default_email_length TEXT DEFAULT 'Medium',
            default_resume_id TEXT DEFAULT '',
            FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
        )
        """)

        # 4. Resumes Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            resume_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            filename TEXT DEFAULT '',
            text TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            is_default INTEGER DEFAULT 0,
            parsed_data TEXT DEFAULT '{}'
        )
        """)

        # 5. Saved Jobs Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_jobs (
            job_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT DEFAULT '',
            url TEXT DEFAULT '',
            score INTEGER DEFAULT 0,
            salary TEXT DEFAULT '',
            saved_at TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'Saved',
            notes TEXT DEFAULT '',
            priority TEXT DEFAULT 'Medium',
            tags TEXT DEFAULT ''
        )
        """)

        # 6. Applications Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            app_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT DEFAULT '',
            score INTEGER DEFAULT 0,
            application_url TEXT DEFAULT '',
            status TEXT DEFAULT 'Applied',
            priority TEXT DEFAULT 'Medium',
            applied_date TEXT DEFAULT '',
            follow_up_date TEXT DEFAULT '',
            last_updated TEXT NOT NULL,
            notes TEXT DEFAULT '',
            contact_name TEXT DEFAULT '',
            contact_email TEXT DEFAULT '',
            salary TEXT DEFAULT '',
            source TEXT DEFAULT '',
            job_description TEXT DEFAULT '',
            resume_used TEXT DEFAULT '',
            cover_letter_used TEXT DEFAULT '',
            next_action TEXT DEFAULT ''
        )
        """)

        # 7. Application Status History Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS application_status_history (
            history_id TEXT PRIMARY KEY,
            app_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            status TEXT NOT NULL,
            changed_at TEXT NOT NULL,
            notes TEXT DEFAULT '',
            FOREIGN KEY(app_id) REFERENCES applications(app_id) ON DELETE CASCADE
        )
        """)

        # 8. Generated Documents Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS generated_documents (
            doc_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            doc_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            metadata TEXT DEFAULT '{}'
        )
        """)

        # Create Indexes for Query Performance & Isolation
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resumes_user ON resumes(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_jobs_user ON saved_jobs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(user_id, status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_app ON application_status_history(app_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_user ON generated_documents(user_id)")

    # Run automatic zero-loss migration from legacy JSON stores
    migrate_legacy_data()


def migrate_legacy_data():
    """Safely migrate existing JSON file data into database tables if not already present."""
    # 1. Migrate Users
    users_json = read_json_file("users.json", default={})
    if isinstance(users_json, dict):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for username, data in users_json.items():
                u_clean = username.strip().lower()
                cursor.execute("SELECT username FROM users WHERE username = ?", (u_clean,))
                if not cursor.fetchone():
                    p_salt = data.get("password_salt", "")
                    p_hash = data.get("password_hash", "")
                    c_at = data.get("created_at", "legacy")
                    email = data.get("profile", {}).get("email", "")

                    cursor.execute(
                        "INSERT INTO users (username, password_salt, password_hash, email, created_at) VALUES (?, ?, ?, ?, ?)",
                        (u_clean, p_salt, p_hash, email, c_at)
                    )

                    prof = data.get("profile", {})
                    cursor.execute("""
                        INSERT INTO profiles (
                            username, full_name, email, phone, location, professional_title,
                            target_roles, preferred_locations, work_mode_preference, years_of_experience,
                            skills, technical_skills, soft_skills, education, certifications,
                            preferred_industries, expected_salary, notice_period, work_authorization,
                            linkedin, github, portfolio
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        u_clean,
                        prof.get("full_name", ""),
                        prof.get("email", ""),
                        prof.get("phone", ""),
                        prof.get("location", ""),
                        prof.get("professional_title", ""),
                        prof.get("target_roles", ""),
                        prof.get("preferred_locations", ""),
                        prof.get("work_mode_preference", "Any"),
                        float(prof.get("years_of_experience", 0.0) or 0.0),
                        prof.get("skills", ""),
                        prof.get("technical_skills", prof.get("skills", "")),
                        prof.get("soft_skills", ""),
                        prof.get("education", ""),
                        prof.get("certifications", ""),
                        prof.get("preferred_industries", ""),
                        prof.get("expected_salary", ""),
                        prof.get("notice_period", ""),
                        prof.get("work_authorization", ""),
                        prof.get("linkedin", ""),
                        prof.get("github", ""),
                        prof.get("portfolio", "")
                    ))

                    prefs = data.get("preferences", {})
                    cursor.execute("""
                        INSERT INTO preferences (
                            username, preferred_roles, preferred_locations, work_preference,
                            default_cover_letter_tone, default_email_length, default_resume_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        u_clean,
                        prefs.get("preferred_roles", ""),
                        prefs.get("preferred_locations", "India"),
                        prefs.get("work_preference", "Any"),
                        prefs.get("default_cover_letter_tone", "Professional"),
                        prefs.get("default_email_length", "Medium"),
                        prefs.get("default_resume_id", "")
                    ))

    # 2. Migrate Resumes
    resumes_json = read_json_file("resumes.json", default={})
    if isinstance(resumes_json, dict):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for user_id, rlist in resumes_json.items():
                if isinstance(rlist, list):
                    for r in rlist:
                        rid = r.get("resume_id")
                        if rid:
                            cursor.execute("SELECT resume_id FROM resumes WHERE resume_id = ?", (rid,))
                            if not cursor.fetchone():
                                cursor.execute("""
                                    INSERT INTO resumes (resume_id, user_id, title, filename, text, uploaded_at, score, is_default, parsed_data)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    rid,
                                    user_id.strip().lower(),
                                    r.get("title", "My Resume"),
                                    r.get("filename", "resume.pdf"),
                                    r.get("text", r.get("content", "")),
                                    r.get("uploaded_at", ""),
                                    int(r.get("score", 0) or 0),
                                    1 if r.get("is_default") else 0,
                                    json.dumps(r.get("parsed_data", {}))
                                ))

    # 3. Migrate Saved Jobs
    saved_jobs_json = read_json_file("saved_jobs.json", default={})
    if isinstance(saved_jobs_json, dict):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for user_id, jlist in saved_jobs_json.items():
                if isinstance(jlist, list):
                    for j in jlist:
                        jid = j.get("job_id")
                        if jid:
                            cursor.execute("SELECT job_id FROM saved_jobs WHERE job_id = ?", (jid,))
                            if not cursor.fetchone():
                                cursor.execute("""
                                    INSERT INTO saved_jobs (job_id, user_id, title, company, location, url, score, salary, saved_at, description, status, notes, priority, tags)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    jid,
                                    user_id.strip().lower(),
                                    j.get("title", "Untitled Job"),
                                    j.get("company", "Unknown Company"),
                                    j.get("location", ""),
                                    j.get("url", ""),
                                    int(j.get("score", 0) or 0),
                                    j.get("salary", ""),
                                    j.get("saved_at", ""),
                                    j.get("description", ""),
                                    j.get("status", "Saved"),
                                    j.get("notes", ""),
                                    j.get("priority", "Medium"),
                                    j.get("tags", "")
                                ))

    # 4. Migrate Applications
    apps_json = read_json_file("applications.json", default=[])
    if isinstance(apps_json, list):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for a in apps_json:
                aid = a.get("app_id")
                uid = a.get("user_id", "venky").strip().lower()
                if aid:
                    cursor.execute("SELECT app_id FROM applications WHERE app_id = ?", (aid,))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO applications (
                                app_id, user_id, title, company, location, score, application_url,
                                status, priority, applied_date, follow_up_date, last_updated,
                                notes, contact_name, contact_email, salary, source, job_description,
                                resume_used, cover_letter_used, next_action
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            aid,
                            uid,
                            a.get("title", "Untitled Application"),
                            a.get("company", "Unknown Company"),
                            a.get("location", ""),
                            int(a.get("score", 0) or 0),
                            a.get("application_url", ""),
                            a.get("status", "Applied"),
                            a.get("priority", "Medium"),
                            a.get("applied_date", ""),
                            a.get("follow_up_date", ""),
                            a.get("last_updated", ""),
                            a.get("notes", ""),
                            a.get("contact_name", ""),
                            a.get("contact_email", ""),
                            a.get("salary", ""),
                            a.get("source", ""),
                            a.get("job_description", ""),
                            a.get("resume_used", ""),
                            a.get("cover_letter_used", ""),
                            a.get("next_action", "")
                        ))
