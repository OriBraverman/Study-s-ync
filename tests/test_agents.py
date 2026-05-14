"""
Tests for all agent functions.
Run with: pytest tests/test_agents.py -v
"""
import pytest
from datetime import date
from typing import List

from src.schemas.models import (
    Citation,
    MissedTopicsSchema,
    PrunedTopicsSchema,
    PruningStats,
    RetrievedChunk,
    StudentInputSchema,
    WeeklyTopic,
)
from src.agents.analyzer import analyze_missed_topics, estimate_missed_weeks
from src.agents.pruning_router import (
    is_admin_entry,
    normalize_topic,
    prune_topics,
)
from src.agents.planner_core import create_mock_bootcamp_plan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_missed_schema(topics: List[WeeklyTopic], course_num: str = "89-110") -> MissedTopicsSchema:
    """Build a MissedTopicsSchema with the given topics as both all_topics and missed_topics."""
    return MissedTopicsSchema(
        course_name="Test Course",
        course_num=course_num,
        absence_start=date(2026, 3, 1),
        absence_end=date(2026, 3, 14),
        semester="סמסטר ב'",
        all_topics=topics,
        missed_topics=topics,
        total_weeks=len(topics),
        missed_weeks_count=len(topics),
    )


def _make_pruned_schema(topics: List[WeeklyTopic]) -> PrunedTopicsSchema:
    stats = PruningStats(
        original_topic_count=len(topics),
        pruned_topic_count=len(topics),
        topics_removed=[],
        removal_reasons=[],
        token_reduction_pct=0.0,
        pruning_log=[],
    )
    return PrunedTopicsSchema(
        course_name="Test Course",
        course_num="89-110",
        validated_missed_topics=topics,
        pruning_stats=stats,
    )


# ---------------------------------------------------------------------------
# Analyzer tests
# ---------------------------------------------------------------------------

class TestEstimateMissedWeeks:
    def test_two_week_absence_from_semester_b_start(self):
        """Absence spanning Semester B start (Mar 1) should give weeks 1-2."""
        weeks = estimate_missed_weeks(
            absence_start=date(2026, 3, 1),
            absence_end=date(2026, 3, 14),
            semester="סמסטר ב'",
        )
        assert 1 in weeks
        assert 2 in weeks

    def test_single_day_absence_one_week(self):
        weeks = estimate_missed_weeks(
            absence_start=date(2026, 3, 1),
            absence_end=date(2026, 3, 1),
            semester="סמסטר ב'",
        )
        assert len(weeks) == 1
        assert weeks[0] == 1

    def test_weeks_within_bounds(self):
        """Returned week numbers should always be in 1-15 range."""
        weeks = estimate_missed_weeks(
            absence_start=date(2026, 3, 1),
            absence_end=date(2026, 6, 30),
            semester="סמסטר ב'",
        )
        assert all(1 <= w <= 15 for w in weeks)

    def test_unknown_semester_defaults_gracefully(self):
        """Unknown semester should not raise, returns some week list."""
        weeks = estimate_missed_weeks(
            absence_start=date(2026, 3, 8),
            absence_end=date(2026, 3, 8),
            semester="Unknown Semester",
        )
        assert isinstance(weeks, list)

    def test_no_duplicates_in_output(self):
        """Result should contain no duplicate week numbers."""
        weeks = estimate_missed_weeks(
            absence_start=date(2026, 3, 1),
            absence_end=date(2026, 3, 10),
            semester="סמסטר ב'",
        )
        assert len(weeks) == len(set(weeks))


class TestAnalyzeMissedTopics:
    def test_unknown_course_returns_schema(self):
        """A course not in the JSON should return a valid schema with empty missed_topics."""
        student = StudentInputSchema(
            student_name="Test",
            course_name="Nonexistent",
            course_num="99-999",
            absence_start=date(2026, 3, 1),
            absence_end=date(2026, 3, 7),
        )
        result = analyze_missed_topics(student)
        assert isinstance(result, MissedTopicsSchema)
        assert result.missed_topics == []
        assert result.total_weeks == 0

    def test_known_course_returns_topics(self):
        """Course 89-110 exists in syllabuses.json and should return topics."""
        student = StudentInputSchema(
            student_name="Alice",
            course_name="מבוא למדעי המחשב",
            course_num="89-110",
            absence_start=date(2026, 3, 1),
            absence_end=date(2026, 3, 14),
        )
        result = analyze_missed_topics(student)
        assert isinstance(result, MissedTopicsSchema)
        assert result.total_weeks > 0
        assert len(result.all_topics) > 0

    def test_schema_fields_populated(self):
        """Returned schema should have course_name and semester populated."""
        student = StudentInputSchema(
            student_name="Bob",
            course_name="מבוא למדעי המחשב",
            course_num="89-110",
            absence_start=date(2026, 3, 1),
            absence_end=date(2026, 3, 7),
        )
        result = analyze_missed_topics(student)
        assert result.course_num == "89-110"
        assert result.semester  # Should not be empty string


