"""
Interview Answer Evaluator Service
Provides transparent, multi-dimensional scoring of interview answers across:
- Technical Correctness
- Relevance to Question
- Completeness
- Clarity & Communication
- Problem Solving & Practical Examples
Strictly grounded in observable textual evidence without fabricating psychological confidence.
"""

import re
from typing import Dict, Any, List, Optional, Tuple


# Technical signal keywords indicating deep engineering understanding
PRACTICAL_KEYWORDS = [
    "tradeoff", "trade-off", "tradeoffs", "trade-offs", "latency", "throughput",
    "scalable", "scaling", "cache", "caching", "index", "indexing", "concurrency",
    "async", "asynchronous", "thread", "memory", "leak", "garbage collection",
    "overhead", "bottleneck", "profiling", "benchmark", "optimize", "optimization",
    "testing", "unit test", "integration test", "mock", "docker", "container",
    "production", "deploy", "rollback", "ci/cd", "observability", "metrics",
    "logging", "distributed", "idempotent", "failover", "replica", "partition"
]

# Behavioral STAR methodology indicators
STAR_INDICATORS = {
    "situation": ["when i was", "at my previous", "in my project", "the situation was", "our team faced", "we were building"],
    "task": ["my responsibility was", "the goal was", "the task was", "i was tasked with", "needed to"],
    "action": ["i implemented", "i investigated", "i refactored", "i analyzed", "i designed", "my approach was", "i collaborated"],
    "result": ["as a result", "which reduced", "improved", "increased", "successfully delivered", "the outcome was", "resulting in"]
}

FILLER_PATTERNS = [r"\bumm?\b", r"\bahh?\b", r"\blike\b", r"\byou know\b", r"\bbasically\b"]


