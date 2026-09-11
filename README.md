# 🚀 AI Off-Campus Job Application Assistant

A modern, production-grade SaaS career copilot designed for job seekers, graduates, and professionals. Features end-to-end resume intelligence, ATS optimization, intelligent job matching, automated outreach generation, a 9-stage application lifecycle tracker with proactive follow-up alerts, multi-resume management, and multi-user data isolation.

---

## 🌟 Key Highlights & Features

### 1. 🛡️ Multi-User Authentication & Data Isolation
- **Secure Security**: PBKDF2 HMAC SHA-256 password hashing with 200,000 iterations and cryptographic salts.
- **Strict Data Isolation**: Every resume, bookmarked job, application record, and analytics calculation is strictly isolated by `user_id`.
- **User Profiles & Preferences**: Manage user contact info, target job roles, preferred locations, and notification settings.

### 2. 📄 Multi-Resume Management & Versioning (`📁 My Resumes`)
- **Multi-Resume Library**: Maintain separate resume versions (e.g., *Frontend Engineering*, *Data Science*, *General Tech*).
- **Default Resume Toggle**: Set a primary default resume that automatically pre-populates the ATS analyzer, job matcher, and tailoring engines.
- **Resume Comparison View**: Side-by-side visual diff and skill matrix comparison across any two uploaded resumes.
- **Comprehensive 7-Component Health Audit**: Evaluates overall score (0–100) across Length/Brevity, Contact Details, Section Structure, Action Verbs, Measurable Metrics/Impact, Formatting Density, and Portfolio/LinkedIn Links.

### 3. 🎯 ATS Optimization & Keyword Analysis (`🎯 ATS Analyzer`)
- **Multi-Resume Selector**: Run ATS checks against any resume from your library or newly pasted content.
- **Keyword Match Matrix**: Compares hard skills, frameworks, and job requirements.
- **Ethical Anti-Fabrication Safeguards**: Emphasizes highlighting existing verifiable experience rather than fabricating skills.

### 4. 🔎 Dual-Track Job Discovery (`🔎 Job Search` & `⭐ Saved Jobs`)
- **Live Search & Local Catalog**: Query live external jobs (Adzuna integration with resilient error-handling) or browse local curated listings.
- **Dual-Action Tracking**:
  - **Bookmark (`⭐ Save Job`)**: Save intriguing opportunities to your personal bookmark catalog without cluttering your application pipeline.
  - **Pipeline Track (`📌 Track Application`)**: Instantly inject a job directly into your 9-stage tracker.
- **Saved Jobs Management**: Filter bookmarks by title or company, view details, apply via direct external link, or promote directly into your tracker.

### 5. 🧠 Intelligent 3-Pillar Job Matching (`🧠 Job Matching`)
- **Transparent Scoring**: Evaluates candidate fit across semantic similarity and skill overlap.
- **3-Pillar Analysis**:
  1. *Why You Match*: Pinpoints shared skills and relevant background.
  2. *Why You May Not Match*: Highlights gaps and missing job requirements.
  3. *What to Improve*: Actionable recommendations to boost candidacy.
- **1-Click Workflow Bridges**: Jump straight from matching into Resume Tailoring, Cover Letter, or Email generation.

### 6. ✍️ AI Application Content Generator (`✨ Tailoring`, `✍️ Cover Letter`, `📧 Email`)
- **Resume Tailoring**: Generates targeted professional summaries and keyword-aligned bullet points.
- **Cover Letter Studio**: Customizable tone (Professional, Confident, Conversational) and length (Short, Medium, Comprehensive) with 1-click styled PDF export.
- **Application Email Drafter**: Creates recruiter outreach emails, connection notes, and follow-up templates with PDF export.

### 7. 📌 9-Stage Application Lifecycle Tracker (`📌 Application Tracker`)
- **Industry-Standard Stages**:
  `Saved` ➔ `Applied` ➔ `Screening` ➔ `Interview` ➔ `Technical Round` ➔ `HR Round` ➔ `Offer` ➔ `Rejected` ➔ `Withdrawn`
- **Stage Tab Filters**: Inspect applications by status category or see all at once.
- **Inline Stage Transitioning**: Advance application stages with a single click.
- **Deadline Monitoring**: Automatically tracks response and interview dates.
- **CSV Data Export**: Export active pipeline records to CSV anytime.

