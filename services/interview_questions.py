"""
Interview Question Generation Service
Generates grounded, resume-aware, job-specific, and dynamically adaptive interview questions
across 11 professional categories and 5 interviewer styles.
"""

import os
import re
import json
import random
from typing import Dict, Any, List, Optional, Tuple

from core_logic import (
    analyze_ats_keywords,
    extract_section,
    extract_education_details,
    extract_job_skills,
    SKILLS_DATABASE,
)


# =========================================================
# DOMAIN-SPECIFIC QUESTION KNOWLEDGE BASE (DETERMINISTIC FALLBACK)
# =========================================================

TECHNICAL_QUESTION_BANK: Dict[str, List[Dict[str, Any]]] = {
    "python": [
        {
            "question": "How do Python's memory management and garbage collection (specifically reference counting and cyclic GC) work in CPython?",
            "category": "Technical Knowledge",
            "difficulty": "Hard",
            "concept": "memory management",
            "follow_up_hard": "How does the GIL interact with multi-threaded Python applications, and when would you choose multiprocessing or asyncio over threading?",
            "follow_up_easy": "Can you explain the difference between mutable and immutable types in Python, giving examples of each?"
        },
        {
            "question": "What are Python decorators and generators, and in what real-world production scenarios would you implement each?",
            "category": "Coding Concepts",
            "difficulty": "Medium",
            "concept": "generators & decorators",
            "follow_up_hard": "How would you implement a parameterized decorator that enforces rate limiting or caching with an LRU eviction policy?",
            "follow_up_easy": "What is the function of the 'yield' keyword compared to 'return' in a Python function?"
        },
        {
            "question": "Explain how list comprehensions, generator expressions, and dictionary comprehensions differ in terms of syntax and memory utilization.",
            "category": "Technical Knowledge",
            "difficulty": "Easy",
            "concept": "comprehensions & memory",
            "follow_up_hard": "If processing a 10GB log file in Python, how would you architect your data pipeline to prevent Out-Of-Memory errors?",
            "follow_up_easy": "How do you handle exceptions using try-except-finally blocks in Python?"
        }
    ],
    "sql": [
        {
            "question": "How would you identify and optimize a slow-running SQL query in production? What database tools and index strategies would you use?",
            "category": "Problem Solving",
            "difficulty": "Medium",
            "concept": "query optimization & indexing",
            "follow_up_hard": "Can you contrast B-Tree indexes with Hash or Composite indexes, and explain index selectivity?",
            "follow_up_easy": "What is the difference between WHERE and HAVING clauses in an aggregate SQL statement?"
        },
        {
            "question": "Explain database normalization up to Third Normal Form (3NF) and discuss when intentional denormalization is beneficial in high-throughput systems.",
            "category": "System Design",
            "difficulty": "Hard",
            "concept": "normalization & schema design",
            "follow_up_hard": "How do database isolation levels (Read Committed vs Serializable) prevent phenomena like dirty reads and phantom reads?",
            "follow_up_easy": "What is the difference between an INNER JOIN and a LEFT OUTER JOIN?"
        }
    ],
    "api": [
        {
            "question": "How would you design a scalable, secure RESTful API that handles authentication, versioning, and rate limiting?",
            "category": "System Design",
            "difficulty": "Medium",
            "concept": "rest api design",
            "follow_up_hard": "How would you handle idempotency for POST requests in a distributed payment processing API?",
            "follow_up_easy": "What are the common HTTP status codes (200, 201, 400, 401, 403, 404, 500) and what do they signify?"
        },
        {
            "question": "When designing service-to-service communication, under what conditions would you choose REST, GraphQL, or gRPC/WebSockets?",
            "category": "System Design",
            "difficulty": "Hard",
            "concept": "api protocols",
            "follow_up_hard": "How do you implement distributed tracing and health checks across microservices communicating via asynchronous event buses?",
            "follow_up_easy": "What is the purpose of API request headers like Authorization and Content-Type?"
        }
    ],
    "machine learning": [
        {
            "question": "How do you handle severe class imbalance in a classification dataset, and which evaluation metrics would you prioritize over accuracy?",
            "category": "Problem Solving",
            "difficulty": "Medium",
            "concept": "class imbalance & metrics",
            "follow_up_hard": "How would you diagnose and mitigate data drift and concept drift in a live production machine learning pipeline?",
            "follow_up_easy": "What is the difference between supervised and unsupervised machine learning?"
        },
        {
            "question": "Explain the bias-variance tradeoff and the concrete regularization techniques you apply to prevent model overfitting.",
            "category": "Technical Knowledge",
            "difficulty": "Medium",
            "concept": "bias-variance & regularization",
            "follow_up_hard": "How do L1 (Lasso) and L2 (Ridge) penalties affect model weights mathematically and in terms of feature selection?",
            "follow_up_easy": "Why do we split data into training, validation, and test sets?"
        }
    ],
    "docker": [
        {
            "question": "How do you optimize a Dockerfile to minimize image size and leverage layer caching efficiently in CI/CD pipelines?",
            "category": "Technical Knowledge",
            "difficulty": "Medium",
            "concept": "containerization",
            "follow_up_hard": "How do you handle container security, non-root user execution, and secret management in Kubernetes or ECS?",
            "follow_up_easy": "What is the difference between a Docker image and a Docker container?"
        }
    ],
    "system design": [
        {
            "question": "How would you design a URL shortening service (like Bitly) or a real-time notification service for 10 million daily active users?",
            "category": "System Design",
            "difficulty": "Hard",
            "concept": "high-scale system design",
            "follow_up_hard": "How would you handle cache invalidation, Redis cluster failover, and database read replicas under peak write load?",
            "follow_up_easy": "What is horizontal scaling versus vertical scaling?"
        }
    ]
}

