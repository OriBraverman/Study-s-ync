"""
ArmorAgent LangGraph Pipeline
Orchestrates: Analyzer -> PruningRouter -> Retriever -> Planner

State flows through four nodes:
  analyzer       : StudentInputSchema  -> MissedTopicsSchema
  pruning_router : MissedTopicsSchema  -> PrunedTopicsSchema
  retriever      : PrunedTopicsSchema  -> List[RetrievedChunk]
  planner        : everything          -> BootcampPlanSchema
"""
from typing import List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from src.agents.analyzer import analyze_missed_topics
from src.agents.planner import generate_bootcamp_plan
from src.agents.pruning_router import prune_topics
from src.agents.retriever import retrieve_for_topics
from src.schemas.models import (
    BootcampPlanSchema,
    MissedTopicsSchema,
    PrunedTopicsSchema,
    RetrievedChunk,
    StudentInputSchema,
)


# ---------------------------------------------------------------------------
# Shared graph state
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    student_input: StudentInputSchema
    missed_topics: Optional[MissedTopicsSchema]
    pruned_topics: Optional[PrunedTopicsSchema]
    retrieved_chunks: Optional[List[RetrievedChunk]]
    bootcamp_plan: Optional[BootcampPlanSchema]
    error: Optional[str]


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------

def analyzer_node(state: AgentState) -> AgentState:
    """
    Node 1 — Syllabus Analyzer.
    Reads the absence window from student_input and maps it to missed topics.
    """
    try:
        student_input = state["student_input"]
        missed = analyze_missed_topics(student_input)
        return {**state, "missed_topics": missed, "error": None}
    except Exception as exc:
        return {**state, "error": f"Analyzer failed: {exc}"}


def pruning_router_node(state: AgentState) -> AgentState:
    """
    Node 2 — Pruning Router.
    Validates and deduplicates missed topics; collects pruning statistics.
    """
    if state.get("error"):
        return state
    try:
        missed = state["missed_topics"]
        if missed is None:
            return {**state, "error": "Pruning router: missed_topics is None"}
        pruned = prune_topics(missed)
        return {**state, "pruned_topics": pruned}
    except Exception as exc:
        return {**state, "error": f"Pruning router failed: {exc}"}


def retriever_node(state: AgentState) -> AgentState:
    """
    Node 3 — Retrieval Agent.
    Queries ChromaDB for content matching each validated missed topic.
    """
    if state.get("error"):
        return state
    try:
        pruned = state["pruned_topics"]
        if pruned is None:
            return {**state, "error": "Retriever: pruned_topics is None"}
        chunks = retrieve_for_topics(pruned)
        return {**state, "retrieved_chunks": chunks}
    except Exception as exc:
        return {**state, "error": f"Retriever failed: {exc}"}


def planner_node(state: AgentState) -> AgentState:
    """
    Node 4 — Bootcamp Planner.
    Synthesises retrieved content into a day-by-day study plan.
    """
    if state.get("error"):
        return state
    try:
        student_input = state["student_input"]
        pruned = state["pruned_topics"]
        chunks = state.get("retrieved_chunks") or []

        if pruned is None:
            return {**state, "error": "Planner: pruned_topics is None"}

        plan = generate_bootcamp_plan(
            student_name=student_input.student_name,
            pruned_schema=pruned,
            retrieved_chunks=chunks,
        )
        return {**state, "bootcamp_plan": plan}
    except Exception as exc:
        return {**state, "error": f"Planner failed: {exc}"}


# ---------------------------------------------------------------------------
# Conditional edge
# ---------------------------------------------------------------------------

def should_continue_after_pruning(state: AgentState) -> str:
    """
    After pruning, decide whether to proceed or end early.
    If there are no validated topics left (all pruned) there is nothing to
    study — skip retrieval and planning.
    """
    if state.get("error"):
        return "end_early"
    pruned = state.get("pruned_topics")
    if pruned is not None and len(pruned.validated_missed_topics) == 0:
        return "end_early"
    return "continue"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Build and compile the LangGraph state machine."""
    workflow = StateGraph(AgentState)

    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("pruning_router", pruning_router_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("planner", planner_node)

    workflow.set_entry_point("analyzer")
    workflow.add_edge("analyzer", "pruning_router")
    workflow.add_conditional_edges(
        "pruning_router",
        should_continue_after_pruning,
        {"continue": "retriever", "end_early": END},
    )
    workflow.add_edge("retriever", "planner")
    workflow.add_edge("planner", END)

    return workflow.compile()


def run_pipeline(student_input: StudentInputSchema) -> BootcampPlanSchema:
    """
    Run the full ArmorAgent pipeline end-to-end.

    Args:
        student_input: validated StudentInputSchema

    Returns:
        BootcampPlanSchema with the complete study plan

    Raises:
        RuntimeError: if any agent node encounters an unrecoverable error
        ValueError: if the pipeline ends without producing a bootcamp plan
                    (e.g., all topics pruned)
    """
    graph = build_graph()

    initial_state: AgentState = {
        "student_input": student_input,
        "missed_topics": None,
        "pruned_topics": None,
        "retrieved_chunks": None,
        "bootcamp_plan": None,
        "error": None,
    }

    result = graph.invoke(initial_state)

    if result.get("error"):
        raise RuntimeError(result["error"])

    plan = result.get("bootcamp_plan")
    if plan is None:
        # Pipeline ended early (all topics pruned) — return a minimal plan
        pruned = result.get("pruned_topics")
        if pruned is not None:
            from datetime import datetime
            from src.schemas.models import PruningStats

            return BootcampPlanSchema(
                student_name=student_input.student_name,
                course_name=student_input.course_name,
                course_num=student_input.course_num,
                generated_at=datetime.utcnow().isoformat() + "Z",
                total_days=0,
                total_hours=0.0,
                executive_summary=(
                    f"No missed topics were found for {student_input.course_name} "
                    f"in the specified absence period, or all identified topics were "
                    "administrative entries (exams, holidays, etc.). "
                    "No recovery bootcamp is needed!"
                ),
                study_tasks=[],
                pruning_stats=pruned.pruning_stats,
                sources_used=[],
            )
        raise ValueError("Pipeline produced no bootcamp plan and no pruned topics.")

    return plan