### 8. ⏰ Proactive Follow-Up Center (`⏰ Follow-Up Center`)
- **Deadline Categorization**: Dynamically separates pending follow-ups into `Overdue`, `Today`, and `Upcoming`.
- **1-Click Follow-up Drafter**: Auto-generates polite, professional follow-up messages tailored to the specific company and role.

### 9. 🤖 Semi-Automatic Application Assistant (`🤖 Application Assistant`)
- **Ethical Human-in-the-Loop Design**: Streamlines form autofill and preparation while keeping final application submission strictly under USER control.
- Prevents blind spamming and safeguards application credibility.

### 10. 📊 Factual User Analytics & Diagnostics (`📊 Analytics` & `⚙️ Settings`)
- **Factual Conversion Funnel**: Real metrics calculated strictly from user's isolated data (Response Rate, Interview Rate, Offer Rate).
- **Diagnostics & Backup**: Live storage diagnostics for all 5 JSON databases, user preferences, and a 1-click complete portfolio JSON export.

---

## 🏗️ Technical Architecture

The application is structured with a decoupled, thread-safe database abstraction layer and clean modular UI views:

```text
resume-analyzer/
├── database/                      # Thread-Safe Database Abstraction Layer
│   ├── __init__.py                # Clean unified exports
│   ├── models.py                  # Dataclass schemas (UserProfile, ResumeRecord, etc.)
│   ├── connection.py              # Thread-safe atomic file I/O adapter
│   ├── users.py                   # PBKDF2 authentication & profiles
│   ├── resumes.py                 # Multi-resume versioning & library
│   ├── jobs.py                    # User-scoped saved jobs bookmarking
│   ├── applications.py            # 9-stage pipeline & follow-up engine
│   └── analytics.py               # Factual user-scoped conversion metrics
├── ui/                            # Modular Streamlit UI Components
│   ├── sidebar.py                 # Categorized navigation with high-contrast text
│   ├── styles.py                  # Light SaaS theme & responsive card styling
│   ├── dashboard_ui.py            # 5 KPI metrics, follow-up alerts, & shortcuts
│   ├── resume_ui.py               # Resume upload, parsing & 7-component audit
│   ├── ats_ui.py                  # ATS score & keyword optimization
│   ├── my_resumes_ui.py           # Multi-resume manager & side-by-side comparison
│   ├── jobs_ui.py                 # Live search, local catalog & dual-save
│   ├── saved_jobs_ui.py           # Bookmark catalog & promotion to pipeline
│   ├── matching_ui.py             # 3-pillar candidate-job match breakdown
│   ├── tailoring_ui.py            # Experience-based resume bullet tailoring
│   ├── cover_letter_ui.py         # Tailored cover letters with PDF export
│   ├── email_ui.py                # Cold outreach & application emails with PDF export
│   ├── tracker_ui.py              # 9-stage Kanban pipeline & CSV export
│   ├── followup_ui.py             # Overdue/Today/Upcoming follow-up triage
│   ├── assistant_ui.py            # Human-in-the-loop application assistant
│   ├── analytics_ui.py            # Real conversion funnel & stage distributions
│   ├── profile_ui.py              # User profile & target role configuration
│   └── settings_ui.py             # System diagnostics & full portfolio export
├── app.py                         # Application entrypoint & clean page router
├── core_logic.py                  # Core NLP, semantic matching, & generators
├── application_tracker.py         # Backward-compatible user-scoped tracker
├── job_matcher.py                 # Skill extraction & match scoring
├── resume_parser.py               # PDF/text extraction & NLP parser
├── requirements.txt               # Project dependencies
└── README.md                      # Documentation
```

---

## ⚡ Quickstart Guide

### Prerequisites
- Python 3.10+ (tested and verified on Python 3.13)
- `pip` package manager

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
streamlit run app.py
```
The application will open in your browser at `http://localhost:8501`.

---

## 🔒 Security & Data Privacy
- **Local & Private**: All data is stored locally in thread-safe JSON datastores in the user's workspace.
- **Salted Hashing**: No passwords are ever stored in plaintext.
- **No Hallucinations / No Fabrications**: All ATS keywords, bullet points, and email drafts strictly ground themselves in the candidate's actual supplied background.