BEHAVIORAL_QUESTION_BANK: List[Dict[str, Any]] = [
    {
        "question": "Tell me about a challenging technical bug or outage you encountered. How did you diagnose the root cause and resolve it under pressure?",
        "category": "Behavioral",
        "difficulty": "Medium",
        "concept": "debugging under pressure",
        "follow_up_hard": "What post-mortem processes, monitoring, or automated tests did you introduce to ensure that class of bug never recurs?",
        "follow_up_easy": "What was your immediate first step when you realized the system wasn't behaving as expected?"
    },
    {
        "question": "Describe a situation where you had a disagreement with a team member or technical lead regarding an architectural decision. How did you resolve it?",
        "category": "Communication",
        "difficulty": "Medium",
        "concept": "technical conflict resolution",
        "follow_up_hard": "Looking back, what data or proof-of-concept did you present to build consensus, and what was the long-term outcome?",
        "follow_up_easy": "How did you ensure the final decision aligned with the team's shared goals?"
    },
    {
        "question": "Give an example of a project where you had to quickly learn an unfamiliar technology or framework to meet an aggressive project deadline.",
        "category": "Situational",
        "difficulty": "Easy",
        "concept": "rapid learning & adaptability",
        "follow_up_hard": "How did you balance moving quickly with maintaining clean code, documentation, and automated test coverage?",
        "follow_up_easy": "What resources (documentation, tutorials, community) did you rely on most?"
    },
    {
        "question": "Can you walk me through a time when you received constructive criticism on your code or performance during a review? How did you respond?",
        "category": "HR",
        "difficulty": "Easy",
        "concept": "receptiveness to feedback",
        "follow_up_hard": "How do you proactively conduct code reviews for peers to maintain high engineering standards without causing friction?",
        "follow_up_easy": "What was one specific change you made following that feedback?"
    }
]


# =========================================================
# QUESTION GENERATION ENGINE
# =========================================================