def evaluate_answer(
    question_text: str,
    answer_text: str,
    category: str = "Technical Knowledge",
    difficulty: str = "Medium",
    target_role: str = "",
) -> Dict[str, Any]:
    """
    Evaluate a candidate's answer with objective, transparent scoring formulas
    and actionable feedback.
    """
    cleaned = (answer_text or "").strip()
    words = cleaned.split()
    word_count = len(words)

    # Empty or trivial response guardrail
    if word_count < 4:
        return {
            "overall_answer_score": 10.0,
            "technical_score": 10.0,
            "relevance_score": 15.0,
            "completeness_score": 5.0,
            "clarity_score": 20.0,
            "problem_solving_score": 10.0,
            "feedback": "The answer was too brief or empty to assess your technical depth. In interviews, aim to explain your reasoning, practical architecture, and concrete examples.",
            "strengths": [],
            "improvements": [
                "Provide a complete structured response explaining core concepts.",
                "Mention concrete examples, tools, or libraries you have used.",
                "Address edge cases or potential technical trade-offs."
            ],
            "detected_topics": [],
            "is_strong": False
        }

    lower_ans = cleaned.lower()
    lower_q = question_text.lower()

    # 1. Relevance Scoring (0-100)
    # Check question keyword overlap in candidate's response
    q_words = [w for w in re.findall(r"\b[a-z]{4,}\b", lower_q) if w not in ("what", "when", "where", "which", "would", "explain", "describe", "tell", "about")]
    matched_q_words = [w for w in q_words if w in lower_ans]
    relevance_ratio = len(matched_q_words) / max(len(q_words), 1)
    relevance_score = min(100.0, max(35.0, round(40.0 + (relevance_ratio * 60.0), 1)))

    # 2. Technical Correctness & Concept Density (0-100)
    practical_hits = [k for k in PRACTICAL_KEYWORDS if k in lower_ans]
    hit_count = len(practical_hits)

    if category in ("Behavioral", "Communication", "HR"):
        # For behavioral questions, check STAR presence
        star_coverage = sum(1 for phase, ph_phrases in STAR_INDICATORS.items() if any(p in lower_ans for p in ph_phrases))
        technical_score = min(100.0, round(50.0 + (star_coverage * 12.5), 1))
    else:
        # For technical questions, reward vocabulary and specificity
        if hit_count >= 5:
            technical_score = min(96.0, round(82.0 + (hit_count * 2.5), 1))
        elif hit_count >= 2:
            technical_score = round(68.0 + (hit_count * 5.0), 1)
        else:
            technical_score = min(65.0, max(45.0, round(45.0 + (word_count * 0.2), 1)))

    # 3. Completeness Scoring (0-100)
    # Ideal answer length: 60-250 words
    if word_count >= 120:
        completeness_score = min(95.0, round(80.0 + (min(word_count, 220) - 120) * 0.15, 1))
    elif word_count >= 60:
        completeness_score = round(65.0 + ((word_count - 60) * 0.25), 1)
    elif word_count >= 30:
        completeness_score = round(45.0 + ((word_count - 30) * 0.65), 1)
    else:
        completeness_score = round(30.0 + (word_count * 0.5), 1)

    # Penalize if lacks trade-offs or examples for hard questions
    if difficulty == "Hard" and not any(t in lower_ans for t in ["tradeoff", "trade-off", "limitation", "drawback", "alternative", "however"]):
        completeness_score = max(40.0, completeness_score - 10.0)

    # 4. Clarity & Communication Structure (0-100)
    sentences = [s.strip() for s in re.split(r"[.!?]+", cleaned) if s.strip()]
    num_sentences = len(sentences)
    avg_sentence_len = word_count / max(num_sentences, 1)

    clarity_base = 75.0
    if 10 <= avg_sentence_len <= 25:
        clarity_base += 15.0  # Well-paced sentences
    elif avg_sentence_len > 35:
        clarity_base -= 10.0  # Run-on sentences

    # Check for formatting/structure: bullet points, enumeration (first, second, also)
    if any(m in lower_ans for m in ["first", "secondly", "additionally", "furthermore", "for example", "specifically"]):
        clarity_base += 8.0

    clarity_score = min(98.0, max(40.0, round(clarity_base, 1)))

    # 5. Problem Solving & Practical Grounding (0-100)
    ps_signals = ["because", "therefore", "in order to", "investigated", "diagnosed", "mitigate", "measured", "designed", "handled"]
    ps_matches = [s for s in ps_signals if s in lower_ans]
    ps_score = min(96.0, max(45.0, round(50.0 + (len(ps_matches) * 8.0) + (len(practical_hits) * 3.0), 1)))

    # Calculate Overall Answer Score
    overall_score = round(
        (technical_score * 0.35) +
        (relevance_score * 0.25) +
        (completeness_score * 0.20) +
        (clarity_score * 0.10) +
        (ps_score * 0.10),
        1
    )

    # Generate Constructive Strengths & Improvements
    strengths = []
    improvements = []

    if relevance_score >= 75:
        strengths.append("Directly addressed the core concepts outlined in the prompt.")
    if technical_score >= 75:
        strengths.append(f"Demonstrated solid technical vocabulary ({', '.join(practical_hits[:3]) or 'clear principles'}).")
    if completeness_score >= 75:
        strengths.append(f"Provided good depth and detail ({word_count} words).")
    if clarity_score >= 80:
        strengths.append("Well-structured phrasing with clear logical progression.")
    if ps_score >= 75:
        strengths.append("Clearly articulated reasoning and practical problem-solving steps.")

    if not strengths:
        strengths.append("Attempted the question with recognizable basic terminology.")

    # Identified areas to improve
    if completeness_score < 70:
        improvements.append("Elaborate further: describe the specific steps, libraries, or architecture you would use.")
    if not any(t in lower_ans for t in ["tradeoff", "trade-off", "drawback", "alternative"]):
        improvements.append("Discuss technical trade-offs: what are the pros/cons of this approach vs alternatives?")
    if not any(e in lower_ans for e in ["for example", "such as", "in my experience", "recently", "instance"]):
        improvements.append("Ground your answer in a concrete project example or real-world production experience.")
    if category == "Behavioral" and not any(r in lower_ans for r in STAR_INDICATORS["result"]):
        improvements.append("Highlight the measurable result or business outcome using the STAR method.")
    if clarity_score < 70:
        improvements.append("Break long complex explanations into structured paragraphs or sequential points.")

    if not improvements:
        improvements.append("Keep practicing advanced architectural trade-offs to reach senior engineering depth.")

    # Synthesize concise feedback paragraph
    if overall_score >= 80:
        feedback = "Strong, confident response. You demonstrated accurate technical comprehension and supported your logic with relevant engineering context."
    elif overall_score >= 60:
        feedback = "Good foundation with valid points. To elevate this to a top-tier answer, introduce concrete trade-offs, mention specific metrics or tools, and provide an illustrative example."
    else:
        feedback = "Partially answered, but lacks depth and specificity. Focus on clearly explaining the underlying mechanism, why that approach is chosen, and how you would handle failure cases."

    return {
        "overall_answer_score": overall_score,
        "technical_score": technical_score,
        "relevance_score": relevance_score,
        "completeness_score": completeness_score,
        "clarity_score": clarity_score,
        "problem_solving_score": ps_score,
        "feedback": feedback,
        "strengths": strengths,
        "improvements": improvements,
        "detected_topics": practical_hits[:4],
        "is_strong": overall_score >= 80
    }
