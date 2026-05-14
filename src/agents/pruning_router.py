"""
Pruning Router (AgentPrune-inspired)
Validates and prunes missed topics to eliminate:
1. Empty/None topics
2. Duplicate topics (same concept, different wording)
3. Administrative entries (exam dates, office hours, holidays, etc.)

Tracks token-reduction statistics for the dashboard display.
No LLM calls — purely algorithmic (regex + text similarity).
"""
import re
import unicodedata
from typing import List, Tuple

from src.schemas.models import (
    MissedTopicsSchema,
    PrunedTopicsSchema,
    PruningStats,
    WeeklyTopic,
)


# ---------------------------------------------------------------------------
# Admin / non-content patterns (Hebrew + English)
# ---------------------------------------------------------------------------
ADMIN_PATTERNS: List[str] = [
    r"בחינה|exam|test|quiz|midterm|final",
    r"שעות קבלה|office hours|consultation",
    r"אין הרצאה|no class|holiday|חג|חגים",
    r"^\s*$",                         # blank
    r"ביטול|cancelled|canceled",
    r"מועד|deadline|due date",
    r"תרגיל|homework|assignment\s*\d",  # assignment numbers
    r"הגשה|submission",
    r"יום עצמאות|פסח|סוכות|חנוכה|ראש השנה|יום כיפור",
    r"אירוע|conference|symposium",
    r"אין שיעור|no lecture|no session",
]

_COMPILED_ADMIN = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in ADMIN_PATTERNS]


# ---------------------------------------------------------------------------
# Public utilities
# ---------------------------------------------------------------------------

def is_admin_entry(topic_text: str) -> bool:
    """
    Return True if the topic text is an administrative/non-content entry.
    Checks against ADMIN_PATTERNS and also rejects very short strings.
    """
    if not topic_text or not topic_text.strip():
        return True
    # Very short entries (≤ 3 chars) are not meaningful content
    if len(topic_text.strip()) <= 3:
        return True
    for pattern in _COMPILED_ADMIN:
        if pattern.search(topic_text):
            return True
    return False


def normalize_topic(topic_text: str) -> str:
    """
    Normalize a topic string for duplicate detection:
    - Unicode NFC normalization
    - Lowercase
    - Strip leading/trailing punctuation
    - Replace internal punctuation (colons, commas, etc.) with spaces
    - Collapse whitespace
    """
    if not topic_text:
        return ""

    # NFC normalize (especially for Hebrew)
    text = unicodedata.normalize("NFC", topic_text)
    text = text.lower()

    # Replace internal punctuation with spaces so "algorithms:" == "algorithms"
    text = re.sub(r"[,:;!?\"'()\[\]{}\-]", " ", text)

    # Strip leading/trailing non-alpha chars
    text = text.strip(".,;:- \t\n")

    # Collapse internal whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _topic_similarity(a: str, b: str) -> float:
    """
    Simple Jaccard similarity on word-level tokens for duplicate detection.
    Returns a float in [0, 1].
    """
    a_norm = normalize_topic(a)
    b_norm = normalize_topic(b)

    if not a_norm or not b_norm:
        return 0.0

    tokens_a = set(re.split(r"\s+", a_norm))
    tokens_b = set(re.split(r"\s+", b_norm))

    # Remove empty tokens
    tokens_a.discard("")
    tokens_b.discard("")

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


DUPLICATE_THRESHOLD = 0.65  # Jaccard similarity above this → duplicate


def calculate_token_reduction(
    original_topics: List[WeeklyTopic],
    pruned_topics: List[WeeklyTopic],
) -> float:
    """
    Estimate token-reduction percentage.
    Rough estimate: each word ≈ 1.3 tokens.
    """
    original_tokens = sum(len(t.topic.split()) * 1.3 for t in original_topics)
    pruned_tokens = sum(len(t.topic.split()) * 1.3 for t in pruned_topics)

    if original_tokens == 0:
        return 0.0

    return round((1 - pruned_tokens / original_tokens) * 100, 1)


# ---------------------------------------------------------------------------
# Main pruning function
# ---------------------------------------------------------------------------

def prune_topics(missed_schema: MissedTopicsSchema) -> PrunedTopicsSchema:
    """
    Prune the missed topics list by:
    1. Removing empty / None topics.
    2. Removing administrative entries.
    3. Removing near-duplicate topics (Jaccard ≥ DUPLICATE_THRESHOLD).

    Returns a PrunedTopicsSchema with full pruning statistics.
    """
    original_topics: List[WeeklyTopic] = list(missed_schema.missed_topics)
    original_count = len(original_topics)

    topics_removed: List[str] = []
    removal_reasons: List[str] = []
    pruning_log: List[str] = []

    # --- Pass 1: Remove empty and admin entries --------------------------------
    after_admin: List[WeeklyTopic] = []
    for wt in original_topics:
        if not wt.topic or not wt.topic.strip():
            topics_removed.append(wt.topic or "(empty)")
            removal_reasons.append("empty topic text")
            pruning_log.append(
                f"Week {wt.week}: REMOVED (empty) — '{wt.topic}'"
            )
        elif is_admin_entry(wt.topic):
            topics_removed.append(wt.topic)
            removal_reasons.append("administrative / non-content entry")
            pruning_log.append(
                f"Week {wt.week}: REMOVED (admin) — '{wt.topic}'"
            )
        else:
            after_admin.append(wt)

    # --- Pass 2: Remove near-duplicates (keep first occurrence) ---------------
    after_dedup: List[WeeklyTopic] = []
    for candidate in after_admin:
        is_dup = False
        for kept in after_dedup:
            sim = _topic_similarity(candidate.topic, kept.topic)
            if sim >= DUPLICATE_THRESHOLD:
                is_dup = True
                topics_removed.append(candidate.topic)
                removal_reasons.append(
                    f"near-duplicate of Week {kept.week} topic (similarity={sim:.2f})"
                )
                pruning_log.append(
                    f"Week {candidate.week}: REMOVED (duplicate, sim={sim:.2f}) — '{candidate.topic}' "
                    f"≈ Week {kept.week}: '{kept.topic}'"
                )
                break
        if not is_dup:
            after_dedup.append(candidate)
            pruning_log.append(
                f"Week {candidate.week}: KEPT — '{candidate.topic}'"
            )

    validated = after_dedup
    token_reduction = calculate_token_reduction(original_topics, validated)

    stats = PruningStats(
        original_topic_count=original_count,
        pruned_topic_count=len(validated),
        topics_removed=topics_removed,
        removal_reasons=removal_reasons,
        token_reduction_pct=token_reduction,
        pruning_log=pruning_log,
    )

    return PrunedTopicsSchema(
        course_name=missed_schema.course_name,
        course_num=missed_schema.course_num,
        validated_missed_topics=validated,
        pruning_stats=stats,
    )