# ---------------------------------------------------------------------------
# Pruning Router tests
# ---------------------------------------------------------------------------

class TestIsAdminEntry:
    def test_exam_detected_as_admin(self):
        assert is_admin_entry("Midterm exam — chapters 1-5") is True

    def test_holiday_detected(self):
        assert is_admin_entry("חג פסח — אין הרצאה") is True

    def test_office_hours_detected(self):
        assert is_admin_entry("שעות קבלה: ראשון 10-12") is True

    def test_regular_topic_not_admin(self):
        assert is_admin_entry("Recursive algorithms and dynamic programming") is False

    def test_empty_string_is_admin(self):
        assert is_admin_entry("") is True

    def test_whitespace_only_is_admin(self):
        assert is_admin_entry("   ") is True

    def test_loops_topic_not_admin(self):
        assert is_admin_entry("Loops and iteration in Python") is False


class TestNormalizeTopic:
    def test_lowercase(self):
        assert normalize_topic("Recursion And Base Cases") == "recursion and base cases"

    def test_strips_leading_punctuation(self):
        result = normalize_topic(".Sorting algorithms")
        assert not result.startswith(".")

    def test_collapses_whitespace(self):
        result = normalize_topic("binary   search   trees")
        assert "  " not in result

    def test_empty_string(self):
        assert normalize_topic("") == ""


class TestPruneTopics:
    def test_removes_empty_topics(self):
        topics = [
            WeeklyTopic(week="1", topic="Loops"),
            WeeklyTopic(week="2", topic=""),          # empty
            WeeklyTopic(week="3", topic="Recursion"),
        ]
        schema = _make_missed_schema(topics)
        result = prune_topics(schema)
        topic_texts = [t.topic for t in result.validated_missed_topics]
        assert "" not in topic_texts
        assert len(result.validated_missed_topics) == 2

    def test_removes_admin_topics(self):
        topics = [
            WeeklyTopic(week="1", topic="Loops and iteration"),
            WeeklyTopic(week="5", topic="Midterm exam"),
            WeeklyTopic(week="8", topic="חג פסח — אין הרצאה"),
        ]
        schema = _make_missed_schema(topics)
        result = prune_topics(schema)
        validated_texts = [t.topic for t in result.validated_missed_topics]
        assert "Midterm exam" not in validated_texts
        assert len(result.validated_missed_topics) == 1

    def test_removes_duplicates(self):
        topics = [
            WeeklyTopic(week="1", topic="Sorting algorithms: bubble sort merge sort"),
            WeeklyTopic(week="2", topic="Sorting: bubble sort and merge sort algorithms"),  # near duplicate
            WeeklyTopic(week="3", topic="Graph traversal BFS DFS"),
        ]
        schema = _make_missed_schema(topics)
        result = prune_topics(schema)
        # Duplicate should be removed; should have 2 topics left
        assert len(result.validated_missed_topics) <= 2

    def test_pruning_stats_populated(self):
        topics = [
            WeeklyTopic(week="1", topic="Loops"),
            WeeklyTopic(week="2", topic="Final exam"),
        ]
        schema = _make_missed_schema(topics)
        result = prune_topics(schema)
        stats = result.pruning_stats
        assert stats.original_topic_count == 2
        assert stats.pruned_topic_count < stats.original_topic_count
        assert len(stats.topics_removed) > 0

    def test_empty_missed_topics(self):
        """Pruning an empty list should return empty with zero stats."""
        schema = _make_missed_schema([])
        result = prune_topics(schema)
        assert result.validated_missed_topics == []
        assert result.pruning_stats.original_topic_count == 0
        assert result.pruning_stats.pruned_topic_count == 0
        assert result.pruning_stats.token_reduction_pct == 0.0

    def test_all_clean_topics_kept(self):
        topics = [
            WeeklyTopic(week="1", topic="Introduction to Python variables"),
            WeeklyTopic(week="2", topic="Loops and iteration in programming"),
            WeeklyTopic(week="3", topic="Functions and scope"),
        ]
        schema = _make_missed_schema(topics)
        result = prune_topics(schema)
        # All are unique and non-admin, all should be kept
        assert len(result.validated_missed_topics) == 3

    def test_pruning_log_not_empty_when_pruning_occurs(self):
        topics = [
            WeeklyTopic(week="1", topic="Algorithms"),
            WeeklyTopic(week="5", topic="Office hours — no class"),
        ]
        schema = _make_missed_schema(topics)
        result = prune_topics(schema)
        assert len(result.pruning_stats.pruning_log) > 0


