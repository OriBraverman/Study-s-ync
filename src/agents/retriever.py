"""
Retrieval Agent
Queries the ChromaDB vector store for content relevant to each pruned topic.
Returns a list of RetrievedChunk objects, each with full citations.
"""
import os
from typing import List

from src.schemas.models import (
    PrunedTopicsSchema,
    RetrievedChunk,
    Citation,
    WeeklyTopic,
)
from src.retrieval.vector_store import VectorStoreManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _distance_to_score(distance: float) -> float:
    """
    Convert a cosine distance (0 = identical, 2 = opposite) to a relevance
    score in [0, 1] where 1 = perfect match.
    """
    # Chromadb cosine distance is 1 - cosine_similarity, so range [0, 2]
    # Map to [0, 1] relevance
    score = max(0.0, 1.0 - distance)
    return round(score, 4)


def _make_citation(chunk: dict, topic_query: str) -> Citation:
    """Build a Citation from a raw vector store result chunk."""
    meta = chunk.get("metadata") or {}

    source_type = meta.get("type", "syllabus")
    if source_type in ("mock_doc", "mock_doc_file"):
        source_type_label = "mock_doc"
    elif source_type in ("syllabus", "syllabus_topic"):
        source_type_label = "syllabus"
    else:
        source_type_label = source_type

    # Build a human-readable source name
    source = meta.get("source", "")
    if not source:
        course_name = meta.get("course_name", "")
        week = meta.get("week", "")
        if week:
            source = f"{course_name} - Week {week} Syllabus"
        elif course_name:
            source = f"{course_name} Syllabus"
        else:
            topic_meta = meta.get("topic", topic_query)
            source = f"CS Reference - {topic_meta.replace('_', ' ').title()}"

    # Build a chunk_id
    chunk_id = (
        meta.get("course_num", "")
        + ("_week_" + meta.get("week", "") if meta.get("week") else "")
        or meta.get("topic", "chunk")
        or "chunk"
    )
    if not chunk_id.strip("_"):
        chunk_id = meta.get("topic", "chunk") or "chunk"

    relevance_score = _distance_to_score(chunk.get("distance", 0.5))

    return Citation(
        source_name=source,
        source_type=source_type_label,
        chunk_id=chunk_id,
        relevance_score=relevance_score,
    )


# ---------------------------------------------------------------------------
# Main retrieval function
# ---------------------------------------------------------------------------

def retrieve_for_topics(
    pruned_schema: PrunedTopicsSchema,
    db_path: str = None,
    n_results: int = 3,
) -> List[RetrievedChunk]:
    """
    For each validated missed topic in pruned_schema, query the vector store
    and return a list of RetrievedChunk objects (one per topic).

    If the vector store is empty or the query returns no results, a fallback
    chunk is generated so the pipeline never stalls.
    """
    if db_path is None:
        db_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")

    # Resolve relative paths to absolute using project root heuristic
    from pathlib import Path
    db_path_resolved = Path(db_path)
    if not db_path_resolved.is_absolute():
        # Try to anchor to the project root (two levels up from this file)
        project_root = Path(__file__).resolve().parents[2]
        db_path_resolved = project_root / db_path

    store = VectorStoreManager(db_path=str(db_path_resolved))
    collection_size = store.get_collection_count()

    retrieved_chunks: List[RetrievedChunk] = []

    for wt in pruned_schema.validated_missed_topics:
        topic_text = wt.topic.strip()
        if not topic_text:
            continue

        if collection_size > 0:
            results = store.query(topic_text, n_results=n_results)
        else:
            results = []

        if results:
            citations = [_make_citation(r, topic_text) for r in results]
            # Combine content from all results into a single chunk
            combined_content = "\n\n---\n\n".join(
                r.get("content", "") for r in results if r.get("content")
            )
            retrieved_chunks.append(
                RetrievedChunk(
                    topic=topic_text,
                    content=combined_content,
                    citations=citations,
                )
            )
        else:
            # Fallback: generate a synthetic chunk so planner always has content
            fallback_citation = Citation(
                source_name=f"{pruned_schema.course_name} - Course Syllabus",
                source_type="syllabus",
                chunk_id=f"{pruned_schema.course_num}_fallback_{wt.week}",
                relevance_score=0.5,
            )
            fallback_content = (
                f"Topic from {pruned_schema.course_name}: {topic_text}\n\n"
                "Review the course textbook chapters corresponding to this topic. "
                "Consult lecture slides and practice exercises. "
                "This topic covers foundational concepts that build upon previous material."
            )
            retrieved_chunks.append(
                RetrievedChunk(
                    topic=topic_text,
                    content=fallback_content,
                    citations=[fallback_citation],
                )
            )

    return retrieved_chunks
