import streamlit as st

def apply_custom_styles():
    """
    Inject professional, light-mode AI SaaS dashboard styling.
    Maintains clean visual hierarchy, soft cards, readable typography,
    and polished chips/badges.
    """
    st.markdown("""
    <style>
    /* Global App Background & Base Typography */
    .stApp {
        background-color: #f8fafc !important;
        color: #1e293b !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }

    /* Force Light Streamlit containers & Comfortable Sidebar Width */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
        min-width: 295px !important;
        width: 305px !important;
        max-width: 335px !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        min-width: 295px !important;
        width: 305px !important;
        max-width: 335px !important;
        background-color: #ffffff !important;
    }

    [data-testid="stSidebarUserContent"] {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    [data-testid="stSidebar"] hr {
        border-color: #f1f5f9 !important;
    }

    /* Force dark readable typography across the entire sidebar */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] .stMarkdown {
        color: #1e293b !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* ========================================================
       SIDEBAR NAVIGATION BUTTON STYLES (SaaS MENU ITEMS)
       ======================================================== */
    [data-testid="stSidebar"] div.stButton {
        margin-bottom: 0.25rem !important;
    }

    [data-testid="stSidebar"] div.stButton > button {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        text-align: left !important;
        width: 100% !important;
        min-height: 44px !important;
        padding: 0.65rem 0.95rem !important;
        border-radius: 8px !important;
        font-size: 0.94rem !important;
        line-height: 1.4 !important;
        gap: 0.75rem !important;
        cursor: pointer !important;
        transition: all 0.15s ease-in-out !important;
    }

    /* Inactive / Normal Navigation Item */
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"],
    [data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-secondary"] {
        background-color: transparent !important;
        border: 1px solid transparent !important;
        border-left: 4px solid transparent !important;
        color: #1e293b !important;
        font-weight: 500 !important;
        box-shadow: none !important;
    }

    [data-testid="stSidebar"] div.stButton > button[kind="secondary"] p,
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"] span,
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"] div {
        color: #1e293b !important;
        font-weight: 500 !important;
        font-size: 0.94rem !important;
        text-align: left !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* Inactive Item Hover State */
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover,
    [data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-secondary"]:hover {
        background-color: #f1f5f9 !important;
        border-color: #e2e8f0 !important;
        border-left: 4px solid #cbd5e1 !important;
        color: #0f172a !important;
    }

    [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover p,
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover span {
        color: #0f172a !important;
        font-weight: 600 !important;
    }

    /* Active Navigation Item */
    [data-testid="stSidebar"] div.stButton > button[kind="primary"],
    [data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-primary"] {
        background-color: #eef2ff !important;
        border: 1px solid #c7d2fe !important;
        border-left: 4px solid #4f46e5 !important;
        color: #3730a3 !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(79, 70, 229, 0.08) !important;
    }

    [data-testid="stSidebar"] div.stButton > button[kind="primary"] p,
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] span,
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] div {
        color: #3730a3 !important;
        font-weight: 600 !important;
        font-size: 0.94rem !important;
        text-align: left !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    [data-testid="stSidebar"] div.stButton > button[kind="primary"]:hover {
        background-color: #e0e7ff !important;
        border-color: #a5b4fc !important;
        border-left: 4px solid #4338ca !important;
    }

    [data-testid="stSidebar"] div.stButton > button[kind="primary"]:hover p,
    [data-testid="stSidebar"] div.stButton > button[kind="primary"]:hover span {
        color: #312e81 !important;
    }

    /* Sidebar Logout Button */
    .sidebar-logout-wrapper {
        margin-top: 0.75rem !important;
    }

    .sidebar-logout-wrapper div.stButton > button {
        justify-content: center !important;
        text-align: center !important;
        background-color: #fef2f2 !important;
        border: 1px solid #fee2e2 !important;
        border-left: 1px solid #fee2e2 !important;
        color: #dc2626 !important;
        font-weight: 600 !important;
    }

    .sidebar-logout-wrapper div.stButton > button p,
    .sidebar-logout-wrapper div.stButton > button span {
        color: #dc2626 !important;
        font-weight: 600 !important;
        text-align: center !important;
    }

    .sidebar-logout-wrapper div.stButton > button:hover {
        background-color: #fee2e2 !important;
        border-color: #fca5a5 !important;
        border-left-color: #fca5a5 !important;
        color: #b91c1c !important;
    }

    .sidebar-logout-wrapper div.stButton > button:hover p {
        color: #b91c1c !important;
    }

    /* ========================================================
       SIDEBAR RADIO FALLBACK (IF ST.RADIO IS EVER USED)
       ======================================================== */
    /* Remove radio circle dots */
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        padding: 0.65rem 0.95rem !important;
        margin-bottom: 0.25rem !important;
        border-radius: 8px !important;
        border: 1px solid transparent !important;
        border-left: 4px solid transparent !important;
        cursor: pointer !important;
        background-color: transparent !important;
        transition: all 0.15s ease-in-out !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label p,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label span,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label div {
        color: #1e293b !important;
        font-size: 0.94rem !important;
        font-weight: 500 !important;
        line-height: 1.4 !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background-color: #f1f5f9 !important;
        border-color: #e2e8f0 !important;
        border-left: 4px solid #cbd5e1 !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover p {
        color: #0f172a !important;
        font-weight: 600 !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked),
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #eef2ff !important;
        border: 1px solid #c7d2fe !important;
        border-left: 4px solid #4f46e5 !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] p {
        color: #3730a3 !important;
        font-weight: 600 !important;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        max-width: 1280px !important;
    }

    /* Top Navigation / App Header */
    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 1.5rem;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        margin-bottom: 1.75rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }
    .app-header-left {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .app-logo {
        font-size: 1.75rem;
    }
    .app-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        line-height: 1.2;
    }
    .app-subtitle {
        font-size: 0.85rem;
        color: #64748b;
        margin: 0;
    }
    .app-header-right {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    /* Dashboard Welcome Banner */
    .welcome-banner {
        background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
        border-radius: 14px;
        padding: 1.75rem 2rem;
        color: #ffffff;
        margin-bottom: 1.75rem;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.18);
    }
    .welcome-title {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0 0 0.35rem 0;
        color: #ffffff !important;
    }
    .welcome-desc {
        font-size: 0.95rem;
        color: #e0e7ff !important;
        margin: 0;
    }

    /* Metric / KPI Card */
    .stat-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    }
    .stat-label {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #64748b;
        margin-bottom: 0.35rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .stat-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.1;
        margin: 0.25rem 0;
    }
    .stat-subtext {
        font-size: 0.8rem;
        color: #10b981;
        font-weight: 500;
    }
    .stat-subtext-neutral {
        font-size: 0.8rem;
        color: #64748b;
    }

    /* SaaS Content Cards */
    .saas-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }
    .saas-card-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* Tag & Skill Chips */
    .chip-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin-top: 0.4rem;
        margin-bottom: 0.4rem;
    }
    .skill-chip {
        display: inline-flex;
        align-items: center;
        background: #eef2ff;
        color: #4338ca;
        border: 1px solid #c7d2fe;
        font-size: 0.82rem;
        font-weight: 500;
        padding: 0.22rem 0.65rem;
        border-radius: 9999px;
        line-height: 1.3;
    }
    .skill-chip-match {
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }
    .skill-chip-missing {
        background: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    .skill-chip-category {
        background: #f8fafc;
        color: #475569;
        border: 1px solid #e2e8f0;
    }

    /* Application Status Badges */
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
        text-align: center;
    }
    .badge-saved { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
    .badge-applied { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .badge-assessment { background: #ffedd5; color: #9a3412; border: 1px solid #fed7aa; }
    .badge-interview { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
    .badge-offer { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
    .badge-selected { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
    .badge-rejected { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    .badge-withdrawn { background: #f3f4f6; color: #6b7280; border: 1px solid #e5e7eb; }

    /* Priority Badges */
    .priority-high { color: #dc2626; font-weight: 600; }
    .priority-medium { color: #d97706; font-weight: 600; }
    .priority-low { color: #16a34a; font-weight: 600; }

    /* Workflow Stepper */
    .stepper-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.85rem 1.25rem;
        margin-bottom: 1.5rem;
    }
    .stepper-step {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.88rem;
        font-weight: 600;
        color: #64748b;
    }
    .stepper-step.active {
        color: #4f46e5;
    }
    .stepper-step.completed {
        color: #10b981;
    }
    .stepper-num {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        background: #f1f5f9;
        color: #64748b;
    }
    .stepper-step.active .stepper-num {
        background: #4f46e5;
        color: #ffffff;
    }
    .stepper-step.completed .stepper-num {
        background: #10b981;
        color: #ffffff;
    }

    /* Document Preview Sheet (Cover Letter, Resumes) */
    .document-sheet {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 2.25rem 2.5rem;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
        font-family: "Georgia", serif, -apple-system;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #1e293b;
        white-space: pre-wrap;
        margin: 1rem 0;
    }

    /* Email Preview Container */
    .email-container {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.05);
        margin: 1rem 0;
    }
    .email-header {
        background: #f8fafc;
        border-bottom: 1px solid #e2e8f0;
        padding: 0.85rem 1.25rem;
        font-size: 0.88rem;
    }
    .email-header-row {
        margin: 0.2rem 0;
        color: #475569;
    }
    .email-header-row strong {
        color: #1e293b;
    }
    .email-body {
        padding: 1.5rem;
        font-size: 0.95rem;
        line-height: 1.65;
        color: #1e293b;
        white-space: pre-wrap;
    }

    /* Modern Job Card */
    .job-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
        transition: all 0.15s ease-in-out;
    }
    .job-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
    }
    .job-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0 0 0.25rem 0;
    }
    .job-company {
        font-size: 0.92rem;
        font-weight: 600;
        color: #475569;
        margin-bottom: 0.5rem;
    }
    .job-meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 0.75rem;
    }

    /* Score Gauge Widget */
    .score-circle {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        border-radius: 50%;
        width: 100px;
        height: 100px;
        margin: 0 auto;
    }
    .score-circle-num {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1;
        color: #4f46e5;
    }
    .score-circle-label {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 600;
    }

    /* Custom Streamlit Element Tweaks */
    div[data-testid="stMetricValue"] {
        font-weight: 700 !important;
        color: #0f172a !important;
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 600 !important;
        color: #64748b !important;
    }

    /* Primary Buttons */
    button[kind="primary"] {
        background-color: #4f46e5 !important;
        border-color: #4f46e5 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    button[kind="primary"]:hover {
        background-color: #4338ca !important;
        border-color: #4338ca !important;
    }

    /* Secondary Buttons */
    button[kind="secondary"] {
        border-radius: 8px !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #ffffff !important;
        color: #334155 !important;
        font-weight: 500 !important;
    }
    button[kind="secondary"]:hover {
        background-color: #f8fafc !important;
        border-color: #94a3b8 !important;
    }

    /* Upload Area Card */
    .upload-card-wrapper {
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 2rem 1.5rem;
        text-align: center;
        background: #ffffff;
        margin-bottom: 1.25rem;
    }

    /* Clean Empty State */
    .empty-state {
        text-align: center;
        padding: 3rem 1.5rem;
        background: #ffffff;
        border: 1px dashed #cbd5e1;
        border-radius: 12px;
        margin: 1rem 0;
    }
    .empty-state-icon {
        font-size: 2.75rem;
        margin-bottom: 0.5rem;
    }
    .empty-state-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.35rem;
    }
    .empty-state-desc {
        font-size: 0.9rem;
        color: #64748b;
        max-width: 440px;
        margin: 0 auto 1.25rem auto;
    }
    </style>
    """, unsafe_allow_html=True)
