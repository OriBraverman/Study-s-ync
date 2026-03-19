"""
Tests for Pydantic v2 schemas (src/schemas/models.py).
Run with: pytest tests/test_schemas.py -v
"""
import pytest
from datetime import date

from src.schemas.models import (
    BootcampPlanSchema,
    Citation,
    MissedTopicsSchema,
    PrunedTopicsSchema,
    PruningStats,
    RetrievedChunk,
    StudentInputSchema,
    StudyTaskSchema,
    WeeklyTopic,
)


# ---------------------------------------------------------------------------
# StudentInputSchema
# ---------------------------------------------------------------------------

class TestStudentInputSchema:
    def test_valid_construction(self):
        s = StudentInputSchema(
            student_name="Alice",
            course_name="Intro to CS",
            course_num="89-110",
            absence_start=date(2026, 3, 1),
            absence_end=date(2026, 3, 14),
        )
        assert s.student_name == "Alice"
        assert s.course_num == "89-110"
        assert s.absence_start < s.absence_end

    def test_missing_required_field_raises(self):
        with pytest.raises(Exception):
            StudentInputSchema(
                student_name="Alice",
                course_name="Intro to CS",
                # course_num missing
                absence_start=date(2026, 3, 1),
                absence_end=date(2026, 3, 14),
            )

    def test_same_start_end_date_valid(self):
        s = StudentInputSchema(
            student_name="Bob",
            course_name="Algorithms",
            course_num="89-200",
            absence_start=date(2026, 3, 10),
            absence_end=date(2026, 3, 10),
        )
        assert s.absence_start == s.absence_end

    def test_date_field_types(self):
        s = StudentInputSchema(
            student_name="Carol",
            course_name="Data Structures",
            course_num="89-150",
            absence_start=date(2026, 3, 1),
            absence_end=date(2026, 3, 21),
        )
        assert isinstance(s.absence_start, date)
        assert isinstance(s.absence_end, date)


# ---------------------------------------------------------------------------
# WeeklyTopic
# ---------------------------------------------------------------------------

class TestWeeklyTopic:
    def test_defaults(self):
        wt = WeeklyTopic(week="1", topic="Loops")
        assert wt.is_missed is False

    def test_is_missed_flag(self):
        wt = WeeklyTopic(week="3", topic="Recursion", is_missed=True)
        assert wt.is_missed is True


# ---------------------------------------------------------------------------
# MissedTopicsSchema
# ---------------------------------------------------------------------------

class TestMissedTopicsSchema:
    def _make_schema(self, missed_count: int = 2) -> MissedTopicsSchema:
        all_t = [WeeklyTopic(week=str(i), topic=f"Topic {i}") for i in range(1, 6)]
        missed_t = [WeeklyTopic(week=str(i), topic=f"Topic {i}", is_missed=True) for i in range(1, missed_count + 1)]
        return MissedTopicsSchema(
            course_name="Intro to CS",
            course_num="89-110",
            absence_start=date(2026, 3, 1),
            absence_end=date(2026, 3, 14),
            semester="סמסטר ב'",
            all_topics=all_t,
            missed_topics=missed_t,
            total_weeks=5,
            missed_weeks_count=missed_count,
        )

    def test_basic_construction(self):
        schema = self._make_schema()
        assert schema.total_weeks == 5
        assert schema.missed_weeks_count == 2
        assert len(schema.missed_topics) == 2

    def test_empty_missed_topics_valid(self):
        schema = self._make_schema(missed_count=0)
        assert schema.missed_topics == []
        assert schema.missed_weeks_count == 0

    def test_all_topics_in_missed_valid(self):
        all_t = [WeeklyTopic(week=str(i), topic=f"T{i}", is_missed=True) for i in range(1, 4)]
        schema = MissedTopicsSchema(
            course_name="DS",
            course_num="89-200",
            absence_start=date(2026, 3, 1),
            absence_end=date(2026, 4, 1),
            semester="סמסטר ב'",
            all_topics=all_t,
            missed_topics=all_t,
            total_weeks=3,
            missed_weeks_count=3,
        )
        assert len(schema.missed_topics) == 3


# ---------------------------------------------------------------------------
# PruningStats
# ---------------------------------------------------------------------------

class TestPruningStats:
    def test_valid_stats(self):
        stats = PruningStats(
            original_topic_count=10,
            pruned_topic_count=7,
            topics_removed=["Exam Day", "Holiday"],
            removal_reasons=["administrative", "administrative"],
            token_reduction_pct=25.5,
            pruning_log=["Week 5: REMOVED (admin)", "Week 8: REMOVED (admin)"],
        )
        assert stats.original_topic_count == 10
        assert stats.token_reduction_pct == 25.5
        assert len(stats.topics_removed) == 2

    def test_zero_reduction(self):
        stats = PruningStats(
            original_topic_count=5,
            pruned_topic_count=5,
            topics_removed=[],
            removal_reasons=[],
            token_reduction_pct=0.0,
            pruning_log=[],
        )
        assert stats.token_reduction_pct == 0.0


# ---------------------------------------------------------------------------
# BootcampPlanSchema
# ---------------------------------------------------------------------------

class TestBootcampPlanSchema:
    def _make_plan(self) -> BootcampPlanSchema:
        citation = Citation(
            source_name="Intro CS - Week 1 Syllabus",
            source_type="syllabus",
            chunk_id="89-110_week_1",
            relevance_score=0.88,
        )
        task = StudyTaskSchema(
            day=1,
            topic="Loops",
            description="Study for loops and while loops.",
            estimated_hours=1.5,
            priority="medium",
            citations=[citation],
            study_tips=["Trace variables", "Write from scratch"],
        )
        stats = PruningStats(
            original_topic_count=3,
            pruned_topic_count=2,
            topics_removed=["Exam"],
            removal_reasons=["administrative"],
            token_reduction_pct=33.3,
            pruning_log=["Week 3: REMOVED (admin)"],
        )
        return BootcampPlanSchema(
            student_name="Alice",
            course_name="Intro to CS",
            course_num="89-110",
            generated_at="2026-03-19T10:00:00Z",
            total_days=1,
            total_hours=1.5,
            executive_summary="Study loops and conditions.",
            study_tasks=[task],
            pruning_stats=stats,
            sources_used=["Intro CS - Week 1 Syllabus"],
        )

    def test_valid_construction(self):
        plan = self._make_plan()
        assert plan.student_name == "Alice"
        assert plan.total_days == 1
        assert len(plan.study_tasks) == 1

    def test_task_citation_integrity(self):
        plan = self._make_plan()
        task = plan.study_tasks[0]
        assert len(task.citations) == 1
        assert task.citations[0].relevance_score == 0.88
        assert task.citations[0].source_type == "syllabus"

    def test_serialization_roundtrip(self):
        plan = self._make_plan()
        data = plan.model_dump()
        plan2 = BootcampPlanSchema(**data)
        assert plan2.student_name == plan.student_name
        assert plan2.total_hours == plan.total_hours

    def test_empty_tasks_plan(self):
        stats = PruningStats(
            original_topic_count=0,
            pruned_topic_count=0,
            topics_removed=[],
            removal_reasons=[],
            token_reduction_pct=0.0,
            pruning_log=[],
        )
        plan = BootcampPlanSchema(
            student_name="Bob",
            course_name="DS",
            course_num="89-200",
            generated_at="2026-03-19T10:00:00Z",
            total_days=0,
            total_hours=0.0,
            executive_summary="Nothing to study.",
            study_tasks=[],
            pruning_stats=stats,
            sources_used=[],
        )
        assert plan.study_tasks == []
        assert plan.total_hours == 0.0
