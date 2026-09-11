# 🚀 AI Off-Campus Job Application Platform — Enterprise Edition

A production-grade, multi-user career copilot and application command center designed for job seekers, graduates, and professionals. Features a dual-backend database abstraction layer (PostgreSQL/Supabase + Zero-Config SQLite), an automated legacy data migration engine, a decoupled services layer, AI-driven job recommendations, an 18-attribute candidate profile, a 10-stage CRM pipeline, and strict human-in-the-loop application submission.

---

## 🌟 Key Highlights & Features

### 1. 🛡️ Dual-Mode Database Abstraction & Multi-User Isolation
- **Dual Database Architecture**: Connects seamlessly to **PostgreSQL / Supabase** via `DATABASE_URL` (or Streamlit secrets) in production, while defaulting to a thread-safe, zero-config local **SQLite database** (`database/job_assistant.db`) during development.
- **Zero-Data-Loss Migration**: Automatically detects and migrates legacy JSON data (`users.json`, `applications.json`, `resumes.json`, `saved_jobs.json`) into relational tables on initial startup.
- **Enterprise Password Security**: Salted PBKDF2 HMAC SHA-256 password hashing with 200,000 iterations, password strength validation, and duplicate email/username prevention.
- **Strict Data Isolation**: Every resume, bookmark, CRM application record, and analytics metric is strictly scoped to the authenticated `user_id`.

### 2. 👤 Comprehensive 18-Field Candidate Profile (`👤 Profile`)
- Supports detailed career specifications: Professional Title, Target Roles, Preferred Locations, Work Mode (Remote / Hybrid / On-site / Any), Years of Experience, Technical Skills, Soft Skills, Education, Certifications, Preferred Industries, Expected Salary, Notice Period, Work Authorization, LinkedIn, GitHub, and Portfolio URLs.
- Automatically powers personalized job matching and AI recommendations.

### 3. 📄 Multi-Resume Library & 7-Component Health Audit (`📁 My Resumes` & `📄 Resume Analyzer`)
- **Version Management**: Store distinct resume variations tailored to different career tracks.
- **Default Resume Setting**: Nominate a primary resume that auto-populates ATS checks, job matching, and tailoring.
- **Resume Comparison View**: Side-by-side visual diff and skill matrix comparison across any two uploaded resumes.
- **7-Component Health Audit**: Evaluates overall score (0–100) across Length/Brevity, Contact Details, Section Structure, Action Verbs, Measurable Metrics/Impact, Formatting Density, and Portfolio/LinkedIn Links.

### 4. 🧠 Decoupled Services Layer & AI Recommendations (`services/`)
- **`services/job_normalizer.py`**: Standardizes postings from heterogeneous sources into a uniform schema.
- **`services/job_deduplicator.py`**: Removes duplicate postings using canonical composite keys.
- **`services/job_sources.py`**: Manages live Adzuna queries and curated local catalog jobs with timeout and error handling.
- **`services/job_search.py`**: Orchestrates multi-source search, filtering (remote/location), and deduplication.
- **`services/job_recommendation.py`**: Multi-factor scoring engine evaluating skill overlap, target roles, geographic preferences, work mode, and experience to generate transparent *Why You Match* and *What Is Missing* explanations.

### 6. 🎙️ Adaptive AI Mock Interview Bot (`🎙️ Mock Interview`)
- **Multi-Mode Interview Practice**: General, Technical, Behavioral, HR, Mixed, and Job-Specific modes.
- **Resume & Job-Grounded Questions**: Extracts verified projects, tools, and job criteria. Strictly refuses to invent candidate experience.
- **Adaptive Question Sequencing**: Raises question difficulty and probes system design trade-offs following strong answers; asks foundational recovery questions following weak answers.
- **Transparent Multi-Factor Scoring**: Evaluates answers across Technical Depth, Relevance, Completeness, Clarity, and Problem Solving with constructive strengths (`✓`) and actionable areas to improve (`⚠`).
- **Interactive Improvement Mode**: Automatically synthesizes focused mini-interviews zeroing in directly on observed weak spots (e.g. System Design, SQL query tuning, STAR behavioral framing).
- **Session Persistence & Timer**: Pause/resume sessions at will, optional live countdown timer (15m/30m/45m/60m), and Web Speech voice dictation bridge.
- **Cross-Platform Deep Integration**: Direct 1-click interview practice from **Job Search**, **Job Matching**, **Application Tracker**, and the **Executive Dashboard**.

### 7. 📌 10-Stage CRM Application Lifecycle Tracker (`📌 Application Tracker`)
- **Industry-Standard Stages**:
  $$\text{Wishlist} \longrightarrow \text{Saved} \longrightarrow \text{Applied} \longrightarrow \text{Assessment} \longrightarrow \text{Interview} \longrightarrow \text{Technical Round} \longrightarrow \text{HR Round} \longrightarrow \text{Offer} \longrightarrow \text{Rejected} \longrightarrow \text{Withdrawn}$$
- **Chronological Status History**: Logs every stage transition with timestamps and notes.
- **Triage Follow-Ups**: Proactively categorizes pending recruiter communications into `Overdue`, `Due Today`, and `Upcoming`.
- **CSV Data Export**: Instant download of the active pipeline.

### 8. 🤖 Semi-Automatic Application Assistant & Smart Checklist (`🤖 Application Assistant`)
- **7-Item Readiness Checklist**: Verifies candidate resume, ATS compatibility, tailored summary, cover letter, outreach email, job requirements, and application link.
- **Strictly User-Controlled (Human-in-the-Loop)**: Never submits applications automatically or spams employers. Final submission is always user-controlled on the official employer portal.

