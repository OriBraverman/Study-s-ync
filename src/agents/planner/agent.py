"""
Study[S]ync Planner Agent

The Planner Agent is the core intelligence of the system. It:
1. Analyzes the student's missed dates and course syllabus
2. Identifies which topics were missed
3. Prunes administrative/duplicate topics
4. Retrieves relevant study material
5. Generates a prioritized day-by-day recovery plan

This agent effectively combines the legacy analyzer, pruning_router,
retriever, and planner modules into a unified interface.
"""
from datetime import date
from typing import List, Optional

from src.schemas.models import (
    BootcampPlanSchema,
    MissedTopicsSchema,
    PrunedTopicsSchema,
    RetrievedChunk,
    StudentInputSchema,
)

# Re-export core functions for convenience
from src.agents.analyzer import analyze_missed_topics, estimate_missed_weeks, load_syllabus
from src.agents.pruning_router import prune_topics, is_admin_entry, normalize_topic
from src.agents.retriever import retrieve_for_topics
from src.agents.planner_core import generate_bootcamp_plan, create_mock_bootcamp_plan


def create_study_plan(
    student_input: StudentInputSchema,
    syllabus_path: Optional[str] = None,
) -> BootcampPlanSchema:
    """
    Unified planner entry point.

    Runs the full internal pipeline:
    Analyzer -> Pruning Router -> Retriever -> Planner

    Args:
        student_input: Validated student input with course and absence window.
        syllabus_path: Optional override for syllabuses.json path.

    Returns:
        BootcampPlanSchema with the complete study plan.
    """
    # Step 1: Analyze missed topics
    missed = analyze_missed_topics(student_input, syllabus_path or "data/raw/syllabuses.json")

    # Step 2: Prune topics
    pruned = prune_topics(missed)

    # Step 3: Retrieve material
    chunks = retrieve_for_topics(pruned)

    # Step 4: Generate plan
    plan = generate_bootcamp_plan(
        student_name=student_input.student_name,
        pruned_schema=pruned,
        retrieved_chunks=chunks,
    )

    return plan