def extract_verified_resume_facts(resume_text: str) -> Dict[str, Any]:
    """
    Extract factual skills, technologies, and projects present in resume.
    Ensures questions are strictly grounded in candidate's actual text.
    """
    if not resume_text or not resume_text.strip():
        return {"skills": [], "projects": [], "education": []}

    text_lower = resume_text.lower()
    verified_skills = []

    for skill in SKILLS_DATABASE:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            verified_skills.append(skill)

    projects_raw = extract_section(resume_text, ["Projects", "Project", "Academic Projects", "Personal Projects"])
    education_raw = extract_education_details(resume_text)

    # Extract distinct project names or sentences
    project_items = []
    if projects_raw:
        for line in projects_raw.split("\n"):
            line_str = line.strip(" -*•\t")
            if 10 <= len(line_str) <= 120 and not line_str.lower().startswith(("technology", "technologies", "tools", "link")):
                project_items.append(line_str)

    return {
        "skills": verified_skills[:12],
        "projects": project_items[:4],
        "education": education_raw
    }


def extract_job_focus_areas(job_description: str) -> Dict[str, Any]:
    """Extract required skills, tools, and responsibilities from a job description."""
    if not job_description or not job_description.strip():
        return {"required_skills": [], "keywords": []}

    skills = extract_job_skills(job_description)
    return {
        "required_skills": skills[:10],
        "keywords": [s.lower() for s in skills]
    }


def format_interviewer_framing(personality: str, question_text: str, is_intro: bool = False, role: str = "") -> str:
    """Format question text according to selected interviewer personality style."""
    if is_intro:
        if personality == "Strict":
            return f"Welcome. We have a focused agenda for the {role} role today. Let's begin immediately with your first question:\n\n{question_text}"
        elif personality == "Friendly":
            return f"Hello! Thanks so much for taking the time to speak with us today for the {role} position. We want this to be a great conversation. Let's start with this:\n\n{question_text}"
        elif personality == "Technical":
            return f"Hi there. I'll be assessing your technical depth and problem-solving capability for the {role} role. Let's start with our first technical challenge:\n\n{question_text}"
        elif personality == "HR":
            return f"Welcome! We're excited to learn more about your background, career trajectory, and practical fit for our {role} opening. Let's get started:\n\n{question_text}"
        else:  # Professional default
            return f"Welcome to your interview for the {role} position. Let's begin with our first question:\n\n{question_text}"

    return question_text


def generate_first_question(
    target_role: str,
    interview_type: str = "Technical",
    difficulty: str = "Adaptive",
    interviewer_personality: str = "Professional",
    resume_text: str = "",
    job_description: str = "",
) -> Dict[str, Any]:
    """Generate the initial question tailored to role, mode, resume, and job description."""
    resume_facts = extract_verified_resume_facts(resume_text)
    job_facts = extract_job_focus_areas(job_description)

    question_text = ""
    category = "Technical Knowledge"
    concept = "fundamentals"
    context_origin = "role_default"

    # Case 1: Resume-Based Interview
    if interview_type in ("Resume-Based", "Technical", "Mixed") and resume_facts["projects"]:
        proj = resume_facts["projects"][0]
        question_text = f"In your resume, you highlighted your project '{proj}'. Can you walk me through the high-level architecture, the key technical trade-offs you made, and what specific impact or result you achieved?"
        category = "Projects"
        concept = f"resume project: {proj[:30]}"
        context_origin = f"resume:project:{proj[:25]}"
    elif interview_type in ("Resume-Based", "Technical") and resume_facts["skills"]:
        top_skill = resume_facts["skills"][0]
        question_text = f"Your resume indicates experience with {top_skill}. How have you leveraged {top_skill} in production or academic projects, and how do you approach debugging or optimizing performance with it?"
        category = "Resume Questions"
        concept = f"resume skill: {top_skill}"
        context_origin = f"resume:skill:{top_skill}"

    # Case 2: Job-Specific Interview
    elif interview_type == "Job-Specific" and job_facts["required_skills"]:
        top_req = job_facts["required_skills"][0]
        question_text = f"This position heavily emphasizes hands-on experience with {top_req}. Can you explain your depth with {top_req}, and describe how you would design or troubleshoot a key workflow using it for this role?"
        category = "Technical Knowledge"
        concept = f"job skill: {top_req}"
        context_origin = f"job:requirement:{top_req}"

    # Case 3: Behavioral / HR Mode
    elif interview_type in ("Behavioral", "HR"):
        b_item = BEHAVIORAL_QUESTION_BANK[0]
        question_text = b_item["question"]
        category = b_item["category"]
        concept = b_item["concept"]
        context_origin = "behavioral_bank"

    # Case 4: General / Technical Fallback
    else:
        role_lower = target_role.lower()
        matched_bank = None
        for k, bank_items in TECHNICAL_QUESTION_BANK.items():
            if k in role_lower:
                matched_bank = bank_items
                break

        if matched_bank:
            item = matched_bank[0]
            question_text = item["question"]
            category = item["category"]
            concept = item["concept"]
            context_origin = f"bank:{concept}"
        else:
            question_text = f"As a candidate for the {target_role} position, how do you approach breaking down a complex, ambiguous technical problem from initial requirements to production deployment?"
            category = "Problem Solving"
            concept = "problem solving process"
            context_origin = "general_framework"

    formatted_text = format_interviewer_framing(
        personality=interviewer_personality,
        question_text=question_text,
        is_intro=True,
        role=target_role
    )

    return {
        "question_number": 1,
        "question_text": formatted_text,
        "raw_question": question_text,
        "category": category,
        "difficulty": "Medium" if difficulty == "Adaptive" else difficulty,
        "concept": concept,
        "context_origin": context_origin
    }


