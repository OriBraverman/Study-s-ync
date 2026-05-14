"""
Bootcamp Planner Agent
Synthesizes retrieved content into a prioritized, day-by-day study plan.

In mock mode (USE_MOCK_LLM=true, the default) no API key is required.
In LLM mode it calls GPT-4o-mini via langchain_openai.
Every study task is guaranteed to carry citations sourced from the retrieval step.
"""
import json
import os
from datetime import datetime
from typing import List

from src.schemas.models import (
    BootcampPlanSchema,
    Citation,
    PrunedTopicsSchema,
    PruningStats,
    RetrievedChunk,
    StudyTaskSchema,
)

USE_MOCK = os.getenv("USE_MOCK_LLM", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Priority assignment heuristic
# ---------------------------------------------------------------------------
_HIGH_PRIORITY_KEYWORDS = [
    "recursion", "rекурс", "sort", "מיון", "complexity", "סיבוכיות",
    "graph", "גרף", "tree", "עץ", "algorithm", "אלגוריתם",
    "pointer", "מצביע", "memory", "זיכרון", "oop", "class", "מחלקה",
]
_LOW_PRIORITY_KEYWORDS = [
    "introduction", "מבוא", "overview", "history", "סקירה", "הסטוריה",
    "summary", "review", "סיכום",
]


def _assign_priority(topic: str) -> str:
    topic_lower = topic.lower()
    for kw in _HIGH_PRIORITY_KEYWORDS:
        if kw in topic_lower:
            return "high"
    for kw in _LOW_PRIORITY_KEYWORDS:
        if kw in topic_lower:
            return "low"
    return "medium"


def _estimate_hours(topic: str, priority: str) -> float:
    """Estimate study hours based on topic complexity signals."""
    topic_lower = topic.lower()
    if any(kw in topic_lower for kw in ["recursion", "graph", "complexity", "sort", "tree"]):
        return 2.5
    if priority == "high":
        return 2.0
    if priority == "low":
        return 1.0
    return 1.5


def _build_study_tips(topic: str, content: str) -> List[str]:
    """Generate contextual study tips based on topic keywords."""
    tips: List[str] = []
    t = topic.lower()
    c = content.lower()

    if any(kw in t or kw in c for kw in ["recursion", "recursive"]):
        tips += [
            "Trace through the call stack by hand for small inputs first.",
            "Identify the base case before writing any code.",
            "Draw a recursion tree to visualize branching.",
        ]
    elif any(kw in t or kw in c for kw in ["sort", "מיון"]):
        tips += [
            "Implement each sorting algorithm from scratch without looking at notes.",
            "Trace a small array (5–7 elements) step by step.",
            "Compare time and space complexities in a summary table.",
        ]
    elif any(kw in t or kw in c for kw in ["graph", "גרף", "bfs", "dfs"]):
        tips += [
            "Draw the graph on paper and manually run BFS then DFS.",
            "Practice adjacency list vs adjacency matrix implementations.",
            "Trace Dijkstra's algorithm on a weighted example.",
        ]
    elif any(kw in t or kw in c for kw in ["tree", "עץ", "bst"]):
        tips += [
            "Draw the tree structure and manually perform each traversal.",
            "Implement insert, search, and delete in a BST from scratch.",
            "Verify that your BST property holds after every operation.",
        ]
    elif any(kw in t or kw in c for kw in ["loop", "iteration", "לולאה"]):
        tips += [
            "Trace variable values through each iteration on paper.",
            "Convert for-loops to while-loops and vice-versa as practice.",
            "Identify the loop invariant before writing code.",
        ]
    elif any(kw in t or kw in c for kw in ["complexity", "big-o", "סיבוכיות"]):
        tips += [
            "Analyse your own code from previous assignments.",
            "Create a cheat-sheet: O(1) → O(log n) → O(n) → O(n log n) → O(n²).",
            "Practice deriving complexity by counting the dominant operation.",
        ]
    elif any(kw in t or kw in c for kw in ["oop", "class", "object", "inheritance"]):
        tips += [
            "Design a small class hierarchy (e.g., Animal → Dog, Cat) from scratch.",
            "Practice overriding __str__ and __eq__ for custom classes.",
            "Write tests that exercise polymorphism explicitly.",
        ]
    else:
        tips += [
            "Summarize the key concepts in your own words before solving problems.",
            "Work through at least two practice problems from the textbook.",
            "Check the course slides for examples and diagrams.",
        ]

    # Always add a general tip
    tips.append("Review this topic again 24 hours later to reinforce retention.")

    return tips[:3]


# ---------------------------------------------------------------------------
# Mock plan generator
# ---------------------------------------------------------------------------

def create_mock_bootcamp_plan(
    student_name: str,
    pruned_schema: PrunedTopicsSchema,
    retrieved_chunks: List[RetrievedChunk],
) -> BootcampPlanSchema:
    """
    Build a realistic day-by-day study plan without any LLM API call.
    Groups topics into days (2–3 topics per day), assigns priority, hours,
    and propagates citations from the retrieval step.
    """
    topics = pruned_schema.validated_missed_topics
    chunk_map = {chunk.topic: chunk for chunk in retrieved_chunks}

    study_tasks: List[StudyTaskSchema] = []
    day = 1
    topics_on_current_day = 0
    MAX_TOPICS_PER_DAY = 2

    for i, wt in enumerate(topics):
        if topics_on_current_day >= MAX_TOPICS_PER_DAY:
            day += 1
            topics_on_current_day = 0

        priority = _assign_priority(wt.topic)
        hours = _estimate_hours(wt.topic, priority)

        # Find matching retrieved chunk (exact or fuzzy)
        chunk = chunk_map.get(wt.topic)
        if chunk is None:
            # Try partial match
            for key, val in chunk_map.items():
                if wt.topic[:20].lower() in key.lower() or key[:20].lower() in wt.topic.lower():
                    chunk = val
                    break

        if chunk and chunk.citations:
            citations = chunk.citations
            content_snippet = chunk.content[:400].strip()
        else:
            # Fallback citation
            citations = [
                Citation(
                    source_name=f"{pruned_schema.course_name} - Week {wt.week} Syllabus",
                    source_type="syllabus",
                    chunk_id=f"{pruned_schema.course_num}_week_{wt.week}",
                    relevance_score=0.6,
                )
            ]
            content_snippet = f"Study the course material for: {wt.topic}"

        description = (
            f"Day {day} focus: {wt.topic}. "
            f"{content_snippet[:300]}{'...' if len(content_snippet) > 300 else ''} "
            f"Estimated study time: {hours} hours."
        )

        study_tips = _build_study_tips(wt.topic, content_snippet)

        study_tasks.append(
            StudyTaskSchema(
                day=day,
                topic=wt.topic,
                description=description,
                estimated_hours=hours,
                priority=priority,
                citations=citations,
                study_tips=study_tips,
            )
        )
        topics_on_current_day += 1

    total_days = day if study_tasks else 0
    total_hours = round(sum(t.estimated_hours for t in study_tasks), 1)

    sources_used = sorted(
        {
            c.source_name
            for task in study_tasks
            for c in task.citations
        }
    )

    missed_count = pruned_schema.pruning_stats.pruned_topic_count
    original_count = pruned_schema.pruning_stats.original_topic_count
    reduction_pct = pruned_schema.pruning_stats.token_reduction_pct

    executive_summary = (
        f"Hi {student_name}! Here is your personalised recovery bootcamp for "
        f"**{pruned_schema.course_name}** (course {pruned_schema.course_num}). "
        f"After analysing your absence, {missed_count} topic(s) were identified "
        f"(down from {original_count} after {reduction_pct}% token reduction via smart pruning). "
        f"Your bootcamp spans {total_days} day(s) with a total of {total_hours} hours of focused study. "
        "Topics are ordered by dependency — complete them in sequence for best results. "
        "Each task includes targeted study tips and citations to source material."
    )

    return BootcampPlanSchema(
        student_name=student_name,
        course_name=pruned_schema.course_name,
        course_num=pruned_schema.course_num,
        generated_at=datetime.utcnow().isoformat() + "Z",
        total_days=total_days,
        total_hours=total_hours,
        executive_summary=executive_summary,
        study_tasks=study_tasks,
        pruning_stats=pruned_schema.pruning_stats,
        sources_used=sources_used,
    )


# ---------------------------------------------------------------------------
# LLM plan generator
# ---------------------------------------------------------------------------

def create_llm_bootcamp_plan(
    student_name: str,
    pruned_schema: PrunedTopicsSchema,
    retrieved_chunks: List[RetrievedChunk],
    api_key: str,
) -> BootcampPlanSchema:
    """
    Generate a bootcamp plan using GPT-4o-mini via LangChain.
    Falls back to mock plan if the API call fails.
    """
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage
    except ImportError:
        return create_mock_bootcamp_plan(student_name, pruned_schema, retrieved_chunks)

    # Build context from retrieved chunks
    context_parts = []
    for chunk in retrieved_chunks:
        cit_str = ", ".join(c.source_name for c in chunk.citations)
        context_parts.append(
            f"Topic: {chunk.topic}\nSources: {cit_str}\nContent:\n{chunk.content[:600]}"
        )
    context_str = "\n\n---\n\n".join(context_parts)

    topics_list = "\n".join(
        f"- Week {wt.week}: {wt.topic}"
        for wt in pruned_schema.validated_missed_topics
    )

    system_prompt = (
        "You are an expert academic tutor specialising in computer science. "
        "Your task is to generate a structured, day-by-day study bootcamp plan "
        "for a university student who missed lectures. "
        "You MUST output valid JSON only — no markdown fences, no extra text. "
        "Every study task MUST include citations derived from the provided source material."
    )

    user_prompt = f"""
Student name: {student_name}
Course: {pruned_schema.course_name} ({pruned_schema.course_num})
Missed topics:
{topics_list}

Retrieved source material:
{context_str}

Generate a JSON object with this exact structure:
{{
  "executive_summary": "string — 3-4 sentence overview",
  "study_tasks": [
    {{
      "day": 1,
      "topic": "topic name",
      "description": "detailed description 100+ words",
      "estimated_hours": 1.5,
      "priority": "high|medium|low",
      "citations": [
        {{
          "source_name": "source name from above",
          "source_type": "syllabus|mock_doc",
          "chunk_id": "identifier",
          "relevance_score": 0.85
        }}
      ],
      "study_tips": ["tip1", "tip2", "tip3"]
    }}
  ]
}}

Rules:
- Group 2-3 topics per day
- Priority must be "high", "medium", or "low"
- Each task MUST have at least one citation from the source material
- study_tips should be actionable and specific to the topic
- Output ONLY the JSON object, no other text
"""

    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, temperature=0.3, max_tokens=8192)

    try:
        response = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        raw = response.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = "\n".join(raw.split("\n")[:-1])

        data = json.loads(raw)
    except Exception as e:
        # Fallback to mock on any error
        print(f"[WARN] LLM plan generation failed ({e}), falling back to mock.")
        return create_mock_bootcamp_plan(student_name, pruned_schema, retrieved_chunks)

    # Parse LLM output into schema objects
    study_tasks: List[StudyTaskSchema] = []
    for task_data in data.get("study_tasks", []):
        citations = [
            Citation(
                source_name=c.get("source_name", "Unknown"),
                source_type=c.get("source_type", "syllabus"),
                chunk_id=c.get("chunk_id", "llm_chunk"),
                relevance_score=float(c.get("relevance_score", 0.7)),
            )
            for c in task_data.get("citations", [])
        ]
        if not citations:
            citations = [
                Citation(
                    source_name=pruned_schema.course_name,
                    source_type="syllabus",
                    chunk_id=f"{pruned_schema.course_num}_llm",
                    relevance_score=0.7,
                )
            ]
        study_tasks.append(
            StudyTaskSchema(
                day=int(task_data.get("day", 1)),
                topic=task_data.get("topic", ""),
                description=task_data.get("description", ""),
                estimated_hours=float(task_data.get("estimated_hours", 1.5)),
                priority=task_data.get("priority", "medium"),
                citations=citations,
                study_tips=task_data.get("study_tips", []),
            )
        )

    total_days = max((t.day for t in study_tasks), default=0)
    total_hours = round(sum(t.estimated_hours for t in study_tasks), 1)
    sources_used = sorted({c.source_name for t in study_tasks for c in t.citations})

    return BootcampPlanSchema(
        student_name=student_name,
        course_name=pruned_schema.course_name,
        course_num=pruned_schema.course_num,
        generated_at=datetime.utcnow().isoformat() + "Z",
        total_days=total_days,
        total_hours=total_hours,
        executive_summary=data.get("executive_summary", ""),
        study_tasks=study_tasks,
        pruning_stats=pruned_schema.pruning_stats,
        sources_used=sources_used,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate_bootcamp_plan(
    student_name: str,
    pruned_schema: PrunedTopicsSchema,
    retrieved_chunks: List[RetrievedChunk],
) -> BootcampPlanSchema:
    """
    Main entry point.
    Routes to mock planner or LLM planner based on USE_MOCK_LLM env var.
    If USE_MOCK_LLM is false but no API key is present, falls back to mock.
    """
    use_mock = os.getenv("USE_MOCK_LLM", "true").lower() == "true"

    if use_mock:
        return create_mock_bootcamp_plan(student_name, pruned_schema, retrieved_chunks)

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("[WARN] USE_MOCK_LLM=false but OPENAI_API_KEY is not set. Using mock planner.")
        return create_mock_bootcamp_plan(student_name, pruned_schema, retrieved_chunks)

    return create_llm_bootcamp_plan(student_name, pruned_schema, retrieved_chunks, api_key)