# ---------------------------------------------------------------------------
# Planner tests
# ---------------------------------------------------------------------------

class TestMockPlanner:
    def _make_retrieved_chunks(self, topics: List[WeeklyTopic]) -> List[RetrievedChunk]:
        chunks = []
        for wt in topics:
            citation = Citation(
                source_name=f"Test Course - Week {wt.week} Syllabus",
                source_type="syllabus",
                chunk_id=f"89-110_week_{wt.week}",
                relevance_score=0.75,
            )
            chunks.append(
                RetrievedChunk(
                    topic=wt.topic,
                    content=f"Detailed content about {wt.topic}. "
                            "This section covers fundamental concepts, examples, and exercises.",
                    citations=[citation],
                )
            )
        return chunks

    def test_generates_plan(self):
        topics = [
            WeeklyTopic(week="1", topic="Loops", is_missed=True),
            WeeklyTopic(week="2", topic="Recursion", is_missed=True),
        ]
        pruned = _make_pruned_schema(topics)
        chunks = self._make_retrieved_chunks(topics)
        plan = create_mock_bootcamp_plan("Alice", pruned, chunks)

        assert plan.student_name == "Alice"
        assert plan.total_days >= 1
        assert len(plan.study_tasks) == 2

    def test_every_task_has_citations(self):
        topics = [WeeklyTopic(week=str(i), topic=f"Topic {i}", is_missed=True) for i in range(1, 5)]
        pruned = _make_pruned_schema(topics)
        chunks = self._make_retrieved_chunks(topics)
        plan = create_mock_bootcamp_plan("Bob", pruned, chunks)

        for task in plan.study_tasks:
            assert len(task.citations) >= 1, f"Task '{task.topic}' has no citations"

    def test_priority_values_valid(self):
        topics = [WeeklyTopic(week="1", topic="Sorting algorithms merge sort", is_missed=True)]
        pruned = _make_pruned_schema(topics)
        chunks = self._make_retrieved_chunks(topics)
        plan = create_mock_bootcamp_plan("Carol", pruned, chunks)
        for task in plan.study_tasks:
            assert task.priority in ("high", "medium", "low")

    def test_hours_positive(self):
        topics = [WeeklyTopic(week="1", topic="Introduction to variables", is_missed=True)]
        pruned = _make_pruned_schema(topics)
        chunks = self._make_retrieved_chunks(topics)
        plan = create_mock_bootcamp_plan("Dan", pruned, chunks)
        for task in plan.study_tasks:
            assert task.estimated_hours > 0

    def test_study_tips_present(self):
        topics = [WeeklyTopic(week="1", topic="Recursion and base cases", is_missed=True)]
        pruned = _make_pruned_schema(topics)
        chunks = self._make_retrieved_chunks(topics)
        plan = create_mock_bootcamp_plan("Eve", pruned, chunks)
        for task in plan.study_tasks:
            assert len(task.study_tips) >= 1

    def test_empty_topics_generates_empty_plan(self):
        pruned = _make_pruned_schema([])
        plan = create_mock_bootcamp_plan("Frank", pruned, [])
        assert plan.study_tasks == []
        assert plan.total_days == 0
        assert plan.total_hours == 0.0

    def test_sources_used_populated(self):
        topics = [WeeklyTopic(week="1", topic="Loops", is_missed=True)]
        pruned = _make_pruned_schema(topics)
        chunks = self._make_retrieved_chunks(topics)
        plan = create_mock_bootcamp_plan("Grace", pruned, chunks)
        assert len(plan.sources_used) >= 1