def generate_adaptive_next_question(
    target_role: str,
    question_number: int,
    total_questions: int,
    previous_question: Dict[str, Any],
    last_evaluation: Dict[str, Any],
    interview_type: str = "Technical",
    difficulty: str = "Adaptive",
    interviewer_personality: str = "Professional",
    resume_text: str = "",
    job_description: str = "",
    asked_concepts: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Dynamically synthesize the next question based on user performance:
    - Score >= 80: Escalate to deeper follow-up, architectural trade-offs, or harder concept.
    - Score < 60: Ask clarification, fundamental concept, or step-back recovery question.
    - 60 <= Score < 80: Ask related topic or next syllabus requirement.
    """
    asked_concepts = asked_concepts or []
    last_score = last_evaluation.get("overall_answer_score", 70.0)
    prev_category = previous_question.get("category", "Technical Knowledge")
    prev_concept = previous_question.get("concept", "")

    resume_facts = extract_verified_resume_facts(resume_text)
    job_facts = extract_job_focus_areas(job_description)

    next_difficulty = "Medium"
    if difficulty == "Adaptive":
        if last_score >= 80:
            next_difficulty = "Hard"
        elif last_score < 60:
            next_difficulty = "Easy"
        else:
            next_difficulty = "Medium"
    else:
        next_difficulty = difficulty

    # 1. Follow-Up Branching based on previous question item
    # Search bank for previous concept follow-ups
    follow_up_text = None
    for domain, items in TECHNICAL_QUESTION_BANK.items():
        for it in items:
            if it.get("concept") == prev_concept:
                if last_score >= 80 and it.get("follow_up_hard"):
                    follow_up_text = it["follow_up_hard"]
                elif last_score < 60 and it.get("follow_up_easy"):
                    follow_up_text = it["follow_up_easy"]
                break
        if follow_up_text:
            break

    if not follow_up_text:
        for b_it in BEHAVIORAL_QUESTION_BANK:
            if b_it.get("concept") == prev_concept:
                if last_score >= 80 and b_it.get("follow_up_hard"):
                    follow_up_text = b_it["follow_up_hard"]
                elif last_score < 60 and b_it.get("follow_up_easy"):
                    follow_up_text = b_it["follow_up_easy"]
                break

    # If adaptive follow-up exists and hasn't been asked yet
    if follow_up_text and follow_up_text not in asked_concepts:
        return {
            "question_number": question_number,
            "question_text": follow_up_text,
            "raw_question": follow_up_text,
            "category": prev_category,
            "difficulty": next_difficulty,
            "concept": f"followup:{prev_concept}",
            "context_origin": f"adaptive_followup:{'hard' if last_score >= 80 else 'recovery'}"
        }

    # 2. Transition to a new unasked topic
    # Mix in behavioral for technical/general if question_number is midway
    if interview_type in ("Mixed", "General") and question_number == (total_questions // 2):
        b_cand = [b for b in BEHAVIORAL_QUESTION_BANK if b["concept"] not in asked_concepts]
        b_pick = b_cand[0] if b_cand else BEHAVIORAL_QUESTION_BANK[0]
        return {
            "question_number": question_number,
            "question_text": b_pick["question"],
            "raw_question": b_pick["question"],
            "category": b_pick["category"],
            "difficulty": next_difficulty,
            "concept": b_pick["concept"],
            "context_origin": "behavioral_midway"
        }

    # If Job-Specific, look for remaining required job skills
    if interview_type in ("Job-Specific", "Technical") and job_facts["required_skills"]:
        unasked_skills = [s for s in job_facts["required_skills"] if s.lower() not in [c.lower() for c in asked_concepts]]
        if unasked_skills:
            target_skill = unasked_skills[0]
            q_text = f"Looking at the requirements for this role, {target_skill} is essential. How would you design a scalable solution utilizing {target_skill}, and what edge cases or performance bottlenecks would you watch out for?"
            return {
                "question_number": question_number,
                "question_text": q_text,
                "raw_question": q_text,
                "category": "Technical Knowledge",
                "difficulty": next_difficulty,
                "concept": target_skill,
                "context_origin": f"job_requirement:{target_skill}"
            }

    # If Resume-Based, look for remaining unasked resume skills or projects
    if interview_type in ("Resume-Based", "Technical") and resume_facts["skills"]:
        unasked_r_skills = [s for s in resume_facts["skills"] if s.lower() not in [c.lower() for c in asked_concepts]]
        if unasked_r_skills:
            target_r_skill = unasked_r_skills[0]
            q_text = f"You noted proficiency with {target_r_skill} on your resume. Could you describe an instance where {target_r_skill} didn't perform as expected or where you had to debug a difficult problem?"
            return {
                "question_number": question_number,
                "question_text": q_text,
                "raw_question": q_text,
                "category": "Resume Questions",
                "difficulty": next_difficulty,
                "concept": target_r_skill,
                "context_origin": f"resume_skill:{target_r_skill}"
            }

    # Select from Technical Question Bank
    available_items = []
    for domain, items in TECHNICAL_QUESTION_BANK.items():
        for item in items:
            if item["concept"] not in asked_concepts:
                available_items.append(item)

    if available_items:
        # Match difficulty preference if possible
        diff_matched = [it for it in available_items if it.get("difficulty") == next_difficulty]
        chosen = diff_matched[0] if diff_matched else available_items[0]
        return {
            "question_number": question_number,
            "question_text": chosen["question"],
            "raw_question": chosen["question"],
            "category": chosen["category"],
            "difficulty": next_difficulty,
            "concept": chosen["concept"],
            "context_origin": f"bank:{chosen['concept']}"
        }

    # Fallback System Design / Problem Solving Question
    fallback_questions = [
        ("How do you ensure data integrity, idempotency, and high availability when designing microservices?", "System Design", "microservices integrity"),
        ("Describe your approach to writing unit tests, integration tests, and maintaining automated CI/CD quality gates.", "Coding Concepts", "testing & CI/CD"),
        ("Tell me about a time you had to make a tough technical compromise due to tight project deadlines.", "Behavioral", "technical compromises"),
        ("How would you monitor and observe a production service to detect memory leaks and traffic spikes before users notice?", "Problem Solving", "production observability")
    ]

    for f_text, f_cat, f_conc in fallback_questions:
        if f_conc not in asked_concepts:
            return {
                "question_number": question_number,
                "question_text": f_text,
                "raw_question": f_text,
                "category": f_cat,
                "difficulty": next_difficulty,
                "concept": f_conc,
                "context_origin": "framework_fallback"
            }

    # Absolute fallback
    final_q = f"In a fast-evolving engineering environment for {target_role}, what is your strategy for evaluating new tools or libraries before adopting them into a production codebase?"
    return {
        "question_number": question_number,
        "question_text": final_q,
        "raw_question": final_q,
        "category": "Problem Solving",
        "difficulty": next_difficulty,
        "concept": "tool evaluation strategy",
        "context_origin": "standard_fallback"
    }
