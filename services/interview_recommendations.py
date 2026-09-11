"""
Interview Recommendations & Improvement Engine
Analyzes cumulative session evaluations to extract genuine skill gaps, synthesize
actionable study plans, and generate targeted 'Improvement Mode' mini-interviews.
"""

from typing import Dict, Any, List, Optional


TOPIC_STUDY_MAP: Dict[str, Dict[str, Any]] = {
    "system design": {
        "label": "System Design & Distributed Scalability",
        "action": "Review high-throughput architecture, horizontal caching (Redis), database sharding, and latency optimization.",
        "practice_category": "System Design"
    },
    "tradeoff": {
        "label": "Architectural Trade-Off Analysis",
        "action": "Practice articulating the pros and cons of technologies (e.g. SQL vs NoSQL, Synchronous REST vs Asynchronous Event Queues).",
        "practice_category": "Problem Solving"
    },
    "sql": {
        "label": "SQL Query Tuning & Indexing",
        "action": "Practice indexing strategies, query execution plans (EXPLAIN), and multi-table joins under high concurrency.",
        "practice_category": "Technical Knowledge"
    },
    "api": {
        "label": "REST API Architecture & Security",
        "action": "Study idempotent API design, token-based authentication (JWT/OAuth), and rate limiting implementations.",
        "practice_category": "Coding Concepts"
    },
    "behavioral": {
        "label": "STAR Behavioral Framework",
        "action": "Structure stories into Situation, Task, Action, and quantifiable Result with measurable impact metrics.",
        "practice_category": "Behavioral"
    },
    "concurrency": {
        "label": "Concurrency & Asynchronous Programming",
        "action": "Study thread synchronization, event loops (asyncio/Node), race conditions, and non-blocking I/O.",
        "practice_category": "Technical Knowledge"
    },
    "testing": {
        "label": "Testing & Code Quality Gates",
        "action": "Incorporate unit testing, mock dependencies, integration suites, and automated CI/CD checks into your answers.",
        "practice_category": "Coding Concepts"
    }
}