### 9. ✍️ AI Application Content Studio (`✨ Tailoring`, `✍️ Cover Letter`, `📧 Email`)
- **Truth Preservation**: Grounds all bullets and summaries strictly in the candidate's actual background without fabricating credentials or experience.
- **Customizable Outreach**: Tone and length selectors with styled ReportLab PDF and text exports.

### 10. 📊 Factual User Analytics (`📊 Analytics`)
- True conversion funnels (Response Rate, Interview Rate, Offer Rate) calculated strictly from user data.
- Enforces an honest statistical guardrail ("Not enough data yet") when fewer than 3 applications exist.

---

## 🏗️ Technical Architecture

```text
resume-analyzer/
├── database/                      # Database Abstraction & Persistence Layer
│   ├── __init__.py                # Clean unified exports
│   ├── models.py                  # Dataclass schemas (UserProfile, InterviewSession, etc.)
│   ├── connection.py              # Dual PostgreSQL/Supabase + SQLite adapter
│   ├── migrations.py              # DDL schema creation (13 tables) & legacy JSON migration
│   ├── repository.py              # Parameterized, user-isolated CRUD repository
│   ├── interview_repo.py          # Isolated interview session/Q&A/evaluation/report repo
│   ├── users.py                   # User & auth backward-compatibility wrapper
│   ├── resumes.py                 # Multi-resume library wrapper
│   ├── jobs.py                    # Saved jobs bookmark wrapper
│   ├── applications.py            # 10-stage CRM pipeline wrapper
│   └── analytics.py               # Factual analytics wrapper
├── services/                      # Decoupled Business Logic & AI Services
│   ├── __init__.py                # Clean services interface
│   ├── job_normalizer.py          # Unified schema transformation & remote detection
│   ├── job_deduplicator.py        # Canonical token deduplication
│   ├── job_sources.py             # Adzuna API client & curated catalog reader
│   ├── job_search.py              # Search orchestration & filtering
│   ├── job_recommendation.py      # Multi-factor candidate-job fit & explanations
│   ├── interview_engine.py        # Central interview state machine & lifecycle
│   ├── interview_questions.py     # Resume-grounded & job-specific adaptive generator
│   ├── interview_evaluator.py     # Multi-dimensional answer evaluation & scoring
│   ├── interview_recommendations.py# Weakness extraction & Improvement Mode planner
│   └── voice_provider.py          # Web Speech API dictation & audio abstraction
├── ui/                            # Modular Streamlit SaaS Components
│   ├── sidebar.py                 # Categorized navigation with high-contrast styling
│   ├── styles.py                  # Light SaaS theme CSS
│   ├── dashboard_ui.py            # Executive dashboard with Interview Preparation widget
│   ├── interview_ui.py            # Complete mock interview room, report, & analytics
│   ├── resume_ui.py               # Resume analyzer & 7-component audit
│   ├── ats_ui.py                  # ATS score & keyword optimization
│   ├── my_resumes_ui.py           # Multi-resume manager & version comparison
│   ├── jobs_ui.py                 # Job search with 1-click interview practice
│   ├── saved_jobs_ui.py           # Bookmark catalog & pipeline promotion
│   ├── matching_ui.py             # 3-pillar candidate-job match & interview prep
│   ├── tailoring_ui.py            # Targeted resume bullet tailoring
│   ├── cover_letter_ui.py         # Document-preview cover letter generator
│   ├── email_ui.py                # Recruiter email drafter with PDF export
│   ├── tracker_ui.py              # 10-stage CRM pipeline with interview preparation action
│   ├── followup_ui.py             # Overdue/Today/Upcoming follow-up triage
│   ├── assistant_ui.py            # Guided assistant with Smart Application Checklist
│   ├── analytics_ui.py            # Real conversion funnel charts
│   ├── profile_ui.py              # 18-attribute candidate profile management
│   └── settings_ui.py             # System diagnostics & full portfolio JSON export
├── app.py                         # Application entrypoint & clean page router
├── core_logic.py                  # NLP parsing, semantic vectors & document engines
├── application_tracker.py         # Scoped backward-compatible tracker interface
├── requirements.txt               # Deployable production dependencies
├── .env.example                   # Configuration template
├── .gitignore                     # Git exclusion rules
└── README.md                      # Documentation
```

---

## ⚡ Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (tested and verified on Python 3.13)
- `pip` package manager

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment (Optional)
Copy `.env.example` to `.env` or configure Streamlit secrets (`.streamlit/secrets.toml`):
```bash
# Optional: Provide PostgreSQL/Supabase URL (defaults to zero-config SQLite if blank)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Optional: Adzuna API keys for live job querying
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

### 4. Launch the Platform
```bash
streamlit run app.py
```
Navigate to `http://localhost:8501` to use the application.

### 5. Run the Comprehensive Verification Test Suite
```bash
py -3.13 "C:\Users\venky\.gemini\antigravity\brain\4622d331-f2b9-4983-82bb-efaedd85805f\scratch\verify_production_master.py"
```

---

## 🔒 Security & Data Privacy
- **Salted Hashing**: PBKDF2 HMAC SHA-256 with 200,000 iterations; no passwords stored in plaintext.
- **SQL Injection Prevention**: All queries across PostgreSQL and SQLite are strictly parameterized.
- **Strict User Isolation**: All read and write operations are scoped by authenticated `user_id`.
- **No Hallucinations / No Fabrications**: All ATS keywords, bullet points, and email drafts strictly ground themselves in the candidate's actual supplied background.
