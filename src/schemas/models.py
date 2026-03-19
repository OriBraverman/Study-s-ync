"""
ArmorAgent Pydantic v2 Data Models
All schemas used across the multi-agent pipeline.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class StudentInputSchema(BaseModel):
    student_name: str
    course_name: str
    course_num: str  # e.g. "89-110"
    absence_start: date
    absence_end: date


class WeeklyTopic(BaseModel):
    week: str
    topic: str
    is_missed: bool = False


class MissedTopicsSchema(BaseModel):
    course_name: str
    course_num: str
    absence_start: date
    absence_end: date
    semester: str
    all_topics: List[WeeklyTopic]
    missed_topics: List[WeeklyTopic]
    total_weeks: int
    missed_weeks_count: int


class PruningStats(BaseModel):
    original_topic_count: int
    pruned_topic_count: int
    topics_removed: List[str]
    removal_reasons: List[str]
    token_reduction_pct: float
    pruning_log: List[str]


class PrunedTopicsSchema(BaseModel):
    course_name: str
    course_num: str
    validated_missed_topics: List[WeeklyTopic]
    pruning_stats: PruningStats


class Citation(BaseModel):
    source_name: str   # e.g. "Intro to CS - Week 3 Syllabus"
    source_type: str   # "syllabus" | "pdf" | "mock_doc"
    chunk_id: str
    relevance_score: float


class RetrievedChunk(BaseModel):
    topic: str
    content: str
    citations: List[Citation]


class StudyTaskSchema(BaseModel):
    day: int
    topic: str
    description: str
    estimated_hours: float
    priority: str   # "high" | "medium" | "low"
    citations: List[Citation]
    study_tips: List[str]


class BootcampPlanSchema(BaseModel):
    student_name: str
    course_name: str
    course_num: str
    generated_at: str
    total_days: int
    total_hours: float
    executive_summary: str
    study_tasks: List[StudyTaskSchema]
    pruning_stats: PruningStats
    sources_used: List[str]