def synthesize_session_report(
    target_role: str,
    questions: List[Dict[str, Any]],
    answers: List[Dict[str, Any]],
    evaluations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Synthesize an honest, transparent performance report from all evaluated answers.
    """
    if not evaluations:
        return {
            "overall_score": 0.0,
            "technical_score": 0.0,
            "problem_solving_score": 0.0,
            "communication_score": 0.0,
            "completeness_score": 0.0,
            "relevance_score": 0.0,
            "strengths": ["Session started."],
            "weaknesses": ["No completed answers evaluated yet."],
            "recommendations": ["Complete answers to generate recommendations."],
            "question_reviews": []
        }

    # Aggregate numerical metrics
    overall_scores = [e.get("overall_answer_score", 0.0) for e in evaluations]
    tech_scores = [e.get("technical_score", 0.0) for e in evaluations]
    ps_scores = [e.get("problem_solving_score", 0.0) for e in evaluations]
    comm_scores = [e.get("clarity_score", 0.0) for e in evaluations]
    comp_scores = [e.get("completeness_score", 0.0) for e in evaluations]
    rel_scores = [e.get("relevance_score", 0.0) for e in evaluations]

    avg_overall = round(sum(overall_scores) / len(overall_scores), 1)
    avg_tech = round(sum(tech_scores) / len(tech_scores), 1)
    avg_ps = round(sum(ps_scores) / len(ps_scores), 1)
    avg_comm = round(sum(comm_scores) / len(comm_scores), 1)
    avg_comp = round(sum(comp_scores) / len(comp_scores), 1)
    avg_rel = round(sum(rel_scores) / len(rel_scores), 1)

    # Collect distinct strengths and areas to improve
    strengths_pool: List[str] = []
    weakness_pool: List[str] = []

    for ev in evaluations:
        for s in ev.get("strengths", []):
            if s not in strengths_pool:
                strengths_pool.append(s)
        for w in ev.get("improvements", []):
            if w not in weakness_pool:
                weakness_pool.append(w)

    # Categorize weaknesses into targeted practice recommendations
    recommendations: List[str] = []
    weak_topics: List[str] = []

    if avg_tech < 75:
        recommendations.append(f"Deepen core technical fundamentals for {target_role}: strengthen specific language keywords and internal mechanisms.")
        weak_topics.append("Core Technical Knowledge")
    if avg_comp < 70:
        recommendations.append("Expand on answer completeness: address technical trade-offs, alternative approaches, and edge cases.")
        weak_topics.append("Architectural Trade-Offs")
    if avg_ps < 75:
        recommendations.append("Ground answers in concrete problem-solving steps: explain root cause diagnostics, profiling, and benchmarking.")
        weak_topics.append("Problem Solving & Diagnostics")
    if avg_comm < 75:
        recommendations.append("Refine answer structure: organize your response with clear sequential points (e.g. First, Next, Finally).")
        weak_topics.append("Communication Structure")

    # Add question-specific weakness mappings
    for ev in evaluations:
        if ev.get("overall_answer_score", 0.0) < 65:
            for top_k, top_info in TOPIC_STUDY_MAP.items():
                if any(top_k in imp.lower() for imp in ev.get("improvements", [])):
                    if top_info["action"] not in recommendations:
                        recommendations.append(top_info["action"])
                    if top_info["label"] not in weak_topics:
                        weak_topics.append(top_info["label"])

    if not recommendations:
        recommendations.append("Strong overall performance! Continue taking hard/adaptive mock interviews to maintain peak interview readiness.")
        recommendations.append("Practice system design whiteboarding and high-concurrency scaling scenarios.")

    # Build Question-by-Question Review objects
    question_reviews = []
    for idx in range(len(evaluations)):
        q_obj = questions[idx] if idx < len(questions) else {}
        a_obj = answers[idx] if idx < len(answers) else {}
        e_obj = evaluations[idx]

        question_reviews.append({
            "question_number": q_obj.get("question_number", idx + 1),
            "question_text": q_obj.get("question_text", "Question"),
            "category": q_obj.get("category", "Technical Knowledge"),
            "difficulty": q_obj.get("difficulty", "Medium"),
            "answer_text": a_obj.get("answer_text", ""),
            "overall_score": e_obj.get("overall_answer_score", 0.0),
            "feedback": e_obj.get("feedback", ""),
            "strengths": e_obj.get("strengths", []),
            "improvements": e_obj.get("improvements", [])
        })

    return {
        "overall_score": avg_overall,
        "technical_score": avg_tech,
        "problem_solving_score": avg_ps,
        "communication_score": avg_comm,
        "completeness_score": avg_comp,
        "relevance_score": avg_rel,
        "strengths": strengths_pool[:5] if strengths_pool else ["Solid effort attempting all interview questions."],
        "weaknesses": weak_topics[:5] if weak_topics else ["Minor edge cases and trade-off elaboration."],
        "recommendations": recommendations[:5],
        "question_reviews": question_reviews
    }


def generate_improvement_interview_plan(
    target_role: str,
    weak_topics: List[str],
    question_count: int = 3,
) -> Dict[str, Any]:
    """
    Generate an 'Improvement Mode' targeted practice session
    focusing heavily on candidate's detected weaknesses.
    """
    focus_areas = weak_topics[:3] if weak_topics else ["System Design", "Core Fundamentals", "Problem Solving"]
    focus_summary = ", ".join(focus_areas)

    return {
        "mode": "Improvement Mode",
        "target_role": target_role,
        "focus_areas": focus_areas,
        "focus_summary": focus_summary,
        "question_count": max(3, min(question_count, 5)),
        "difficulty": "Adaptive",
        "guidance": f"This targeted practice session is calibrated to strengthen your performance in: {focus_summary}. Focus on concrete examples, trade-offs, and structured explanations."
    }
